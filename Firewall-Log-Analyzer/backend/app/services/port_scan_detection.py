from datetime import datetime, timedelta
from typing import Optional, List, Dict
from collections import defaultdict

from pymongo import DESCENDING

from app.db.mongo import logs_collection


def detect_port_scan(
    time_window_minutes: int = 10,
    unique_ports_threshold: int = 10,
    min_total_attempts: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None,
    protocol: Optional[str] = None
) -> List[Dict]:
    """
    Detect port scanning behavior based on one source IP attempting multiple destination ports
    within a short time window.

    Args:
        time_window_minutes: Sliding window size in minutes
        unique_ports_threshold: Minimum unique destination ports in a window to flag port scan
        min_total_attempts: Minimum total connection attempts (logs) for the IP in the period
        start_date/end_date: Optional analysis time range (default: last 24h)
        source_ip: Optional specific IP to check
        protocol: Optional protocol filter (TCP/UDP)

    Returns:
        List of detections sorted by severity/unique ports
    """
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(hours=24)

    base_query = {
        "timestamp": {"$gte": start_date, "$lte": end_date},
        "source_ip": {"$ne": None},
        "destination_port": {"$ne": None},
    }
    if source_ip:
        base_query["source_ip"] = source_ip
    if protocol:
        base_query["protocol"] = protocol

    logs = list(
        logs_collection.find(
            base_query,
            {"source_ip": 1, "timestamp": 1, "destination_port": 1, "protocol": 1, "raw_log": 1, "log_source": 1, "event_type": 1, "_id": 1}
        ).sort("timestamp", DESCENDING)
    )
    if not logs:
        return []

    # Group by source IP
    ip_logs: Dict[str, List[Dict]] = defaultdict(list)
    for log in logs:
        ip = log.get("source_ip")
        if not ip:
            continue
        ip_logs[ip].append(log)

    detections: List[Dict] = []
    window_delta = timedelta(minutes=time_window_minutes)

    for ip, ip_log_list in ip_logs.items():
        if len(ip_log_list) < min_total_attempts:
            continue

        # Sort ascending for sliding window
        ip_log_list.sort(key=lambda x: x["timestamp"])

        attack_windows: List[Dict] = []
        i = 0
        while i < len(ip_log_list):
            window_start = ip_log_list[i]["timestamp"]
            window_end = window_start + window_delta

            j = i
            window_ports = set()
            window_attempts = []
            while j < len(ip_log_list) and ip_log_list[j]["timestamp"] <= window_end:
                port = ip_log_list[j].get("destination_port")
                if port is not None:
                    window_ports.add(int(port))
                # Keep attempts small in response
                if len(window_attempts) < 50:
                    window_attempts.append({
                        "timestamp": ip_log_list[j]["timestamp"],
                        "destination_port": ip_log_list[j].get("destination_port"),
                        "protocol": ip_log_list[j].get("protocol"),
                        "log_id": str(ip_log_list[j]["_id"]),
                        "raw_log": ip_log_list[j].get("raw_log", ""),
                        "log_source": ip_log_list[j].get("log_source", "ufw.log"),
                        "event_type": ip_log_list[j].get("event_type", "PORT_SCAN"),
                    })
                j += 1

            unique_ports = len(window_ports)
            if unique_ports >= unique_ports_threshold:
                attack_windows.append({
                    "window_start": window_start,
                    "window_end": ip_log_list[j - 1]["timestamp"] if j - 1 >= 0 else window_start,
                    "attempt_count": (j - i),
                    "unique_ports": unique_ports,
                    "ports": sorted(list(window_ports))[:50],
                    "attempts": window_attempts,
                })
                # Skip past this window to avoid heavy overlap
                i = j
            else:
                i += 1

        if not attack_windows:
            continue

        # Overall stats
        all_ports = set(int(l.get("destination_port")) for l in ip_log_list if l.get("destination_port") is not None)
        detections.append({
            "source_ip": ip,
            "total_attempts": len(ip_log_list),
            "unique_ports_attempted": len(all_ports),
            "ports_attempted": sorted(list(all_ports))[:100],
            "first_attempt": ip_log_list[0]["timestamp"],
            "last_attempt": ip_log_list[-1]["timestamp"],
            "attack_windows": attack_windows,
            "severity": _calculate_severity(len(all_ports), len(attack_windows), len(ip_log_list)),
        })

    detections.sort(key=lambda d: (
        {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(d.get("severity", "LOW"), 4),
        -d.get("unique_ports_attempted", 0),
        -d.get("total_attempts", 0),
    ))
    return detections


def _calculate_severity(unique_ports_attempted: int, window_count: int, total_attempts: int) -> str:
    if unique_ports_attempted >= 50 or window_count >= 6 or total_attempts >= 500:
        return "CRITICAL"
    if unique_ports_attempted >= 25 or window_count >= 4 or total_attempts >= 200:
        return "HIGH"
    if unique_ports_attempted >= 10 or window_count >= 2 or total_attempts >= 50:
        return "MEDIUM"
    return "LOW"


