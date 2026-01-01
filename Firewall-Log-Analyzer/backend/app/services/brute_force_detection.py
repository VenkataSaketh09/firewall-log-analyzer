from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from pymongo import DESCENDING
from app.db.mongo import logs_collection


def detect_brute_force(
    time_window_minutes: int = 15,
    threshold: int = 5,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None
) -> List[Dict]:
    """
    Detect brute force attacks based on failed login attempts.
    
    Args:
        time_window_minutes: Time window in minutes to check for failed attempts (default: 15)
        threshold: Number of failed attempts to trigger detection (default: 5)
        start_date: Optional start date to analyze (default: last 24 hours)
        end_date: Optional end date to analyze (default: now)
        source_ip: Optional specific IP to check (if None, checks all IPs)
    
    Returns:
        List of dictionaries containing brute force attack information
    """
    # Set default time range to last 24 hours if not specified
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(hours=24)
    
    # Build base query for failed login attempts
    base_query = {
        "event_type": "SSH_FAILED_LOGIN",
        "timestamp": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    if source_ip:
        base_query["source_ip"] = source_ip
    
    # Get all failed login attempts in the time range
    failed_logins = logs_collection.find(
        base_query,
        {"source_ip": 1, "timestamp": 1, "username": 1, "raw_log": 1, "log_source": 1, "event_type": 1, "_id": 1}
    ).sort("timestamp", DESCENDING)
    
    # Group attempts by IP and check for brute force patterns
    ip_attempts: Dict[str, List[Dict]] = {}
    brute_force_detections: List[Dict] = []
    
    for attempt in failed_logins:
        ip = attempt["source_ip"]
        
        if ip not in ip_attempts:
            ip_attempts[ip] = []
        
        ip_attempts[ip].append({
            "timestamp": attempt["timestamp"],
            "username": attempt.get("username"),
            "log_id": str(attempt["_id"]),
            "raw_log": attempt.get("raw_log", ""),
            "log_source": attempt.get("log_source", "auth.log"),
            "event_type": attempt.get("event_type", "SSH_FAILED_LOGIN"),
        })
    
    # Analyze each IP for brute force patterns
    for ip, attempts in ip_attempts.items():
        # Sort attempts by timestamp
        attempts.sort(key=lambda x: x["timestamp"])
        
        # Group attempts into time windows
        attack_windows = []
        i = 0
        
        while i < len(attempts):
            window_start = attempts[i]["timestamp"]
            window_end = window_start + timedelta(minutes=time_window_minutes)
            window_attempts = []
            
            # Collect all attempts within the time window starting from current attempt
            j = i
            while j < len(attempts) and attempts[j]["timestamp"] <= window_end:
                window_attempts.append(attempts[j])
                j += 1
            
            # If this window exceeds threshold, add it
            if len(window_attempts) >= threshold:
                attack_windows.append({
                    "window_start": window_start,
                    "window_end": window_attempts[-1]["timestamp"],
                    "attempts": window_attempts,
                    "attempt_count": len(window_attempts)
                })
                # Skip to after this window to avoid overlapping windows
                i = j
            else:
                # Move to next attempt
                i += 1
        
        # If brute force detected, add to results
        if attack_windows:
            # Calculate total attempts and unique usernames
            total_attempts = len(attempts)
            unique_usernames = set(a["username"] for a in attempts if a.get("username"))
            
            # Get first and last attempt times
            first_attempt = attempts[0]["timestamp"]
            last_attempt = attempts[-1]["timestamp"]
            
            brute_force_detections.append({
                "source_ip": ip,
                "total_attempts": total_attempts,
                "unique_usernames_attempted": len(unique_usernames),
                "usernames_attempted": list(unique_usernames) if unique_usernames else [],
                "first_attempt": first_attempt,
                "last_attempt": last_attempt,
                "attack_windows": attack_windows,
                "severity": _calculate_severity(total_attempts, len(attack_windows)),
                # Representative log line for ML scoring / debugging
                "sample_raw_log": attempts[-1].get("raw_log", "") if attempts else "",
                "sample_log_source": attempts[-1].get("log_source", "auth.log") if attempts else "auth.log",
                "sample_event_type": attempts[-1].get("event_type", "SSH_FAILED_LOGIN") if attempts else "SSH_FAILED_LOGIN",
            })
    
    # Sort by total attempts (most severe first)
    brute_force_detections.sort(key=lambda x: x["total_attempts"], reverse=True)
    
    return brute_force_detections


def _calculate_severity(total_attempts: int, window_count: int) -> str:
    """Calculate severity based on attempt count and window count"""
    if total_attempts >= 50 or window_count >= 5:
        return "CRITICAL"
    elif total_attempts >= 20 or window_count >= 3:
        return "HIGH"
    elif total_attempts >= 10:
        return "MEDIUM"
    else:
        return "LOW"


def get_brute_force_timeline(ip: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
    """
    Get detailed timeline of brute force attempts for a specific IP.
    
    Args:
        ip: Source IP address
        start_date: Optional start date
        end_date: Optional end date
    
    Returns:
        Dictionary with timeline information
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(hours=24)
    
    query = {
        "source_ip": ip,
        "event_type": "SSH_FAILED_LOGIN",
        "timestamp": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    attempts = list(logs_collection.find(
        query,
        {"timestamp": 1, "username": 1, "_id": 1}
    ).sort("timestamp", DESCENDING))
    
    timeline = []
    for attempt in attempts:
        timeline.append({
            "timestamp": attempt["timestamp"],
            "username": attempt.get("username"),
            "log_id": str(attempt["_id"])
        })
    
    return {
        "source_ip": ip,
        "total_attempts": len(timeline),
        "timeline": timeline,
        "time_range": {
            "start": start_date,
            "end": end_date
        }
    }

