"""
Dedicated SQL attack detection and parsing
"""
import re
from datetime import datetime
from typing import Optional
from app.models.log_model import build_log
from app.services.timestamp_parser import extract_timestamp

# SQL-related patterns
SQL_CONNECTION_PATTERN = re.compile(
    r'(?i)(?:mysql|postgres|mssql|sql server).*?(?:connection|login|auth).*?from\s+(?P<ip>[\d.]+)',
    re.IGNORECASE
)
SQL_FAILED_PATTERN = re.compile(
    r'(?i)(?:failed|denied|error|unauthorized).*?(?:login|connection|authentication).*?(?:mysql|postgres|mssql|sql)',
    re.IGNORECASE
)
SQL_INJECTION_PATTERN = re.compile(
    r'(?i)(?:union|select|insert|delete|update|drop|exec|execute).*?(?:--|;|/\*|\*/)',
    re.IGNORECASE
)
SQL_PORT_PATTERN = re.compile(r'(?:1433|3306|5432|1521)')  # MSSQL, MySQL, PostgreSQL, Oracle


def parse_sql_log(line: str) -> Optional[dict]:
    """
    Parse SQL-related log entries.
    
    Detects:
    - SQL connection attempts
    - SQL authentication failures
    - SQL injection attempts
    - SQL port access
    """
    if not line.strip():
        return None
    
    timestamp = extract_timestamp(line, "syslog")
    
    # Extract IP address
    ip_match = re.search(r'\b(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\b', line)
    if not ip_match:
        return None
    
    source_ip = ip_match.group("ip")
    
    # Extract port
    port_match = re.search(r':(?P<port>\d{1,5})\b|port\s+(?P<port2>\d{1,5})', line)
    destination_port = None
    if port_match:
        destination_port = int(port_match.group("port") or port_match.group("port2"))
    else:
        # Try to infer from SQL type
        if "1433" in line or "mssql" in line.lower() or "sql server" in line.lower():
            destination_port = 1433
        elif "3306" in line or "mysql" in line.lower():
            destination_port = 3306
        elif "5432" in line or "postgres" in line.lower():
            destination_port = 5432
        elif "1521" in line or "oracle" in line.lower():
            destination_port = 1521
    
    # Determine event type and severity
    event_type = "SQL_ACCESS_ATTEMPT"
    severity = "HIGH"
    
    # Check for SQL injection
    if SQL_INJECTION_PATTERN.search(line):
        event_type = "SQL_INJECTION_ATTEMPT"
        severity = "CRITICAL"
    # Check for failed authentication
    elif SQL_FAILED_PATTERN.search(line):
        event_type = "SQL_AUTH_FAILED"
        severity = "HIGH"
    # Check for connection attempt
    elif SQL_CONNECTION_PATTERN.search(line):
        event_type = "SQL_CONNECTION_ATTEMPT"
        severity = "MEDIUM"
    # Check for port access
    elif SQL_PORT_PATTERN.search(line):
        event_type = "SQL_PORT_ACCESS"
        severity = "HIGH"
    
    return build_log(
        timestamp=timestamp,
        source_ip=source_ip,
        destination_port=destination_port or 1433,
        protocol="TCP",
        log_source="sql.log",
        event_type=event_type,
        severity=severity,
        username=None,
        raw_log=line.strip()
    )

