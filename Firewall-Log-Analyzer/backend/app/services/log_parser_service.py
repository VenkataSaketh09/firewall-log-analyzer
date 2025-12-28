"""
Unified log parsing service that routes logs to appropriate parsers
"""
from typing import Optional, List, Dict
from app.services.auth_log_parser import parse_auth_log
from app.services.ufw_log_parser import parse_ufw_log
from app.services.iptables_parser import parse_iptables_log
from app.services.syslog_parser import parse_syslog
from app.services.sql_parser import parse_sql_log


def parse_log_line(line: str, log_source: Optional[str] = None) -> Optional[Dict]:
    """
    Parse a log line using the appropriate parser based on log source or content.
    
    Args:
        line: Raw log line
        log_source: Optional hint about log source (auth.log, ufw.log, iptables, syslog, sql.log)
    
    Returns:
        Parsed log dict or None if line couldn't be parsed
    """
    if not line or not line.strip():
        return None
    
    # Try source-specific parsers first
    if log_source:
        log_source_lower = log_source.lower()
        
        if "auth" in log_source_lower:
            result = parse_auth_log(line)
            if result:
                return result
        elif "ufw" in log_source_lower:
            result = parse_ufw_log(line)
            if result:
                return result
        elif "iptables" in log_source_lower or "netfilter" in log_source_lower:
            result = parse_iptables_log(line)
            if result:
                return result
        elif "sql" in log_source_lower:
            result = parse_sql_log(line)
            if result:
                return result
        elif "syslog" in log_source_lower:
            result = parse_syslog(line)
            if result:
                return result
    
    # Try content-based detection
    # Check for SQL patterns
    result = parse_sql_log(line)
    if result:
        return result
    
    # Check for auth.log patterns
    if "Failed password" in line or "Accepted password" in line:
        result = parse_auth_log(line)
        if result:
            return result
    
    # Check for UFW patterns
    if "[UFW" in line or "UFW" in line:
        result = parse_ufw_log(line)
        if result:
            return result
    
    # Check for iptables patterns
    if "kernel:" in line and "SRC=" in line:
        result = parse_iptables_log(line)
        if result:
            return result
    
    # Try generic syslog parser as fallback
    result = parse_syslog(line)
    if result:
        return result
    
    return None


def parse_multiple_logs(lines: List[str], log_source: Optional[str] = None) -> List[Dict]:
    """
    Parse multiple log lines.
    
    Args:
        lines: List of raw log lines
        log_source: Optional hint about log source
    
    Returns:
        List of parsed log dicts (skips None results)
    """
    parsed_logs = []
    for line in lines:
        parsed = parse_log_line(line, log_source)
        if parsed:
            parsed_logs.append(parsed)
    return parsed_logs

