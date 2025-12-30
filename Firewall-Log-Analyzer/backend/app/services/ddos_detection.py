from datetime import datetime, timedelta
from typing import Optional, List, Dict
from collections import defaultdict
from pymongo import DESCENDING
from app.db.mongo import logs_collection


def detect_ddos(
    time_window_seconds: int = 60,
    single_ip_threshold: int = 100,  # requests per time window for single IP
    distributed_ip_count: int = 10,  # minimum unique IPs for distributed detection
    distributed_request_threshold: int = 500,  # total requests from distributed IPs
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    destination_port: Optional[int] = None,
    protocol: Optional[str] = None
) -> List[Dict]:
    """
    Detect DDoS/Flood attacks using rate-based and distributed pattern recognition.
    
    Detects:
    1. Single IP floods - High request rate from a single source IP
    2. Distributed floods - Multiple IPs targeting same destination/port simultaneously
    
    Args:
        time_window_seconds: Time window in seconds for rate calculation (default: 60)
        single_ip_threshold: Minimum requests per window to flag single IP flood (default: 100)
        distributed_ip_count: Minimum unique IPs to consider distributed attack (default: 10)
        distributed_request_threshold: Total requests threshold for distributed attack (default: 500)
        start_date: Optional start date to analyze (default: last hour)
        end_date: Optional end date to analyze (default: now)
        destination_port: Optional destination port to filter by
        protocol: Optional protocol to filter by (TCP, UDP, etc.)
    
    Returns:
        List of dictionaries containing DDoS/flood attack information
    """
    # Set default time range to last hour if not specified
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(hours=1)
    
    # Build base query
    base_query = {
        "timestamp": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    if destination_port:
        base_query["destination_port"] = destination_port
    if protocol:
        base_query["protocol"] = protocol
    
    # Get all logs in the time range
    logs = list(logs_collection.find(
        base_query,
        {
            "source_ip": 1,
            "timestamp": 1,
            "destination_port": 1,
            "protocol": 1,
            "event_type": 1,
            "log_source": 1,
            "raw_log": 1,
            "_id": 1
        }
    ).sort("timestamp", DESCENDING))
    
    if not logs:
        return []
    
    detections = []
    
    # 1. Detect single IP floods
    single_ip_detections = _detect_single_ip_floods(
        logs, time_window_seconds, single_ip_threshold
    )
    detections.extend(single_ip_detections)
    
    # 2. Detect distributed attacks
    distributed_detections = _detect_distributed_floods(
        logs, time_window_seconds, distributed_ip_count, distributed_request_threshold
    )
    detections.extend(distributed_detections)
    
    # Sort by severity and request rate (most severe first)
    detections.sort(key=lambda x: (
        {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x["severity"], 4),
        -x["peak_request_rate"]
    ))
    
    return detections


def _detect_single_ip_floods(
    logs: List[Dict],
    time_window_seconds: int,
    threshold: int
) -> List[Dict]:
    """
    Detect floods from single IPs using rate-based anomaly detection.
    """
    # Group logs by source IP
    ip_logs: Dict[str, List[Dict]] = defaultdict(list)
    
    for log in logs:
        source_ip = log.get("source_ip")
        if source_ip:
            ip_logs[source_ip].append(log)
    
    detections = []
    
    for source_ip, ip_log_list in ip_logs.items():
        # Sort by timestamp
        ip_log_list.sort(key=lambda x: x["timestamp"])
        
        # Sliding window analysis for rate detection
        attack_windows = []
        i = 0
        
        while i < len(ip_log_list):
            window_start = ip_log_list[i]["timestamp"]
            window_end = window_start + timedelta(seconds=time_window_seconds)
            
            # Count requests in this window
            window_logs = [
                log for log in ip_log_list
                if window_start <= log["timestamp"] <= window_end
            ]
            
            request_count = len(window_logs)
            request_rate = request_count / (time_window_seconds / 60)  # requests per minute
            
            # If exceeds threshold, flag as flood
            if request_count >= threshold:
                # Get destination details
                destinations = defaultdict(int)
                protocols = defaultdict(int)
                ports = defaultdict(int)
                
                for log in window_logs:
                    if log.get("destination_port"):
                        ports[log["destination_port"]] += 1
                    if log.get("protocol"):
                        protocols[log["protocol"]] += 1
                
                attack_windows.append({
                    "window_start": window_start,
                    "window_end": min(window_end, ip_log_list[-1]["timestamp"]),
                    "request_count": request_count,
                    "request_rate_per_min": request_rate,
                    "target_ports": dict(ports),
                    "protocols": dict(protocols)
                })
            
            # Move to next distinct window (non-overlapping)
            # Find first log outside current window
            i += 1
            while i < len(ip_log_list) and ip_log_list[i]["timestamp"] <= window_end:
                i += 1
        
        # If we have attack windows, add detection
        if attack_windows:
            total_requests = len(ip_log_list)
            peak_request_rate = max(win["request_rate_per_min"] for win in attack_windows)
            time_span = (ip_log_list[-1]["timestamp"] - ip_log_list[0]["timestamp"]).total_seconds()
            if time_span > 0:
                avg_request_rate = total_requests / (time_span / 60)
            else:
                avg_request_rate = total_requests  # All requests at same time
            
            # Get unique targets
            all_ports = set()
            all_protocols = set()
            for log in ip_log_list:
                if log.get("destination_port"):
                    all_ports.add(log["destination_port"])
                if log.get("protocol"):
                    all_protocols.add(log["protocol"])
            
            detections.append({
                "attack_type": "SINGLE_IP_FLOOD",
                "source_ips": [source_ip],
                "source_ip_count": 1,
                "total_requests": total_requests,
                "peak_request_rate": peak_request_rate,
                "avg_request_rate": avg_request_rate,
                "target_ports": list(all_ports),
                "target_protocols": list(all_protocols),
                "first_request": ip_log_list[0]["timestamp"],
                "last_request": ip_log_list[-1]["timestamp"],
                "attack_windows": attack_windows,
                "severity": _calculate_severity_single_ip(peak_request_rate, len(attack_windows))
            })
    
    return detections


def _detect_distributed_floods(
    logs: List[Dict],
    time_window_seconds: int,
    min_ip_count: int,
    min_request_threshold: int
) -> List[Dict]:
    """
    Detect distributed DDoS attacks from multiple IPs.
    Groups by destination port/protocol and detects coordinated attacks.
    """
    # Group logs by destination port and protocol
    target_groups: Dict[tuple, List[Dict]] = defaultdict(list)
    
    for log in logs:
        port = log.get("destination_port")
        protocol = log.get("protocol")
        key = (port, protocol)
        target_groups[key].append(log)
    
    detections = []
    
    for (port, protocol), target_logs in target_groups.items():
        if len(target_logs) < min_request_threshold:
            continue
        
        # Sort by timestamp
        target_logs.sort(key=lambda x: x["timestamp"])
        
        # Group source IPs
        ip_logs: Dict[str, List[Dict]] = defaultdict(list)
        for log in target_logs:
            source_ip = log.get("source_ip")
            if source_ip:
                ip_logs[source_ip].append(log)
        
        unique_ips = len(ip_logs)
        
        # Check if this qualifies as distributed attack
        if unique_ips >= min_ip_count:
            # Sliding window analysis
            attack_windows = []
            i = 0
            
            while i < len(target_logs):
                window_start = target_logs[i]["timestamp"]
                window_end = window_start + timedelta(seconds=time_window_seconds)
                
                # Get logs in window
                window_logs = [
                    log for log in target_logs
                    if window_start <= log["timestamp"] <= window_end
                ]
                
                if len(window_logs) >= min_request_threshold:
                    # Count unique IPs in this window
                    window_ips = set(log.get("source_ip") for log in window_logs if log.get("source_ip"))
                    
                    if len(window_ips) >= min_ip_count:
                        request_rate = len(window_logs) / (time_window_seconds / 60)
                        
                        # Calculate IP distribution stats
                        ip_request_counts = defaultdict(int)
                        for log in window_logs:
                            ip = log.get("source_ip")
                            if ip:
                                ip_request_counts[ip] += 1
                        
                        attack_windows.append({
                            "window_start": window_start,
                            "window_end": min(window_end, target_logs[-1]["timestamp"]),
                            "request_count": len(window_logs),
                            "unique_ip_count": len(window_ips),
                            "request_rate_per_min": request_rate,
                            "top_attacking_ips": dict(sorted(
                                ip_request_counts.items(),
                                key=lambda x: x[1],
                                reverse=True
                            )[:10])  # Top 10 attacking IPs
                        })
                
                # Move to next window
                i += 1
                while i < len(target_logs) and target_logs[i]["timestamp"] <= window_end:
                    i += 1
        
        # If we have attack windows, add detection
        if attack_windows:
            total_requests = len(target_logs)
            peak_request_rate = max(win["request_rate_per_min"] for win in attack_windows)
            peak_unique_ips = max(win["unique_ip_count"] for win in attack_windows)
            
            # Calculate average request rate
            time_span = (target_logs[-1]["timestamp"] - target_logs[0]["timestamp"]).total_seconds()
            if time_span > 0:
                avg_request_rate = total_requests / (time_span / 60)
            else:
                avg_request_rate = total_requests
            
            # Get top attacking IPs overall
            all_ip_counts = defaultdict(int)
            for log in target_logs:
                ip = log.get("source_ip")
                if ip:
                    all_ip_counts[ip] += 1
            
            top_ips = sorted(
                all_ip_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]  # Top 20 attacking IPs
            
            detections.append({
                "attack_type": "DISTRIBUTED_FLOOD",
                "source_ips": [ip for ip, _ in top_ips],
                "source_ip_count": unique_ips,
                "total_requests": total_requests,
                "peak_request_rate": peak_request_rate,
                "avg_request_rate": avg_request_rate,
                "peak_unique_ips": peak_unique_ips,
                "target_port": port,
                "target_protocol": protocol,
                "first_request": target_logs[0]["timestamp"],
                "last_request": target_logs[-1]["timestamp"],
                "attack_windows": attack_windows,
                "top_attacking_ips": {ip: count for ip, count in top_ips},
                "severity": _calculate_severity_distributed(peak_request_rate, unique_ips, len(attack_windows))
            })
    
    return detections


def _calculate_severity_single_ip(peak_rate: float, window_count: int) -> str:
    """Calculate severity for single IP flood"""
    if peak_rate >= 1000 or window_count >= 10:
        return "CRITICAL"
    elif peak_rate >= 500 or window_count >= 5:
        return "HIGH"
    elif peak_rate >= 200 or window_count >= 3:
        return "MEDIUM"
    else:
        return "LOW"


def _calculate_severity_distributed(peak_rate: float, unique_ips: int, window_count: int) -> str:
    """Calculate severity for distributed flood"""
    if peak_rate >= 2000 or unique_ips >= 50 or window_count >= 10:
        return "CRITICAL"
    elif peak_rate >= 1000 or unique_ips >= 25 or window_count >= 5:
        return "HIGH"
    elif peak_rate >= 500 or unique_ips >= 15 or window_count >= 3:
        return "MEDIUM"
    else:
        return "LOW"

