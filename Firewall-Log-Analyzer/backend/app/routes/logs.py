from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Body, Security, Response
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
import csv
import json
import io
from app.services.log_queries import get_logs, get_log_by_id, get_statistics, get_top_ips, get_top_ports, build_log_query
from app.services.virustotal_service import get_multiple_ip_reputations, enhance_severity_with_reputation
from app.services.log_parser_service import parse_multiple_logs
from app.middleware.auth_middleware import verify_api_key
from app.schemas.log_schema import LogResponse, LogsResponse, StatsResponse, TopIPResponse, TopPortResponse, VirusTotalReputation
from app.schemas.ingestion_schema import LogIngestionRequest, LogIngestionResponse
from app.db.mongo import logs_collection

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/ingest", response_model=LogIngestionResponse)
def ingest_logs_endpoint(
    request: LogIngestionRequest = Body(...),
    api_key: str = Security(verify_api_key)
):
    """
    Ingest firewall logs from remote VMs or log sources.
    
    This endpoint accepts raw log lines and automatically parses them using
    the appropriate parser (auth.log, ufw.log, iptables, syslog, sql.log).
    
    Requires API key authentication via X-API-Key header.
    
    Example:
    ```json
    {
        "logs": [
            "Jan  1 10:00:00 hostname sshd[12345]: Failed password for admin from 192.168.1.100",
            "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.1 DST=192.168.1.100 PROTO=TCP DPT=22"
        ],
        "log_source": "auth.log"
    }
    ```
    """
    try:
        if not request.logs:
            raise HTTPException(status_code=400, detail="Logs list cannot be empty")
        
        if len(request.logs) > 1000:
            raise HTTPException(status_code=400, detail="Maximum 1000 log lines per request")
        
        # Parse logs
        parsed_logs = parse_multiple_logs(request.logs, request.log_source)
        
        if not parsed_logs:
            return LogIngestionResponse(
                success=False,
                ingested_count=0,
                failed_count=len(request.logs),
                total_received=len(request.logs),
                message="No logs could be parsed from the provided lines"
            )
        
        # Insert into database
        if parsed_logs:
            logs_collection.insert_many(parsed_logs)
        
        failed_count = len(request.logs) - len(parsed_logs)
        
        return LogIngestionResponse(
            success=True,
            ingested_count=len(parsed_logs),
            failed_count=failed_count,
            total_received=len(request.logs),
            message=f"Successfully ingested {len(parsed_logs)} log(s). {failed_count} failed to parse."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting logs: {str(e)}")


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
            try:
                log_dict = dict(log)
                
                # Ensure required fields have default values if missing
                if "timestamp" not in log_dict or log_dict["timestamp"] is None:
                    continue  # Skip logs without timestamp
                if "source_ip" not in log_dict or not log_dict["source_ip"]:
                    log_dict["source_ip"] = "Unknown"
                if "log_source" not in log_dict or not log_dict["log_source"]:
                    log_dict["log_source"] = "unknown"
                if "event_type" not in log_dict or not log_dict["event_type"]:
                    log_dict["event_type"] = "UNKNOWN"
                if "severity" not in log_dict or not log_dict["severity"]:
                    log_dict["severity"] = "LOW"
                if "raw_log" not in log_dict or log_dict["raw_log"] is None:
                    log_dict["raw_log"] = ""
                
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
            except ValidationError as e:
                # Skip logs that fail Pydantic validation
                continue
            except Exception as e:
                # Skip any other errors for individual log entries
                continue
        
        return LogsResponse(
            logs=log_responses,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@router.get("/export")
def export_logs_endpoint(
    format: str = Query("csv", regex="^(csv|json)$", description="Export format (csv or json)"),
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
    """Export logs in CSV or JSON format with filtering"""
    try:
        # Build query
        query = build_log_query(
            source_ip=source_ip,
            severity=severity,
            event_type=event_type,
            destination_port=destination_port,
            protocol=protocol,
            log_source=log_source,
            start_date=start_date,
            end_date=end_date,
            search=search
        )
        
        # Get all logs matching the query (no pagination for export)
        from pymongo import DESCENDING, ASCENDING
        
        # Special handling for severity sorting (custom order: CRITICAL > HIGH > MEDIUM > LOW)
        if sort_by == "severity":
            sort_direction = -1 if sort_order.lower() == "desc" else 1
            
            # Use aggregation pipeline for custom severity sorting
            pipeline = [
                {"$match": query},
                {
                    "$addFields": {
                        "severity_order": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$severity", "CRITICAL"]}, "then": 0},
                                    {"case": {"$eq": ["$severity", "HIGH"]}, "then": 1},
                                    {"case": {"$eq": ["$severity", "MEDIUM"]}, "then": 2},
                                    {"case": {"$eq": ["$severity", "LOW"]}, "then": 3}
                                ],
                                "default": 99  # Unknown severity values go to end
                            }
                        }
                    }
                },
                {"$sort": {"severity_order": sort_direction}},
                {"$project": {"severity_order": 0}}  # Remove temporary field
            ]
            
            logs = list(logs_collection.aggregate(pipeline))
        else:
            # Standard sorting for other fields
            sort_direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
            sort_fields = {
                "timestamp": ("timestamp", sort_direction),
                "source_ip": ("source_ip", sort_direction),
                "event_type": ("event_type", sort_direction),
            }
            sort_criteria = [sort_fields.get(sort_by, ("timestamp", DESCENDING))]
            
            # Fetch all matching logs
            cursor = logs_collection.find(query).sort(sort_criteria)
            logs = list(cursor)
        
        # Convert ObjectId to string and format timestamps
        for log in logs:
            log["_id"] = str(log["_id"])
            # Format timestamp for display
            if "timestamp" in log and isinstance(log["timestamp"], datetime):
                timestamp_str = log["timestamp"].isoformat()
                log["timestamp"] = timestamp_str
            elif "timestamp" in log:
                # Already a string, keep as is
                pass
        
        if format.lower() == "csv":
            # Export as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            if logs:
                headers = ["ID", "Timestamp", "Source IP", "Destination IP", "Source Port", "Destination Port", "Protocol",
                          "Log Source", "Event Type", "Severity", "Username", "Raw Log"]
                writer.writerow(headers)
                
                # Write data rows
                for log in logs:
                    writer.writerow([
                        log.get("_id", ""),
                        log.get("timestamp", ""),
                        log.get("source_ip", ""),
                        log.get("destination_ip", ""),
                        log.get("source_port", ""),
                        log.get("destination_port", ""),
                        log.get("protocol", ""),
                        log.get("log_source", ""),
                        log.get("event_type", ""),
                        log.get("severity", ""),
                        log.get("username", ""),
                        log.get("raw_log", "")
                    ])
            
            # Convert to bytes
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content.encode('utf-8'),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=logs_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        else:
            # Export as JSON
            json_content = json.dumps(logs, indent=2, default=str, ensure_ascii=False)
            
            return Response(
                content=json_content.encode('utf-8'),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=logs_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting logs: {str(e)}")


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
    
    try:
        log_dict = dict(log)
        
        # Ensure required fields have default values if missing
        if "timestamp" not in log_dict or log_dict["timestamp"] is None:
            raise HTTPException(status_code=500, detail="Log entry is missing required timestamp field")
        if "source_ip" not in log_dict or not log_dict["source_ip"]:
            log_dict["source_ip"] = "Unknown"
        if "log_source" not in log_dict or not log_dict["log_source"]:
            log_dict["log_source"] = "unknown"
        if "event_type" not in log_dict or not log_dict["event_type"]:
            log_dict["event_type"] = "UNKNOWN"
        if "severity" not in log_dict or not log_dict["severity"]:
            log_dict["severity"] = "LOW"
        if "raw_log" not in log_dict or log_dict["raw_log"] is None:
            log_dict["raw_log"] = ""
        
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
    except ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Log entry validation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving log: {str(e)}")


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

