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
from app.services.log_queries import get_top_ips
from app.db.mongo import logs_collection, client
from app.services.alert_service import get_or_compute_alerts, sort_alert_docs

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
        start_date, end_date, alert_docs = get_or_compute_alerts()
        
        # 1. Active alerts (high-severity)
        active_alerts: list[ActiveAlert] = []
        sorted_docs = sort_alert_docs(alert_docs)
        for doc in sorted_docs:
            sev = doc.get("severity", "LOW")
            if sev not in ["CRITICAL", "HIGH"]:
                continue
            active_alerts.append(
                ActiveAlert(
                    type=doc.get("alert_type", "UNKNOWN"),
                    source_ip=doc.get("source_ip", "Unknown"),
                    severity=sev,
                    detected_at=doc.get("last_seen", end_date),
                    description=doc.get("description", ""),
                    threat_count=doc.get("count", 0),
                )
            )
            if len(active_alerts) >= 10:
                break
        
        # 2. Threat summary from cached alerts (counts of detections)
        all_threats = alert_docs or []
        threat_summary = ThreatSummary(
            total_brute_force=sum(1 for d in all_threats if d.get("alert_type") == "BRUTE_FORCE"),
            total_ddos=sum(1 for d in all_threats if d.get("alert_type") == "DDOS"),
            total_port_scan=sum(1 for d in all_threats if d.get("alert_type") == "PORT_SCAN"),
            critical_count=sum(1 for d in all_threats if (d.get("severity") == "CRITICAL")),
            high_count=sum(1 for d in all_threats if (d.get("severity") == "HIGH")),
            medium_count=sum(1 for d in all_threats if (d.get("severity") == "MEDIUM")),
            low_count=sum(1 for d in all_threats if (d.get("severity") == "LOW"))
        )
        
        # 3. Get top IPs (use last 7 days for better data, fallback to all-time if needed)
        top_ips_start_date = end_date - timedelta(days=7)
        top_ips_data = get_top_ips(limit=10, start_date=top_ips_start_date, end_date=end_date)
        
        # Fallback to all-time if no data in last 7 days
        if not top_ips_data:
            top_ips_data = get_top_ips(limit=10, start_date=None, end_date=None)
        
        top_ips = []
        
        for ip_data in top_ips_data:
            # Get last seen timestamp for this IP (all-time, not just last 24h)
            last_log = logs_collection.find_one(
                {"source_ip": ip_data["source_ip"]},
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

