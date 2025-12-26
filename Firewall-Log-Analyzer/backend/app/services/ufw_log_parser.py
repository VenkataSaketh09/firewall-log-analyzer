import re
from datetime import datetime
from app.models.log_model import build_log

# Example UFW log line:
# [UFW AUDIT] IN=enp0s8 OUT= SRC=192.168.56.1 DST=192.168.56.101 PROTO=TCP SPT=50520 DPT=22

SRC_REGEX = re.compile(r"SRC=(?P<src>[\d.]+)")
DPT_REGEX = re.compile(r"DPT=(?P<dpt>\d+)")
PROTO_REGEX = re.compile(r"PROTO=(?P<proto>\w+)")

def parse_ufw_log(line: str):
    if "[UFW" not in line:
        return None

    timestamp = datetime.utcnow()

    src_match = SRC_REGEX.search(line)
    dpt_match = DPT_REGEX.search(line)
    proto_match = PROTO_REGEX.search(line)

    if not src_match:
        return None

    source_ip = src_match.group("src")
    destination_port = int(dpt_match.group("dpt")) if dpt_match else None
    protocol = proto_match.group("proto") if proto_match else None

    # Determine severity
    severity = "LOW"
    event_type = "UFW_TRAFFIC"

    if destination_port in [22, 23, 1433, 3306]:
        severity = "HIGH"
        event_type = "SUSPICIOUS_PORT_ACCESS"

    return build_log(
        timestamp=timestamp,
        source_ip=source_ip,
        destination_port=destination_port,
        protocol=protocol,
        log_source="ufw.log",
        event_type=event_type,
        severity=severity,
        username=None,
        raw_log=line.strip()
    )
