import re
from datetime import datetime
from app.models.log_model import build_log
from app.services.timestamp_parser import extract_timestamp

FAILED_REGEX = re.compile(
    r"Failed password for (invalid user )?(?P<user>\w+) from (?P<ip>[\d.]+)"
)

SUCCESS_REGEX = re.compile(
    r"Accepted password for (?P<user>\w+) from (?P<ip>[\d.]+)"
)

def parse_auth_log(line: str):
    timestamp = extract_timestamp(line, "auth.log")

    if "Failed password" in line:
        match = FAILED_REGEX.search(line)
        if match:
            return build_log(
                timestamp=timestamp,
                source_ip=match.group("ip"),
                destination_port=22,
                protocol="TCP",
                log_source="auth.log",
                event_type="SSH_FAILED_LOGIN",
                severity="HIGH",
                username=match.group("user"),
                raw_log=line.strip()
            )

    if "Accepted password" in line:
        match = SUCCESS_REGEX.search(line)
        if match:
            return build_log(
                timestamp=timestamp,
                source_ip=match.group("ip"),
                destination_port=22,
                protocol="TCP",
                log_source="auth.log",
                event_type="SSH_LOGIN_SUCCESS",
                severity="LOW",
                username=match.group("user"),
                raw_log=line.strip()
            )

    return None
