"""
Timestamp parsing utilities for various log formats
"""
import re
from datetime import datetime, timezone
from typing import Optional


def parse_syslog_timestamp(log_line: str) -> Optional[datetime]:
    """
    Parse timestamp from syslog format.
    Examples:
    - Jan  1 10:00:00
    - Jan 15 10:00:00
    - 2024-01-01T10:00:00
    """
    # Try ISO format first
    iso_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', log_line)
    if iso_match:
        try:
            return datetime.fromisoformat(iso_match.group(1))
        except ValueError:
            pass
    
    # Try syslog format: MMM DD HH:MM:SS
    syslog_match = re.search(r'([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})', log_line)
    if syslog_match:
        month_str, day, hour, minute, second = syslog_match.groups()
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        month = month_map.get(month_str, 1)
        year = datetime.now(timezone.utc).year  # Assume current year if not specified
        try:
            return datetime(year, month, int(day), int(hour), int(minute), int(second))
        except ValueError:
            pass
    
    return None


def parse_auth_log_timestamp(log_line: str) -> Optional[datetime]:
    """
    Parse timestamp from auth.log format.
    Example: Jan  1 10:00:00 hostname sshd[12345]: ...
    """
    return parse_syslog_timestamp(log_line)


def parse_ufw_timestamp(log_line: str) -> Optional[datetime]:
    """
    Parse timestamp from UFW log format.
    Example: [UFW AUDIT] Jan  1 10:00:00 ...
    """
    return parse_syslog_timestamp(log_line)


def parse_iptables_timestamp(log_line: str) -> Optional[datetime]:
    """
    Parse timestamp from iptables log format.
    Example: Jan  1 10:00:00 kernel: [12345.123] IN=eth0 OUT= ...
    """
    return parse_syslog_timestamp(log_line)


def extract_timestamp(log_line: str, log_source: str = "unknown") -> datetime:
    """
    Extract timestamp from log line based on log source.
    Falls back to current UTC time if parsing fails.
    """
    timestamp = None
    
    if log_source in ["auth.log", "syslog"]:
        timestamp = parse_syslog_timestamp(log_line)
    elif log_source == "ufw.log":
        timestamp = parse_ufw_timestamp(log_line)
    elif log_source == "iptables":
        timestamp = parse_iptables_timestamp(log_line)
    else:
        # Try generic syslog format
        timestamp = parse_syslog_timestamp(log_line)
    
    # Fallback to current time if parsing failed
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    return timestamp

