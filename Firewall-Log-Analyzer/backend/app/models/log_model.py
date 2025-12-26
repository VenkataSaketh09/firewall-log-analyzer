from datetime import datetime
from typing import Optional

def build_log(
    timestamp: datetime,
    source_ip: str,
    destination_port: Optional[int],
    protocol: Optional[str],
    log_source: str,
    event_type: str,
    severity: str,
    username: Optional[str],
    raw_log: str
):
    return {
        "timestamp": timestamp,
        "source_ip": source_ip,
        "destination_port": destination_port,
        "protocol": protocol,
        "log_source": log_source,
        "event_type": event_type,
        "severity": severity,
        "username": username,
        "raw_log": raw_log
    }
