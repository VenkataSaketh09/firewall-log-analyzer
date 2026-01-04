import time
import threading
import os
from app.services.auth_log_parser import parse_auth_log
from app.services.ufw_log_parser import parse_ufw_log
from app.services.iptables_parser import parse_iptables_log
from app.services.syslog_parser import parse_syslog
from app.services.sql_parser import parse_sql_log
from app.db.mongo import logs_collection
from app.services.raw_log_broadcaster import raw_log_broadcaster

# Log file paths for network engineers
AUTH_LOG = "/var/log/auth.log"
UFW_LOG = "/var/log/ufw.log"
KERN_LOG = "/var/log/kern.log"  # iptables/netfilter logs
SYSLOG = "/var/log/syslog"  # General system logs
MESSAGES = "/var/log/messages"  # Alternative syslog location

def follow(file_path):
    """Follow a log file in real-time (tail -f equivalent)"""
    if not os.path.exists(file_path):
        print(f"Warning: Log file {file_path} does not exist. Skipping.")
        return
    
    try:
        with open(file_path, "r", errors='ignore') as f:
            f.seek(0, 2)  # go to end
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                yield line
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

def ingest_auth_logs():
    """Ingest authentication logs (SSH, login attempts)"""
    for line in follow(AUTH_LOG):
        # Broadcast raw line to WebSocket clients
        raw_log_broadcaster.broadcast("auth", line)
        
        # Existing parsing and storage
        log = parse_auth_log(line)
        if log:
            logs_collection.insert_one(log)

def ingest_ufw_logs():
    """Ingest UFW (Uncomplicated Firewall) logs"""
    for line in follow(UFW_LOG):
        # Broadcast raw line to WebSocket clients
        raw_log_broadcaster.broadcast("ufw", line)
        
        # Existing parsing and storage
        log = parse_ufw_log(line)
        if log:
            logs_collection.insert_one(log)

def ingest_kern_logs():
    """Ingest kernel logs (iptables/netfilter firewall logs)"""
    for line in follow(KERN_LOG):
        # Broadcast raw line to WebSocket clients (all kern logs, not just iptables)
        raw_log_broadcaster.broadcast("kern", line)
        
        # Only process iptables-related kernel logs for parsing
        if "kernel:" in line and ("SRC=" in line or "iptables" in line.lower()):
            log = parse_iptables_log(line)
            if log:
                logs_collection.insert_one(log)

def ingest_syslog():
    """Ingest general syslog entries (security events, SQL access, etc.)"""
    for line in follow(SYSLOG):
        # Broadcast raw line to WebSocket clients (all syslog, not filtered)
        raw_log_broadcaster.broadcast("syslog", line)
        
        # Skip if already processed by auth.log or kern.log for parsing
        if "sshd" in line.lower() or "kernel:" in line:
            continue
        log = parse_syslog(line)
        if log:
            logs_collection.insert_one(log)

def ingest_messages():
    """Ingest /var/log/messages (alternative syslog location)"""
    for line in follow(MESSAGES):
        # Broadcast raw line to WebSocket clients (all messages, not filtered)
        raw_log_broadcaster.broadcast("messages", line)
        
        # Skip if already processed by other log files for parsing
        if "sshd" in line.lower() or "kernel:" in line:
            continue
        log = parse_syslog(line)
        if log:
            logs_collection.insert_one(log)

def start_log_ingestion():
    """
    Start real-time log ingestion from local VM log files.
    Monitors multiple log sources useful for network engineers:
    - auth.log: SSH and authentication events
    - ufw.log: UFW firewall logs
    - kern.log: iptables/netfilter firewall logs
    - syslog: General system and security events
    - messages: Alternative syslog location
    """
    threads = []
    
    # Start thread for each log source
    log_sources = [
        ("auth", ingest_auth_logs),
        ("ufw", ingest_ufw_logs),
        ("kern", ingest_kern_logs),
        ("syslog", ingest_syslog),
        ("messages", ingest_messages),
    ]
    
    for name, func in log_sources:
        thread = threading.Thread(target=func, daemon=True, name=f"log-ingestor-{name}")
        thread.start()
        threads.append(thread)
        print(f"✓ Started log ingestion for {name}")
    
    # Keep main thread alive
    while True:
        time.sleep(10)
