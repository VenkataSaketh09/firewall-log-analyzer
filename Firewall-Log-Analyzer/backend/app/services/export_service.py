from typing import Dict, Any
import csv
import io
import json
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


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
    
    # Summary section (optional)
    summary = report_data.get("summary")
    if summary:
        writer.writerow(["SUMMARY"])
        writer.writerow(["Total Logs", summary.get("total_logs", 0)])
        writer.writerow(["Security Score", summary.get("security_score", 0)])
        writer.writerow(["Security Status", summary.get("security_status", "UNKNOWN")])

        threat_summary = summary.get("threat_summary", {}) or {}
        writer.writerow(["Total Threats", threat_summary.get("total_threats", 0)])
        writer.writerow(["Critical Threats", threat_summary.get("critical_threats", 0)])
        writer.writerow(["High Threats", threat_summary.get("high_threats", 0)])
        writer.writerow(["Medium Threats", threat_summary.get("medium_threats", 0)])
        writer.writerow(["Low Threats", threat_summary.get("low_threats", 0)])
        writer.writerow([])
    
    # Log Statistics (optional)
    log_stats = report_data.get("log_statistics")
    if log_stats:
        writer.writerow(["LOG STATISTICS - SEVERITY DISTRIBUTION"])
        writer.writerow(["Severity", "Count"])
        for severity, count in (log_stats.get("severity_distribution", {}) or {}).items():
            writer.writerow([severity, count])
        writer.writerow([])

        writer.writerow(["LOG STATISTICS - EVENT TYPE DISTRIBUTION"])
        writer.writerow(["Event Type", "Count"])
        for event_type, count in (log_stats.get("event_type_distribution", {}) or {}).items():
            writer.writerow([event_type, count])
        writer.writerow([])

        writer.writerow(["TOP SOURCE IPs"])
        writer.writerow(["IP Address", "Total Count", "HIGH", "MEDIUM", "LOW"])
        for ip_info in log_stats.get("top_source_ips", []) or []:
            severity_breakdown = ip_info.get("severity_breakdown", {}) or {}
            writer.writerow([
                ip_info.get("source_ip", ""),
                ip_info.get("count", 0),
                severity_breakdown.get("HIGH", 0),
                severity_breakdown.get("MEDIUM", 0),
                severity_breakdown.get("LOW", 0)
            ])
        writer.writerow([])

        writer.writerow(["TOP PORTS"])
        writer.writerow(["Port", "Count", "Protocol"])
        for port_info in log_stats.get("top_ports", []) or []:
            writer.writerow([
                port_info.get("port", ""),
                port_info.get("count", 0),
                port_info.get("protocol", "")
            ])
        writer.writerow([])

        time_breakdown = log_stats.get("time_breakdown", []) or []
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
    
    # Threat Detections (optional)
    threat_detections = report_data.get("threat_detections")
    if threat_detections:
        writer.writerow(["BRUTE FORCE ATTACKS"])
        writer.writerow(["Source IP", "Total Attempts", "Severity", "First Attempt", "Last Attempt"])
        for attack in threat_detections.get("brute_force_attacks", []) or []:
            writer.writerow([
                attack.get("source_ip", ""),
                attack.get("total_attempts", 0),
                attack.get("severity", ""),
                attack.get("first_attempt", ""),
                attack.get("last_attempt", "")
            ])
        writer.writerow([])

        writer.writerow(["DDOS ATTACKS"])
        writer.writerow(["Attack Type", "Source IP Count", "Total Requests", "Peak Rate (req/min)",
                         "Target Port", "Target Protocol", "Severity", "First Request", "Last Request"])
        for attack in threat_detections.get("ddos_attacks", []) or []:
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

        port_scans = threat_detections.get("port_scan_attacks", []) or []
        if port_scans:
            writer.writerow(["PORT SCAN ATTACKS"])
            writer.writerow(["Source IP", "Total Attempts", "Unique Ports", "Severity", "First Attempt", "Last Attempt"])
            for attack in port_scans:
                writer.writerow([
                    attack.get("source_ip", ""),
                    attack.get("total_attempts", 0),
                    attack.get("unique_ports_attempted", 0),
                    attack.get("severity", ""),
                    attack.get("first_attempt", ""),
                    attack.get("last_attempt", "")
                ])
            writer.writerow([])
    
    top_sources = report_data.get("top_threat_sources") or []
    if top_sources:
        writer.writerow(["TOP THREAT SOURCES"])
        writer.writerow(["IP Address", "Brute Force Attacks", "DDoS Attacks", "Total Attempts", "Severity"])
        for source in top_sources:
            writer.writerow([
                source.get("ip", ""),
                source.get("brute_force_attacks", 0),
                source.get("ddos_attacks", 0),
                source.get("total_attempts", 0),
                source.get("severity", "")
            ])
        writer.writerow([])
    
    recs = report_data.get("recommendations") or []
    if recs:
        writer.writerow(["RECOMMENDATIONS"])
        for i, recommendation in enumerate(recs, 1):
            writer.writerow([f"{i}. {recommendation}"])

    # Detailed Logs (optional; truncated)
    detailed = report_data.get("detailed_logs") or []
    if detailed:
        writer.writerow([])
        writer.writerow(["DETAILED LOGS (TRUNCATED)"])
        writer.writerow(["Timestamp", "Source IP", "Dest IP", "Dest Port", "Protocol", "Log Source", "Event Type", "Severity", "Username", "Raw Log"])
        for log in detailed:
            writer.writerow([
                log.get("timestamp", ""),
                log.get("source_ip", ""),
                log.get("destination_ip", ""),
                log.get("destination_port", ""),
                log.get("protocol", ""),
                log.get("log_source", ""),
                log.get("event_type", ""),
                log.get("severity", ""),
                log.get("username", ""),
                log.get("raw_log", ""),
            ])
    
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


def export_to_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Export report data as a real PDF (bytes) for backend-generated PDF download.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        title="Firewall Security Report"
    )
    styles = getSampleStyleSheet()
    story = []

    report_type = report_data.get("report_type", "UNKNOWN")
    period = report_data.get("period", {})
    summary = report_data.get("summary") or None
    log_stats = report_data.get("log_statistics") or None
    threat_detections = report_data.get("threat_detections") or None

    story.append(Paragraph("Firewall Security Report", styles["Title"]))
    story.append(Paragraph(f"Report Type: <b>{report_type}</b>", styles["Normal"]))
    story.append(Paragraph(f"Period: {period.get('start', '')} to {period.get('end', '')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Summary block (optional)
    if summary:
        story.append(Paragraph("Summary", styles["Heading2"]))
        threat_summary = summary.get("threat_summary", {}) or {}
        summary_rows = [
            ["Total Logs", str(summary.get("total_logs", 0))],
            ["Security Score", str(summary.get("security_score", 0))],
            ["Security Status", str(summary.get("security_status", "UNKNOWN"))],
            ["Total Threats", str(threat_summary.get("total_threats", 0))],
            ["Critical Threats", str(threat_summary.get("critical_threats", 0))],
            ["High Threats", str(threat_summary.get("high_threats", 0))],
            ["Medium Threats", str(threat_summary.get("medium_threats", 0))],
            ["Low Threats", str(threat_summary.get("low_threats", 0))],
        ]
        t = Table(summary_rows, colWidths=[180, 340])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ]))
        story.append(t)
        story.append(Spacer(1, 14))

    # Top IPs (optional)
    if log_stats:
        story.append(Paragraph("Top Source IPs", styles["Heading2"]))
        top_ips = log_stats.get("top_source_ips", []) or []
        ip_table_data = [["IP Address", "Total", "HIGH", "MEDIUM", "LOW"]]
        for ip_info in top_ips[:10]:
            sev = ip_info.get("severity_breakdown", {}) or {}
            ip_table_data.append([
                str(ip_info.get("source_ip", "")),
                str(ip_info.get("count", 0)),
                str(sev.get("HIGH", 0)),
                str(sev.get("MEDIUM", 0)),
                str(sev.get("LOW", 0)),
            ])
        ip_table = Table(ip_table_data, colWidths=[170, 70, 70, 70, 70])
        ip_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(ip_table)
        story.append(Spacer(1, 14))

        # Top Ports
        story.append(Paragraph("Top Ports", styles["Heading2"]))
        top_ports = log_stats.get("top_ports", []) or []
        port_table_data = [["Port", "Count", "Protocol"]]
        for p in top_ports[:10]:
            port_table_data.append([
                str(p.get("port", "")),
                str(p.get("count", 0)),
                str(p.get("protocol", "") or ""),
            ])
        port_table = Table(port_table_data, colWidths=[100, 100, 360])
        port_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(port_table)
        story.append(Spacer(1, 14))

    # Threat tables (optional)
    if threat_detections:
        story.append(Paragraph("Threat Detections - Brute Force", styles["Heading2"]))
        bf = threat_detections.get("brute_force_attacks", []) or []
        bf_table_data = [["Source IP", "Attempts", "Severity", "First", "Last"]]
        for a in bf[:20]:
            bf_table_data.append([
                str(a.get("source_ip", "")),
                str(a.get("total_attempts", 0)),
                str(a.get("severity", "")),
                str(a.get("first_attempt", "") or ""),
                str(a.get("last_attempt", "") or ""),
            ])
        bf_table = Table(bf_table_data, colWidths=[120, 60, 70, 135, 135])
        bf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(bf_table)
        story.append(Spacer(1, 14))

        story.append(Paragraph("Threat Detections - DDoS", styles["Heading2"]))
        dd = threat_detections.get("ddos_attacks", []) or []
        dd_table_data = [["Type", "IPs", "Requests", "Peak Rate", "Target Port", "Severity"]]
        for a in dd[:20]:
            dd_table_data.append([
                str(a.get("attack_type", "")),
                str(a.get("source_ip_count", 0)),
                str(a.get("total_requests", 0)),
                str(a.get("peak_request_rate", 0)),
                str(a.get("target_port", "") or ""),
                str(a.get("severity", "")),
            ])
        dd_table = Table(dd_table_data, colWidths=[140, 50, 70, 80, 90, 80])
        dd_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(dd_table)
        story.append(Spacer(1, 14))

        ps = threat_detections.get("port_scan_attacks", []) or []
        if ps:
            story.append(Paragraph("Threat Detections - Port Scans", styles["Heading2"]))
            ps_table_data = [["Source IP", "Attempts", "Unique Ports", "Severity", "First", "Last"]]
            for a in ps[:20]:
                ps_table_data.append([
                    str(a.get("source_ip", "")),
                    str(a.get("total_attempts", 0)),
                    str(a.get("unique_ports_attempted", 0)),
                    str(a.get("severity", "")),
                    str(a.get("first_attempt", "") or ""),
                    str(a.get("last_attempt", "") or ""),
                ])
            ps_table = Table(ps_table_data, colWidths=[120, 60, 75, 70, 95, 100])
            ps_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            story.append(ps_table)
            story.append(Spacer(1, 14))

    # Recommendations (optional)
    recs = report_data.get("recommendations", []) or []
    if recs:
        story.append(Paragraph("Recommendations", styles["Heading2"]))
        for r in recs[:20]:
            story.append(Paragraph(f"- {str(r)}", styles["Normal"]))
        story.append(Spacer(1, 8))

    # Detailed logs (optional, truncated)
    detailed = report_data.get("detailed_logs") or []
    if detailed:
        story.append(Paragraph("Detailed Logs (Truncated)", styles["Heading2"]))
        dl_table_data = [["Timestamp", "Source IP", "Event Type", "Severity", "Raw Log"]]
        for log in detailed[:100]:
            dl_table_data.append([
                str(log.get("timestamp", "") or ""),
                str(log.get("source_ip", "") or ""),
                str(log.get("event_type", "") or ""),
                str(log.get("severity", "") or ""),
                str(log.get("raw_log", "") or "")[:200],
            ])
        dl_table = Table(dl_table_data, colWidths=[120, 90, 120, 70, 150])
        dl_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(dl_table)
        story.append(Spacer(1, 14))

    doc.build(story)
    return buf.getvalue()


def export_logs_to_pdf(logs: list[Dict[str, Any]], title: str = "Logs Export") -> bytes:
    """
    Export a list of logs as a PDF with color-coded rows based on severity.
    Intended for per-log export (not summary reports).
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        title=title
    )
    styles = getSampleStyleSheet()

    # Smaller text for dense tables
    small = styles["BodyText"].clone("SmallBody")
    small.fontSize = 7
    small.leading = 9

    story = []
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles["Normal"]))
    story.append(Spacer(1, 10))

    # Keep table narrow enough for LETTER with default margins (width ~468pt)
    headers = ["Timestamp", "Source IP", "Event", "Sev", "Port", "Proto", "Message"]
    table_data = [headers]

    def sev_bg(sev: str):
        s = (sev or "").upper()
        if s == "CRITICAL":
            return colors.HexColor("#FEE2E2")  # light red
        if s == "HIGH":
            return colors.HexColor("#FFEDD5")  # light orange
        if s == "MEDIUM":
            return colors.HexColor("#FEF9C3")  # light yellow
        if s == "LOW":
            return colors.HexColor("#DCFCE7")  # light green
        return colors.HexColor("#F3F4F6")      # gray

    for log in logs:
        ts = log.get("timestamp", "") or ""
        src = log.get("source_ip", "") or ""
        event = log.get("event_type", "") or ""
        sev = log.get("severity", "") or ""
        port = log.get("destination_port", "") or ""
        proto = log.get("protocol", "") or ""
        raw = (log.get("raw_log", "") or "")

        # Truncate slightly; wrapping is allowed but we keep things readable.
        if len(raw) > 400:
            raw = raw[:400] + "…"

        table_data.append([
            Paragraph(str(ts), small),
            Paragraph(str(src), small),
            Paragraph(str(event), small),
            Paragraph(str(sev), small),
            Paragraph(str(port), small),
            Paragraph(str(proto), small),
            Paragraph(str(raw), small),
        ])

    col_widths = [85, 60, 80, 45, 35, 35, 128]  # sums to 468
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]

    # Color-code body rows by severity
    for i in range(1, len(table_data)):
        sev = logs[i - 1].get("severity")
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), sev_bg(sev)))

    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    doc.build(story)
    return buf.getvalue()

