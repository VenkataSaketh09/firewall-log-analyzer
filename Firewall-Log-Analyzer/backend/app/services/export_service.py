from typing import Dict, Any
import csv
import io
import json
from datetime import datetime


def export_to_json(report_data: Dict[str, Any]) -> str:
    """
    Export report data to JSON format.
    
    Args:
        report_data: Report data dictionary
    
    Returns:
        JSON string representation of the report
    """
    return json.dumps(report_data, indent=2, default=str)


def export_to_csv(report_data: Dict[str, Any]) -> str:
    """
    Export report data to CSV format.
    Creates multiple sections for different data types.
    
    Args:
        report_data: Report data dictionary
    
    Returns:
        CSV string representation of the report
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Firewall Security Report"])
    writer.writerow(["Generated:", datetime.utcnow().isoformat()])
    writer.writerow(["Report Type:", report_data.get("report_type", "UNKNOWN")])
    writer.writerow(["Period:", f"{report_data.get('period', {}).get('start')} to {report_data.get('period', {}).get('end')}"])
    writer.writerow([])
    
    # Summary section
    summary = report_data.get("summary", {})
    writer.writerow(["SUMMARY"])
    writer.writerow(["Total Logs", summary.get("total_logs", 0)])
    writer.writerow(["Security Score", summary.get("security_score", 0)])
    writer.writerow(["Security Status", summary.get("security_status", "UNKNOWN")])
    
    threat_summary = summary.get("threat_summary", {})
    writer.writerow(["Total Threats", threat_summary.get("total_threats", 0)])
    writer.writerow(["Critical Threats", threat_summary.get("critical_threats", 0)])
    writer.writerow(["High Threats", threat_summary.get("high_threats", 0)])
    writer.writerow(["Medium Threats", threat_summary.get("medium_threats", 0)])
    writer.writerow(["Low Threats", threat_summary.get("low_threats", 0)])
    writer.writerow([])
    
    # Log Statistics - Severity Distribution
    log_stats = report_data.get("log_statistics", {})
    writer.writerow(["LOG STATISTICS - SEVERITY DISTRIBUTION"])
    writer.writerow(["Severity", "Count"])
    for severity, count in log_stats.get("severity_distribution", {}).items():
        writer.writerow([severity, count])
    writer.writerow([])
    
    # Log Statistics - Event Types
    writer.writerow(["LOG STATISTICS - EVENT TYPE DISTRIBUTION"])
    writer.writerow(["Event Type", "Count"])
    for event_type, count in log_stats.get("event_type_distribution", {}).items():
        writer.writerow([event_type, count])
    writer.writerow([])
    
    # Top Source IPs
    writer.writerow(["TOP SOURCE IPs"])
    writer.writerow(["IP Address", "Total Count", "HIGH", "MEDIUM", "LOW"])
    for ip_info in log_stats.get("top_source_ips", []):
        severity_breakdown = ip_info.get("severity_breakdown", {})
        writer.writerow([
            ip_info.get("source_ip", ""),
            ip_info.get("count", 0),
            severity_breakdown.get("HIGH", 0),
            severity_breakdown.get("MEDIUM", 0),
            severity_breakdown.get("LOW", 0)
        ])
    writer.writerow([])
    
    # Top Ports
    writer.writerow(["TOP PORTS"])
    writer.writerow(["Port", "Count", "Protocol"])
    for port_info in log_stats.get("top_ports", []):
        writer.writerow([
            port_info.get("port", ""),
            port_info.get("count", 0),
            port_info.get("protocol", "")
        ])
    writer.writerow([])
    
    # Time Breakdown
    time_breakdown = log_stats.get("time_breakdown", [])
    if time_breakdown:
        writer.writerow(["TIME BREAKDOWN"])
        writer.writerow(["Time", "Total Logs", "High Severity"])
        for time_entry in time_breakdown:
            writer.writerow([
                time_entry.get("time", ""),
                time_entry.get("count", 0),
                time_entry.get("high_severity", 0)
            ])
        writer.writerow([])
    
    # Brute Force Attacks
    threat_detections = report_data.get("threat_detections", {})
    writer.writerow(["BRUTE FORCE ATTACKS"])
    writer.writerow(["Source IP", "Total Attempts", "Severity", "First Attempt", "Last Attempt"])
    for attack in threat_detections.get("brute_force_attacks", []):
        writer.writerow([
            attack.get("source_ip", ""),
            attack.get("total_attempts", 0),
            attack.get("severity", ""),
            attack.get("first_attempt", ""),
            attack.get("last_attempt", "")
        ])
    writer.writerow([])
    
    # DDoS Attacks
    writer.writerow(["DDOS ATTACKS"])
    writer.writerow(["Attack Type", "Source IP Count", "Total Requests", "Peak Rate (req/min)", 
                     "Target Port", "Target Protocol", "Severity", "First Request", "Last Request"])
    for attack in threat_detections.get("ddos_attacks", []):
        writer.writerow([
            attack.get("attack_type", ""),
            attack.get("source_ip_count", 0),
            attack.get("total_requests", 0),
            attack.get("peak_request_rate", 0),
            attack.get("target_port", ""),
            attack.get("target_protocol", ""),
            attack.get("severity", ""),
            attack.get("first_request", ""),
            attack.get("last_request", "")
        ])
    writer.writerow([])
    
    # Top Threat Sources
    writer.writerow(["TOP THREAT SOURCES"])
    writer.writerow(["IP Address", "Brute Force Attacks", "DDoS Attacks", "Total Attempts", "Severity"])
    for source in report_data.get("top_threat_sources", []):
        writer.writerow([
            source.get("ip", ""),
            source.get("brute_force_attacks", 0),
            source.get("ddos_attacks", 0),
            source.get("total_attempts", 0),
            source.get("severity", "")
        ])
    writer.writerow([])
    
    # Recommendations
    writer.writerow(["RECOMMENDATIONS"])
    for i, recommendation in enumerate(report_data.get("recommendations", []), 1):
        writer.writerow([f"{i}. {recommendation}"])
    
    return output.getvalue()


def export_to_pdf_ready(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export report data in a PDF-ready format (structured data for PDF generation).
    This returns structured data that can be easily converted to PDF by frontend or external service.
    
    Args:
        report_data: Report data dictionary
    
    Returns:
        Dictionary with PDF-ready structured format
    """
    return {
        "metadata": {
            "title": f"{report_data.get('report_type', 'Security')} Security Report",
            "generated_at": datetime.utcnow().isoformat(),
            "period": report_data.get("period", {}),
            "report_type": report_data.get("report_type", "UNKNOWN")
        },
        "header": {
            "title": "Firewall Security Report",
            "subtitle": f"{report_data.get('report_type', 'Security')} Report",
            "generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "period": f"{report_data.get('period', {}).get('start', '')} to {report_data.get('period', {}).get('end', '')}"
        },
        "executive_summary": {
            "security_score": report_data.get("summary", {}).get("security_score", 0),
            "security_status": report_data.get("summary", {}).get("security_status", "UNKNOWN"),
            "total_logs": report_data.get("summary", {}).get("total_logs", 0),
            "threat_summary": report_data.get("summary", {}).get("threat_summary", {})
        },
        "sections": [
            {
                "title": "Log Statistics",
                "type": "statistics",
                "data": {
                    "severity_distribution": report_data.get("log_statistics", {}).get("severity_distribution", {}),
                    "event_type_distribution": report_data.get("log_statistics", {}).get("event_type_distribution", {}),
                    "protocol_distribution": report_data.get("log_statistics", {}).get("protocol_distribution", {})
                }
            },
            {
                "title": "Top Source IPs",
                "type": "table",
                "headers": ["IP Address", "Total Count", "HIGH", "MEDIUM", "LOW"],
                "rows": [
                    [
                        ip_info.get("source_ip", ""),
                        str(ip_info.get("count", 0)),
                        str(ip_info.get("severity_breakdown", {}).get("HIGH", 0)),
                        str(ip_info.get("severity_breakdown", {}).get("MEDIUM", 0)),
                        str(ip_info.get("severity_breakdown", {}).get("LOW", 0))
                    ]
                    for ip_info in report_data.get("log_statistics", {}).get("top_source_ips", [])
                ]
            },
            {
                "title": "Threat Detections - Brute Force Attacks",
                "type": "table",
                "headers": ["Source IP", "Total Attempts", "Severity", "First Attempt", "Last Attempt"],
                "rows": [
                    [
                        attack.get("source_ip", ""),
                        str(attack.get("total_attempts", 0)),
                        attack.get("severity", ""),
                        attack.get("first_attempt", "") or "",
                        attack.get("last_attempt", "") or ""
                    ]
                    for attack in report_data.get("threat_detections", {}).get("brute_force_attacks", [])
                ]
            },
            {
                "title": "Threat Detections - DDoS Attacks",
                "type": "table",
                "headers": ["Attack Type", "Source IPs", "Total Requests", "Peak Rate", "Target Port", "Severity"],
                "rows": [
                    [
                        attack.get("attack_type", ""),
                        str(attack.get("source_ip_count", 0)),
                        str(attack.get("total_requests", 0)),
                        f"{attack.get('peak_request_rate', 0):.2f} req/min",
                        str(attack.get("target_port", "") or ""),
                        attack.get("severity", "")
                    ]
                    for attack in report_data.get("threat_detections", {}).get("ddos_attacks", [])
                ]
            },
            {
                "title": "Recommendations",
                "type": "list",
                "items": report_data.get("recommendations", [])
            }
        ]
    }

