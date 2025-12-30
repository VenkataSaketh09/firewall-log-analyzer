"""
Parser for iptables/netfilter logs
"""
import re
from datetime import datetime
from typing import Optional
from app.models.log_model import build_log
from app.services.timestamp_parser import extract_timestamp

# Example iptables log line:
# Jan  1 10:00:00 hostname kernel: [12345.123] IN=eth0 OUT= MAC=... SRC=192.168.1.1 DST=192.168.1.100 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP SPT=12345 DPT=22 SYN URGP=0

SRC_REGEX = re.compile(r"SRC=(?P<src>[\d.]+)")
DST_REGEX = re.compile(r"DST=(?P<dst>[\d.]+)")
DPT_REGEX = re.compile(r"DPT=(?P<dpt>\d+)")
SPT_REGEX = re.compile(r"SPT=(?P<spt>\d+)")
PROTO_REGEX = re.compile(r"PROTO=(?P<proto>\w+)")
IN_REGEX = re.compile(r"IN=(?P<in>\w+)")
OUT_REGEX = re.compile(r"OUT=(?P<out>\w+)")
FLAGS_REGEX = re.compile(r"(SYN|ACK|FIN|RST|PSH|URG)")


def parse_iptables_log(line: str) -> Optional[dict]:
    """
    Parse iptables/netfilter log line.
    
    Returns log dict or None if line doesn't match iptables format.
    """
    # Check if it's an iptables log
    if "kernel:" not in line or "SRC=" not in line:
        return None
    
    # Extract timestamp
    timestamp = extract_timestamp(line, "iptables")
    
    # Extract source IP
    src_match = SRC_REGEX.search(line)
    if not src_match:
        return None
    
    source_ip = src_match.group("src")
    
    # Extract destination IP (optional)
    dst_match = DST_REGEX.search(line)
    destination_ip = dst_match.group("dst") if dst_match else None
    
    # Extract destination port
    dpt_match = DPT_REGEX.search(line)
    destination_port = int(dpt_match.group("dpt")) if dpt_match else None
    
    # Extract source port (optional)
    spt_match = SPT_REGEX.search(line)
    source_port = int(spt_match.group("spt")) if spt_match else None
    
    # Extract protocol
    proto_match = PROTO_REGEX.search(line)
    protocol = proto_match.group("proto") if proto_match else None
    
    # Extract interface
    in_match = IN_REGEX.search(line)
    interface_in = in_match.group("in") if in_match else None
    
    # Extract flags
    flags = FLAGS_REGEX.findall(line)
    
    # Determine event type and severity
    severity = "LOW"
    event_type = "IPTABLES_TRAFFIC"
    
    # Check for suspicious ports
    if destination_port in [22, 23, 1433, 3306, 3389, 5432]:
        severity = "HIGH"
        event_type = "SUSPICIOUS_PORT_ACCESS"
    
    # Check for SQL ports specifically
    if destination_port in [1433, 3306, 5432]:
        event_type = "SQL_ACCESS_ATTEMPT"
        severity = "HIGH"
    
    # Check for connection attempts (SYN without ACK)
    if "SYN" in flags and "ACK" not in flags:
        if event_type == "IPTABLES_TRAFFIC":
            event_type = "CONNECTION_ATTEMPT"
        severity = max(severity, "MEDIUM")
    
    # Check for rejected/dropped packets (if log contains DROP/REJECT)
    if "DROP" in line or "REJECT" in line:
        event_type = "IPTABLES_BLOCKED"
        severity = "MEDIUM"
    
    return build_log(
        timestamp=timestamp,
        source_ip=source_ip,
        destination_ip=destination_ip,
        source_port=source_port,
        destination_port=destination_port,
        protocol=protocol,
        log_source="iptables",
        event_type=event_type,
        severity=severity,
        username=None,
        raw_log=line.strip()
    )

