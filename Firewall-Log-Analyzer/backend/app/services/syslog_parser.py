"""
Parser for generic syslog format logs
"""
import re
from datetime import datetime
from typing import Optional
from app.models.log_model import build_log
from app.services.timestamp_parser import extract_timestamp

# Example syslog line:
# Jan  1 10:00:00 hostname service[pid]: message

# Common patterns
IP_REGEX = re.compile(r'\b(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\b')
PORT_REGEX = re.compile(r':(?P<port>\d{1,5})\b')
SSH_PATTERNS = [
    re.compile(r'Failed password for (?:invalid user )?(?P<user>\w+) from (?P<ip>[\d.]+)'),
    re.compile(r'Accepted password for (?P<user>\w+) from (?P<ip>[\d.]+)'),
    re.compile(r'Invalid user (?P<user>\w+) from (?P<ip>[\d.]+)'),
]
SQL_PATTERNS = [
    re.compile(r'(?i)(?:mysql|postgres|mssql|sql).*?(?:connection|login|auth).*?(?:failed|denied|error)', re.IGNORECASE),
    re.compile(r'(?i)port\s+(?:1433|3306|5432)', re.IGNORECASE),
]


def parse_syslog(line: str) -> Optional[dict]:
    """
    Parse generic syslog line.
    
    Attempts to identify SSH, SQL, and other security-relevant events.
    """
    if not line.strip():
        return None
    
    # Extract timestamp
    timestamp = extract_timestamp(line, "syslog")
    
    # Try to match SSH patterns first
    for pattern in SSH_PATTERNS:
        match = pattern.search(line)
        if match:
            source_ip = match.group("ip")
            username = match.group("user") if "user" in match.groups() else None
            
            if "Failed password" in line or "Invalid user" in line:
                return build_log(
                    timestamp=timestamp,
                    source_ip=source_ip,
                    destination_port=22,
                    protocol="TCP",
                    log_source="syslog",
                    event_type="SSH_FAILED_LOGIN",
                    severity="HIGH",
                    username=username,
                    raw_log=line.strip()
                )
            elif "Accepted password" in line:
                return build_log(
                    timestamp=timestamp,
                    source_ip=source_ip,
                    destination_port=22,
                    protocol="TCP",
                    log_source="syslog",
                    event_type="SSH_LOGIN_SUCCESS",
                    severity="LOW",
                    username=username,
                    raw_log=line.strip()
                )
    
    # Try to match SQL patterns
    for pattern in SQL_PATTERNS:
        if pattern.search(line):
            # Extract IP and port
            ip_match = IP_REGEX.search(line)
            port_match = PORT_REGEX.search(line)
            
            source_ip = ip_match.group("ip") if ip_match else None
            destination_port = int(port_match.group("port")) if port_match else None
            
            if not source_ip:
                # Try to extract from common SQL log formats
                continue
            
            # Determine SQL port if not found
            if not destination_port:
                if "1433" in line or "mssql" in line.lower():
                    destination_port = 1433
                elif "3306" in line or "mysql" in line.lower():
                    destination_port = 3306
                elif "5432" in line or "postgres" in line.lower():
                    destination_port = 5432
            
            event_type = "SQL_ACCESS_ATTEMPT"
            severity = "HIGH"
            
            if "failed" in line.lower() or "denied" in line.lower() or "error" in line.lower():
                event_type = "SQL_AUTH_FAILED"
                severity = "HIGH"
            
            return build_log(
                timestamp=timestamp,
                source_ip=source_ip,
                destination_port=destination_port or 1433,
                protocol="TCP",
                log_source="syslog",
                event_type=event_type,
                severity=severity,
                username=None,
                raw_log=line.strip()
            )
    
    # Generic syslog entry - extract IP if present
    ip_match = IP_REGEX.search(line)
    if ip_match:
        source_ip = ip_match.group("ip")
        port_match = PORT_REGEX.search(line)
        destination_port = int(port_match.group("port")) if port_match else None
        
        # Check for security-relevant keywords
        severity = "LOW"
        event_type = "SYSLOG_ENTRY"
        
        security_keywords = ["denied", "blocked", "rejected", "failed", "error", "attack", "intrusion"]
        if any(keyword in line.lower() for keyword in security_keywords):
            severity = "MEDIUM"
            event_type = "SYSLOG_SECURITY_EVENT"
        
        return build_log(
            timestamp=timestamp,
            source_ip=source_ip,
            destination_port=destination_port,
            protocol=None,
            log_source="syslog",
            event_type=event_type,
            severity=severity,
            username=None,
            raw_log=line.strip()
        )
    
    return None

