from datetime import datetime, timedelta
from typing import Optional, Dict, List
from app.services.log_queries import get_statistics
from app.services.brute_force_detection import detect_brute_force
from app.services.ddos_detection import detect_ddos


def generate_daily_report(date: Optional[datetime] = None) -> Dict:
    """
    Generate a daily security report for a specific date.
    
    Args:
        date: Date to generate report for (default: today)
    
    Returns:
        Dictionary containing comprehensive daily security report
    """
    if date is None:
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_date = date
    end_date = date + timedelta(days=1) - timedelta(microseconds=1)
    
    return _generate_report(start_date, end_date, "DAILY")


def generate_weekly_report(start_date: Optional[datetime] = None) -> Dict:
    """
    Generate a weekly security report for the past 7 days.
    
    Args:
        start_date: Start date of the week (default: 7 days ago)
    
    Returns:
        Dictionary containing comprehensive weekly security report
    """
    if start_date is None:
        start_date = (datetime.utcnow() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_date = datetime.utcnow()
    
    return _generate_report(start_date, end_date, "WEEKLY")


def generate_custom_report(start_date: datetime, end_date: datetime) -> Dict:
    """
    Generate a custom date range security report.
    
    Args:
        start_date: Start date for the report
        end_date: End date for the report
    
    Returns:
        Dictionary containing comprehensive security report
    """
    return _generate_report(start_date, end_date, "CUSTOM")


def _generate_report(start_date: datetime, end_date: datetime, report_type: str) -> Dict:
    """
    Internal function to generate comprehensive security reports.
    """
    # Get log statistics
    log_stats = get_statistics(start_date=start_date, end_date=end_date)
    
    # Get brute force detections
    brute_force_detections = detect_brute_force(
        time_window_minutes=15,
        threshold=5,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get DDoS detections
    ddos_detections = detect_ddos(
        time_window_seconds=60,
        single_ip_threshold=100,
        distributed_ip_count=10,
        distributed_request_threshold=500,
        start_date=start_date,
        end_date=end_date
    )
    
    # Calculate threat summary
    threat_summary = {
        "total_brute_force_attacks": len(brute_force_detections),
        "total_ddos_attacks": len(ddos_detections),
        "total_threats": len(brute_force_detections) + len(ddos_detections),
        "critical_threats": 0,
        "high_threats": 0,
        "medium_threats": 0,
        "low_threats": 0
    }
    
    # Count threats by severity
    for detection in brute_force_detections:
        severity = detection.get("severity", "LOW")
        if severity == "CRITICAL":
            threat_summary["critical_threats"] += 1
        elif severity == "HIGH":
            threat_summary["high_threats"] += 1
        elif severity == "MEDIUM":
            threat_summary["medium_threats"] += 1
        else:
            threat_summary["low_threats"] += 1
    
    for detection in ddos_detections:
        severity = detection.get("severity", "LOW")
        if severity == "CRITICAL":
            threat_summary["critical_threats"] += 1
        elif severity == "HIGH":
            threat_summary["high_threats"] += 1
        elif severity == "MEDIUM":
            threat_summary["medium_threats"] += 1
        else:
            threat_summary["low_threats"] += 1
    
    # Get top threat sources (from brute force and DDoS)
    threat_sources = {}
    
    for detection in brute_force_detections:
        ip = detection.get("source_ip")
        if ip:
            if ip not in threat_sources:
                threat_sources[ip] = {
                    "ip": ip,
                    "brute_force_attacks": 0,
                    "ddos_attacks": 0,
                    "total_attempts": 0,
                    "severity": "LOW"
                }
            threat_sources[ip]["brute_force_attacks"] += 1
            threat_sources[ip]["total_attempts"] += detection.get("total_attempts", 0)
            # Update severity to highest
            current_sev = threat_sources[ip]["severity"]
            det_sev = detection.get("severity", "LOW")
            if _severity_level(det_sev) > _severity_level(current_sev):
                threat_sources[ip]["severity"] = det_sev
    
    for detection in ddos_detections:
        source_ips = detection.get("source_ips", [])
        for ip in source_ips:
            if ip not in threat_sources:
                threat_sources[ip] = {
                    "ip": ip,
                    "brute_force_attacks": 0,
                    "ddos_attacks": 0,
                    "total_attempts": 0,
                    "severity": "LOW"
                }
            threat_sources[ip]["ddos_attacks"] += 1
            threat_sources[ip]["total_attempts"] += detection.get("total_requests", 0)
            # Update severity to highest
            current_sev = threat_sources[ip]["severity"]
            det_sev = detection.get("severity", "LOW")
            if _severity_level(det_sev) > _severity_level(current_sev):
                threat_sources[ip]["severity"] = det_sev
    
    # Sort threat sources by total attempts
    top_threat_sources = sorted(
        list(threat_sources.values()),
        key=lambda x: x["total_attempts"],
        reverse=True
    )[:20]
    
    # Calculate security score (0-100, higher is better)
    # Base score starts at 100, deduct points for threats
    security_score = 100
    security_score -= min(threat_summary["critical_threats"] * 20, 80)
    security_score -= min(threat_summary["high_threats"] * 10, 60)
    security_score -= min(threat_summary["medium_threats"] * 5, 40)
    security_score -= min(threat_summary["low_threats"] * 1, 20)
    security_score = max(security_score, 0)
    
    # Determine security status
    if security_score >= 80:
        security_status = "SECURE"
    elif security_score >= 60:
        security_status = "MODERATE"
    elif security_score >= 40:
        security_status = "WARNING"
    else:
        security_status = "CRITICAL"
    
    # Get daily/hourly breakdown for time-based analysis
    time_breakdown = _get_time_breakdown(start_date, end_date, report_type)
    
    return {
        "report_type": report_type,
        "report_date": datetime.utcnow().isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "summary": {
            "total_logs": log_stats.get("total_logs", 0),
            "security_score": security_score,
            "security_status": security_status,
            "threat_summary": threat_summary
        },
        "log_statistics": {
            "severity_distribution": log_stats.get("severity_counts", {}),
            "event_type_distribution": log_stats.get("event_type_counts", {}),
            "protocol_distribution": log_stats.get("protocol_counts", {}),
            "top_source_ips": log_stats.get("top_source_ips", [])[:10],
            "top_ports": log_stats.get("top_ports", [])[:10],
            "time_breakdown": time_breakdown
        },
        "threat_detections": {
            "brute_force_attacks": [
                {
                    "source_ip": d.get("source_ip"),
                    "total_attempts": d.get("total_attempts", 0),
                    "severity": d.get("severity", "LOW"),
                    "first_attempt": d.get("first_attempt").isoformat() if d.get("first_attempt") else None,
                    "last_attempt": d.get("last_attempt").isoformat() if d.get("last_attempt") else None
                }
                for d in brute_force_detections
            ],
            "ddos_attacks": [
                {
                    "attack_type": d.get("attack_type"),
                    "source_ip_count": d.get("source_ip_count", 0),
                    "total_requests": d.get("total_requests", 0),
                    "peak_request_rate": d.get("peak_request_rate", 0),
                    "target_port": d.get("target_port"),
                    "target_protocol": d.get("target_protocol"),
                    "severity": d.get("severity", "LOW"),
                    "first_request": d.get("first_request").isoformat() if d.get("first_request") else None,
                    "last_request": d.get("last_request").isoformat() if d.get("last_request") else None
                }
                for d in ddos_detections
            ]
        },
        "top_threat_sources": top_threat_sources,
        "recommendations": _generate_recommendations(
            threat_summary, brute_force_detections, ddos_detections, log_stats
        )
    }


def _severity_level(severity: str) -> int:
    """Convert severity string to numeric level for comparison"""
    levels = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1
    }
    return levels.get(severity, 0)


def _get_time_breakdown(start_date: datetime, end_date: datetime, report_type: str) -> List[Dict]:
    """Get time-based breakdown of logs and threats"""
    from app.db.mongo import logs_collection
    from pymongo import ASCENDING
    
    time_diff = (end_date - start_date).total_seconds()
    
    # Determine grouping interval based on report type
    if report_type == "DAILY":
        # Hourly breakdown
        format_str = "%Y-%m-%dT%H:00:00"
        group_format = "%H:00"
    elif report_type == "WEEKLY":
        # Daily breakdown
        format_str = "%Y-%m-%dT00:00:00"
        group_format = "%Y-%m-%d"
    else:
        # Custom: hourly if < 7 days, daily if >= 7 days
        if time_diff < 7 * 24 * 3600:
            format_str = "%Y-%m-%dT%H:00:00"
            group_format = "%Y-%m-%d %H:00"
        else:
            format_str = "%Y-%m-%dT00:00:00"
            group_format = "%Y-%m-%d"
    
    query = {
        "timestamp": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": format_str,
                        "date": "$timestamp"
                    }
                },
                "count": {"$sum": 1},
                "high_severity": {
                    "$sum": {"$cond": [{"$eq": ["$severity", "HIGH"]}, 1, 0]}
                }
            }
        },
        {"$sort": {"_id": ASCENDING}},
        {"$project": {
            "time": "$_id",
            "count": 1,
            "high_severity": 1,
            "_id": 0
        }}
    ]
    
    return list(logs_collection.aggregate(pipeline))


def _generate_recommendations(
    threat_summary: Dict,
    brute_force_detections: List[Dict],
    ddos_detections: List[Dict],
    log_stats: Dict
) -> List[str]:
    """Generate security recommendations based on the report data"""
    recommendations = []
    
    if threat_summary["critical_threats"] > 0:
        recommendations.append(
            f"CRITICAL: {threat_summary['critical_threats']} critical threat(s) detected. "
            "Immediate action required - consider blocking source IPs and reviewing firewall rules."
        )
    
    if threat_summary["total_brute_force_attacks"] > 10:
        recommendations.append(
            f"High number of brute force attacks detected ({threat_summary['total_brute_force_attacks']}). "
            "Consider implementing IP-based rate limiting and fail2ban."
        )
    
    if threat_summary["total_ddos_attacks"] > 0:
        recommendations.append(
            f"DDoS attacks detected ({threat_summary['total_ddos_attacks']}). "
            "Consider implementing DDoS protection services and rate limiting at the firewall level."
        )
    
    high_severity_logs = log_stats.get("severity_counts", {}).get("HIGH", 0)
    if high_severity_logs > 1000:
        recommendations.append(
            f"High volume of HIGH severity logs ({high_severity_logs}). "
            "Review and optimize firewall rules to reduce false positives."
        )
    
    # Check for suspicious ports
    top_ports = log_stats.get("top_ports", [])
    suspicious_ports = [22, 23, 1433, 3306, 3389]  # SSH, Telnet, MSSQL, MySQL, RDP
    for port_info in top_ports:
        if port_info.get("port") in suspicious_ports:
            recommendations.append(
                f"High traffic on port {port_info['port']} detected. "
                "Ensure this port is properly secured and access is restricted."
            )
    
    if not recommendations:
        recommendations.append("No critical issues detected. Continue monitoring and maintain current security posture.")
    
    return recommendations

