from datetime import datetime, timedelta
from typing import Optional, Dict, List
from app.services.log_queries import get_statistics
from app.services.brute_force_detection import detect_brute_force
from app.services.ddos_detection import detect_ddos
from app.services.port_scan_detection import detect_port_scan
from app.services.virustotal_service import get_multiple_ip_reputations
from app.db.mongo import logs_collection


def generate_daily_report(
    date: Optional[datetime] = None,
    include_charts: bool = True,
    include_summary: bool = True,
    include_threats: bool = True,
    include_logs: bool = False,
) -> Dict:
    """
    Generate a daily security report for a specific date.
    
    Args:
        date: Date to generate report for (default: today)
        include_charts: Include chart/statistics sections
        include_summary: Include executive summary section
        include_threats: Include threats sections
        include_logs: Include detailed logs section
    
    Returns:
        Dictionary containing comprehensive daily security report
    """
    if date is None:
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_date = date
    end_date = date + timedelta(days=1) - timedelta(microseconds=1)
    
    return _generate_report(
        start_date, 
        end_date, 
        "DAILY",
        include_charts=include_charts,
        include_summary=include_summary,
        include_threats=include_threats,
        include_logs=include_logs,
    )


def generate_weekly_report(
    start_date: Optional[datetime] = None,
    include_charts: bool = True,
    include_summary: bool = True,
    include_threats: bool = True,
    include_logs: bool = False,
) -> Dict:
    """
    Generate a weekly security report for the past 7 days.
    
    Args:
        start_date: Start date of the week (default: 7 days ago)
        include_charts: Include chart/statistics sections
        include_summary: Include executive summary section
        include_threats: Include threats sections
        include_logs: Include detailed logs section
    
    Returns:
        Dictionary containing comprehensive weekly security report
    """
    if start_date is None:
        start_date = (datetime.utcnow() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Ensure start_date is a datetime object and set to beginning of day
        if isinstance(start_date, datetime):
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # If it's a string or other type, convert it
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    
    # End date: use current time (not end of day) to avoid including future timestamps
    end_date = datetime.utcnow()
    
    return _generate_report(
        start_date, 
        end_date, 
        "WEEKLY",
        include_charts=include_charts,
        include_summary=include_summary,
        include_threats=include_threats,
        include_logs=include_logs,
    )


def generate_custom_report(
    start_date: datetime,
    end_date: datetime,
    include_charts: bool = True,
    include_summary: bool = True,
    include_threats: bool = True,
    include_logs: bool = False,
    detailed_logs_limit: int = 500,
) -> Dict:
    """
    Generate a custom date range security report.
    
    Args:
        start_date: Start date for the report
        end_date: End date for the report
    
    Returns:
        Dictionary containing comprehensive security report
    """
    return _generate_report(
        start_date,
        end_date,
        "CUSTOM",
        include_charts=include_charts,
        include_summary=include_summary,
        include_threats=include_threats,
        include_logs=include_logs,
        detailed_logs_limit=detailed_logs_limit,
    )


def _generate_report(
    start_date: datetime,
    end_date: datetime,
    report_type: str,
    include_charts: bool = True,
    include_summary: bool = True,
    include_threats: bool = True,
    include_logs: bool = False,
    detailed_logs_limit: int = 500,
) -> Dict:
    """
    Internal function to generate comprehensive security reports.
    """
    # Only compute what we might return; this makes include_* options meaningful and reduces work.
    needs_log_stats = include_charts or include_summary or include_logs
    needs_threats = include_threats or include_summary

    log_stats = get_statistics(start_date=start_date, end_date=end_date) if needs_log_stats else {}

    brute_force_detections = []
    ddos_detections = []
    port_scan_detections = []
    if needs_threats:
        brute_force_detections = detect_brute_force(
            time_window_minutes=15,
            threshold=5,
            start_date=start_date,
            end_date=end_date
        )
        ddos_detections = detect_ddos(
            time_window_seconds=60,
            single_ip_threshold=100,
            distributed_ip_count=10,
            distributed_request_threshold=500,
            start_date=start_date,
            end_date=end_date
        )
        port_scan_detections = detect_port_scan(
            time_window_minutes=10,
            unique_ports_threshold=10,
            min_total_attempts=20,
            start_date=start_date,
            end_date=end_date
        )
        
        # #region agent log
        import json
        with open('/home/saketh/firewall-log-analyzer/Firewall-Log-Analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G",
                "location": "report_service.py:166",
                "message": "Reports page: detect_port_scan returned",
                "data": {
                    "report_type": report_type,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "time_window_minutes": 10,
                    "unique_ports_threshold": 10,
                    "min_total_attempts": 20,
                    "total_detections": len(port_scan_detections),
                    "detections": [{"source_ip": d.get("source_ip"), "severity": d.get("severity"), "unique_ports_attempted": d.get("unique_ports_attempted"), "last_attempt": d.get("last_attempt").isoformat() if d.get("last_attempt") else None} for d in port_scan_detections]
                },
                "timestamp": datetime.utcnow().timestamp() * 1000
            }) + '\n')
        # #endregion
    
    threat_summary = None
    if include_summary:
        # Calculate threat summary (only needed for executive summary / score)
        threat_summary = {
            "total_brute_force_attacks": len(brute_force_detections),
            "total_ddos_attacks": len(ddos_detections),
            "total_port_scan_attacks": len(port_scan_detections),
            "total_threats": len(brute_force_detections) + len(ddos_detections) + len(port_scan_detections),
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

        for detection in port_scan_detections:
            severity = detection.get("severity", "LOW")
            if severity == "CRITICAL":
                threat_summary["critical_threats"] += 1
            elif severity == "HIGH":
                threat_summary["high_threats"] += 1
            elif severity == "MEDIUM":
                threat_summary["medium_threats"] += 1
            else:
                threat_summary["low_threats"] += 1
    
    top_threat_sources = []
    malicious_ip_analysis = None
    if include_threats:
        # Get top threat sources (from brute force, DDoS, port scan)
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
                current_sev = threat_sources[ip]["severity"]
                det_sev = detection.get("severity", "LOW")
                if _severity_level(det_sev) > _severity_level(current_sev):
                    threat_sources[ip]["severity"] = det_sev

        for detection in port_scan_detections:
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
                threat_sources[ip]["total_attempts"] += detection.get("total_attempts", 0)
                current_sev = threat_sources[ip]["severity"]
                det_sev = detection.get("severity", "LOW")
                if _severity_level(det_sev) > _severity_level(current_sev):
                    threat_sources[ip]["severity"] = det_sev

        top_threat_sources = sorted(
            list(threat_sources.values()),
            key=lambda x: x["total_attempts"],
            reverse=True
        )[:20]

        malicious_ip_analysis = _analyze_malicious_ips(top_threat_sources)
    
    security_score = None
    security_status = None
    if include_summary and threat_summary is not None:
        # Calculate security score (0-100, higher is better)
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
    
    time_breakdown = _get_time_breakdown(start_date, end_date, report_type) if include_charts else None

    report_doc: Dict = {
        "report_type": report_type,
        "report_date": datetime.utcnow().isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    }

    if include_summary and threat_summary is not None:
        report_doc["summary"] = {
            "total_logs": log_stats.get("total_logs", 0),
            "security_score": security_score or 0,
            "security_status": security_status or "UNKNOWN",
            "threat_summary": threat_summary
        }

    if include_charts:
        report_doc["log_statistics"] = {
            "severity_distribution": log_stats.get("severity_counts", {}),
            "event_type_distribution": log_stats.get("event_type_counts", {}),
            "protocol_distribution": log_stats.get("protocol_counts", {}),
            "top_source_ips": (log_stats.get("top_source_ips", []) or [])[:10],
            "top_ports": (log_stats.get("top_ports", []) or [])[:10],
            "time_breakdown": time_breakdown or []
        }

    if include_threats:
        report_doc["threat_detections"] = {
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
            ],
            "port_scan_attacks": [
                {
                    "source_ip": d.get("source_ip"),
                    "total_attempts": d.get("total_attempts", 0),
                    "unique_ports_attempted": d.get("unique_ports_attempted", 0),
                    "severity": d.get("severity", "LOW"),
                    "first_attempt": d.get("first_attempt").isoformat() if d.get("first_attempt") else None,
                    "last_attempt": d.get("last_attempt").isoformat() if d.get("last_attempt") else None
                }
                for d in port_scan_detections
            ]
        }
        report_doc["top_threat_sources"] = top_threat_sources
        report_doc["malicious_ip_analysis"] = malicious_ip_analysis

    if include_summary and threat_summary is not None:
        report_doc["recommendations"] = _generate_recommendations(
            threat_summary, brute_force_detections, ddos_detections, log_stats, malicious_ip_analysis
        )

    if include_logs:
        # Include raw logs (truncated) to support "Include Detailed Logs"
        cursor = (
            logs_collection.find(
                {"timestamp": {"$gte": start_date, "$lte": end_date}},
                {
                    "_id": 1,
                    "timestamp": 1,
                    "source_ip": 1,
                    "destination_ip": 1,
                    "destination_port": 1,
                    "protocol": 1,
                    "log_source": 1,
                    "event_type": 1,
                    "severity": 1,
                    "username": 1,
                    "raw_log": 1,
                },
            )
            .sort("timestamp", -1)
            .limit(max(0, int(detailed_logs_limit)))
        )
        detailed_logs = []
        for log in cursor:
            detailed_logs.append(
                {
                    "id": str(log.get("_id")),
                    "timestamp": log.get("timestamp").isoformat() if log.get("timestamp") else None,
                    "source_ip": log.get("source_ip"),
                    "destination_ip": log.get("destination_ip"),
                    "destination_port": log.get("destination_port"),
                    "protocol": log.get("protocol"),
                    "log_source": log.get("log_source"),
                    "event_type": log.get("event_type"),
                    "severity": log.get("severity"),
                    "username": log.get("username"),
                    "raw_log": log.get("raw_log"),
                }
            )
        report_doc["detailed_logs"] = detailed_logs

    return report_doc


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


def _analyze_malicious_ips(top_threat_sources: List[Dict]) -> Dict:
    """Analyze top threat source IPs using VirusTotal reputation"""
    if not top_threat_sources:
        return {
            "total_ips_checked": 0,
            "malicious_ips": 0,
            "suspicious_ips": 0,
            "clean_ips": 0,
            "unknown_ips": 0,
            "malicious_ip_list": []
        }
    
    # Get reputation for top threat source IPs (limit to top 20)
    ip_addresses = [source["ip"] for source in top_threat_sources[:20] if source.get("ip")]
    reputation_data = get_multiple_ip_reputations(ip_addresses)
    
    malicious_ips = []
    suspicious_ips = []
    clean_ips = []
    unknown_ips = []
    
    for ip, rep in reputation_data.items():
        if not rep or rep.get("error"):
            unknown_ips.append(ip)
            continue
        
        threat_level = rep.get("threat_level", "UNKNOWN")
        detected = rep.get("detected", False)
        
        if threat_level in ["CRITICAL", "HIGH"] or detected:
            malicious_ips.append({
                "ip": ip,
                "threat_level": threat_level,
                "reputation_score": rep.get("reputation_score", 0),
                "malicious_count": rep.get("malicious_count", 0),
                "country": rep.get("country"),
                "categories": rep.get("categories", [])
            })
        elif threat_level == "MEDIUM" or rep.get("suspicious_count", 0) > 0:
            suspicious_ips.append(ip)
        else:
            clean_ips.append(ip)
    
    return {
        "total_ips_checked": len(ip_addresses),
        "malicious_ips": len(malicious_ips),
        "suspicious_ips": len(suspicious_ips),
        "clean_ips": len(clean_ips),
        "unknown_ips": len(unknown_ips),
        "malicious_ip_list": malicious_ips
    }


def _generate_recommendations(
    threat_summary: Dict,
    brute_force_detections: List[Dict],
    ddos_detections: List[Dict],
    log_stats: Dict,
    malicious_ip_analysis: Optional[Dict] = None
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
    
    # Add recommendations based on malicious IP analysis
    if malicious_ip_analysis:
        malicious_count = malicious_ip_analysis.get("malicious_ips", 0)
        if malicious_count > 0:
            recommendations.append(
                f"CRITICAL: {malicious_count} known malicious IP(s) detected in threat sources. "
                "Immediately block these IPs in your firewall: " +
                ", ".join([ip["ip"] for ip in malicious_ip_analysis.get("malicious_ip_list", [])[:5]])
            )
        
        suspicious_count = malicious_ip_analysis.get("suspicious_ips", 0)
        if suspicious_count > 0:
            recommendations.append(
                f"Warning: {suspicious_count} suspicious IP(s) detected. "
                "Monitor these IPs closely and consider implementing additional security measures."
            )
    
    if not recommendations:
        recommendations.append("No critical issues detected. Continue monitoring and maintain current security posture.")
    
    return recommendations

