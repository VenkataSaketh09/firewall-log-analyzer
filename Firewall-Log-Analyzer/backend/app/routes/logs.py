from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.log_queries import get_logs, get_log_by_id, get_statistics, get_top_ips, get_top_ports
from app.services.virustotal_service import get_multiple_ip_reputations, enhance_severity_with_reputation
from app.schemas.log_schema import LogResponse, LogsResponse, StatsResponse, TopIPResponse, TopPortResponse, VirusTotalReputation

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=LogsResponse)
def get_logs_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Number of logs per page"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP"),
    severity: Optional[str] = Query(None, description="Filter by severity (HIGH, MEDIUM, LOW)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    destination_port: Optional[int] = Query(None, description="Filter by destination port"),
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    log_source: Optional[str] = Query(None, description="Filter by log source"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    search: Optional[str] = Query(None, description="Search in source_ip, raw_log, or username"),
    sort_by: str = Query("timestamp", description="Field to sort by (timestamp, severity, source_ip, event_type)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order (asc or desc)"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
):
    """Get paginated logs with filtering and sorting"""
    try:
        result = get_logs(
            page=page,
            page_size=page_size,
            source_ip=source_ip,
            severity=severity,
            event_type=event_type,
            destination_port=destination_port,
            protocol=protocol,
            log_source=log_source,
            start_date=start_date,
            end_date=end_date,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get unique IP addresses for reputation lookup
        reputation_data = {}
        if include_reputation:
            unique_ips = list(set(log.get("source_ip") for log in result["logs"] if log.get("source_ip")))
            reputation_data = get_multiple_ip_reputations(unique_ips)
        
        # Convert logs to LogResponse models with reputation
        log_responses = []
        for log in result["logs"]:
            log_dict = dict(log)
            
            # Add reputation data if requested
            if include_reputation:
                ip = log_dict.get("source_ip")
                if ip and ip in reputation_data:
                    reputation = reputation_data[ip]
                    log_dict["virustotal"] = reputation
                    
                    # Enhance severity based on reputation
                    if reputation.get("detected"):
                        original_severity = log_dict.get("severity", "LOW")
                        log_dict["severity"] = enhance_severity_with_reputation(original_severity, reputation)
            
            log_responses.append(LogResponse(**log_dict))
        
        return LogsResponse(
            logs=log_responses,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@router.get("/{log_id}", response_model=LogResponse)
def get_log_endpoint(
    log_id: str,
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
):
    """Get a single log entry by ID"""
    from app.services.virustotal_service import get_ip_reputation, enhance_severity_with_reputation
    
    log = get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    log_dict = dict(log)
    
    # Add reputation data if requested
    if include_reputation:
        ip = log_dict.get("source_ip")
        if ip:
            reputation = get_ip_reputation(ip)
            if reputation:
                log_dict["virustotal"] = reputation
                
                # Enhance severity based on reputation
                if reputation.get("detected"):
                    original_severity = log_dict.get("severity", "LOW")
                    log_dict["severity"] = enhance_severity_with_reputation(original_severity, reputation)
    
    return LogResponse(**log_dict)


@router.get("/stats/summary", response_model=StatsResponse)
def get_stats_endpoint(
    start_date: Optional[datetime] = Query(None, description="Start date for statistics (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date for statistics (ISO format)")
):
    """Get aggregated statistics about logs"""
    try:
        stats = get_statistics(start_date=start_date, end_date=end_date)
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@router.get("/stats/top-ips", response_model=list[TopIPResponse])
def get_top_ips_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top IPs to return"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
):
    """Get top source IPs by log count"""
    try:
        top_ips = get_top_ips(limit=limit, start_date=start_date, end_date=end_date)
        
        # Get reputation data if requested
        reputation_data = {}
        if include_reputation:
            unique_ips = [ip.get("source_ip") for ip in top_ips if ip.get("source_ip")]
            reputation_data = get_multiple_ip_reputations(unique_ips)
        
        # Enhance IP responses with reputation
        ip_responses = []
        for ip in top_ips:
            ip_dict = dict(ip)
            if include_reputation:
                ip_addr = ip_dict.get("source_ip")
                if ip_addr and ip_addr in reputation_data:
                    ip_dict["virustotal"] = reputation_data[ip_addr]
            ip_responses.append(TopIPResponse(**ip_dict))
        
        return ip_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving top IPs: {str(e)}")


@router.get("/stats/top-ports", response_model=list[TopPortResponse])
def get_top_ports_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Number of top ports to return"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)")
):
    """Get top destination ports by log count"""
    try:
        top_ports = get_top_ports(limit=limit, start_date=start_date, end_date=end_date)
        return [TopPortResponse(**port) for port in top_ports]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving top ports: {str(e)}")

