from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.log_queries import get_logs, get_log_by_id, get_statistics, get_top_ips, get_top_ports
from app.schemas.log_schema import LogResponse, LogsResponse, StatsResponse, TopIPResponse, TopPortResponse

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
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order (asc or desc)")
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
        
        # Convert logs to LogResponse models
        log_responses = [LogResponse(**log) for log in result["logs"]]
        
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
def get_log_endpoint(log_id: str):
    """Get a single log entry by ID"""
    log = get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return LogResponse(**log)


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
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)")
):
    """Get top source IPs by log count"""
    try:
        top_ips = get_top_ips(limit=limit, start_date=start_date, end_date=end_date)
        return [TopIPResponse(**ip) for ip in top_ips]
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

