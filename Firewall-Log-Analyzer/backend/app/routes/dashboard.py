from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pymongo import DESCENDING
from app.schemas.dashboard_schema import (
    DashboardSummaryResponse,
    ActiveAlert,
    ThreatSummary,
    TopIP,
    SystemHealth
)
from app.services.brute_force_detection import detect_brute_force
from app.services.ddos_detection import detect_ddos
from app.services.log_queries import get_top_ips
from app.db.mongo import logs_collection, client

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary():
    """
    Get quick dashboard summary with active alerts, threats, top IPs, and system health.
    
    Provides a comprehensive overview of the firewall log analyzer system including:
    - Active alerts: Recent high-severity threats (brute force and DDoS)
    - Threats: Summary counts of active threats by type and severity
    - Top IPs: Most active source IPs with statistics
    - System health: Database status and recent activity metrics
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)
        
        # 1. Get active alerts (recent high-severity threats)
        active_alerts = []
        
        # Get brute force detections from last 24 hours
        brute_force_detections = detect_brute_force(
            time_window_minutes=15,
            threshold=5,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get DDoS detections from last 24 hours
        ddos_detections = detect_ddos(
            time_window_seconds=60,
            single_ip_threshold=100,
            distributed_ip_count=10,
            distributed_request_threshold=500,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert brute force detections to alerts (limit to top 5 by severity)
        for detection in brute_force_detections[:5]:
            severity = detection.get("severity", "LOW")
            if severity in ["CRITICAL", "HIGH"]:
                active_alerts.append(
                    ActiveAlert(
                        type="BRUTE_FORCE",
                        source_ip=detection.get("source_ip", "Unknown"),
                        severity=severity,
                        detected_at=detection.get("last_attempt", end_date),
                        description=f"Brute force attack: {detection.get('total_attempts', 0)} failed login attempts",
                        threat_count=detection.get("total_attempts", 0)
                    )
                )
        
        # Convert DDoS detections to alerts (limit to top 5 by severity)
        for detection in ddos_detections[:5]:
            severity = detection.get("severity", "LOW")
            if severity in ["CRITICAL", "HIGH"]:
                attack_type = detection.get("attack_type", "UNKNOWN")
                source_ips = detection.get("source_ips", [])
                source_ip = source_ips[0] if source_ips else "Multiple IPs"
                
                if attack_type == "DISTRIBUTED_FLOOD":
                    description = f"Distributed DDoS: {detection.get('source_ip_count', 0)} IPs, {detection.get('total_requests', 0)} requests"
                else:
                    description = f"Single IP flood: {detection.get('total_requests', 0)} requests"
                
                active_alerts.append(
                    ActiveAlert(
                        type="DDOS",
                        source_ip=source_ip,
                        severity=severity,
                        detected_at=detection.get("last_request", end_date),
                        description=description,
                        threat_count=detection.get("total_requests", 0)
                    )
                )
        
        # Sort alerts by severity (CRITICAL > HIGH) and then by detected_at (most recent first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        active_alerts.sort(key=lambda x: (severity_order.get(x.severity, 99), -x.detected_at.timestamp()))
        active_alerts = active_alerts[:10]  # Limit to top 10 alerts
        
        # 2. Calculate threat summary
        threat_summary = ThreatSummary(
            total_brute_force=len(brute_force_detections),
            total_ddos=len(ddos_detections),
            critical_count=sum(1 for d in brute_force_detections + ddos_detections if d.get("severity") == "CRITICAL"),
            high_count=sum(1 for d in brute_force_detections + ddos_detections if d.get("severity") == "HIGH"),
            medium_count=sum(1 for d in brute_force_detections + ddos_detections if d.get("severity") == "MEDIUM"),
            low_count=sum(1 for d in brute_force_detections + ddos_detections if d.get("severity") == "LOW")
        )
        
        # 3. Get top IPs (last 24 hours)
        top_ips_data = get_top_ips(limit=10, start_date=start_date, end_date=end_date)
        top_ips = []
        
        for ip_data in top_ips_data:
            # Get last seen timestamp for this IP
            last_log = logs_collection.find_one(
                {"source_ip": ip_data["source_ip"], "timestamp": {"$gte": start_date, "$lte": end_date}},
                {"timestamp": 1},
                sort=[("timestamp", DESCENDING)]
            )
            
            top_ips.append(
                TopIP(
                    source_ip=ip_data["source_ip"],
                    total_logs=ip_data["count"],
                    severity_breakdown=ip_data.get("severity_breakdown", {}),
                    last_seen=last_log["timestamp"] if last_log else None
                )
            )
        
        # 4. Get system health
        # Check database connection
        try:
            client.admin.command('ping')
            db_status = "healthy"
        except Exception:
            db_status = "down"
        
        # Get 24h statistics
        query_24h = {
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        total_logs_24h = logs_collection.count_documents(query_24h)
        high_severity_logs_24h = logs_collection.count_documents({
            **query_24h,
            "severity": "HIGH"
        })
        
        # Get last log timestamp
        last_log = logs_collection.find_one(
            {},
            {"timestamp": 1},
            sort=[("timestamp", DESCENDING)]
        )
        last_log_timestamp = last_log["timestamp"] if last_log else None
        
        system_health = SystemHealth(
            database_status=db_status,
            total_logs_24h=total_logs_24h,
            high_severity_logs_24h=high_severity_logs_24h,
            last_log_timestamp=last_log_timestamp,
            uptime_seconds=None  # Could be calculated if we track startup time
        )
        
        return DashboardSummaryResponse(
            active_alerts=active_alerts,
            threats=threat_summary,
            top_ips=top_ips,
            system_health=system_health,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard summary: {str(e)}")

