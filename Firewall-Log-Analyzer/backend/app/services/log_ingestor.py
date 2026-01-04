import time
import threading
import os
import select
from datetime import datetime
from app.services.auth_log_parser import parse_auth_log
from app.services.ufw_log_parser import parse_ufw_log
from app.services.iptables_parser import parse_iptables_log
from app.services.syslog_parser import parse_syslog
from app.services.sql_parser import parse_sql_log
from app.db.mongo import logs_collection
from app.services.raw_log_broadcaster import raw_log_broadcaster
from app.services.redis_cache import redis_log_cache

# Log file paths for network engineers
AUTH_LOG = "/var/log/auth.log"
UFW_LOG = "/var/log/ufw.log"
KERN_LOG = "/var/log/kern.log"  # iptables/netfilter logs
SYSLOG = "/var/log/syslog"  # General system logs
MESSAGES = "/var/log/messages"  # Alternative syslog location

def follow(file_path):
    """Follow a log file in real-time (tail -f equivalent) with optimized polling"""
    if not os.path.exists(file_path):
        print(f"Warning: Log file {file_path} does not exist. Skipping.")
        return
    
    try:
        with open(file_path, "r", errors='ignore') as f:
            f.seek(0, 2)  # go to end
            # Use select for non-blocking I/O when possible (Unix/Linux)
            use_select = hasattr(select, 'select')
            fd = f.fileno() if use_select else None
            
            # Reduced sleep time for faster response (0.01 seconds = 10ms)
            # This allows checking 100 times per second instead of once per second
            poll_interval = 0.01
            
            while True:
                line = f.readline()
                if line:
                    yield line
                    # If we got a line, check immediately for more (no sleep)
                    # This prevents batching when multiple lines arrive quickly
                    continue
                
                # No new line available
                if use_select and fd is not None:
                    # Use select with a small timeout for efficient polling
                    # This is more efficient than sleep() as it wakes up when data is available
                    ready, _, _ = select.select([fd], [], [], poll_interval)
                    if not ready:
                        # No data available, small sleep to prevent CPU spinning
                        time.sleep(poll_interval)
                else:
                    # Fallback for systems without select (Windows, etc.)
                    time.sleep(poll_interval)
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

def ingest_auth_logs():
    """Ingest authentication logs (SSH, login attempts)"""
    for line in follow(AUTH_LOG):
        # Create log message for caching and broadcasting
        log_message = {
            "type": "raw_log",
            "log_source": "auth",
            "raw_line": line.strip(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache in Redis FIRST (for instant switching)
        redis_log_cache.add_log("auth", log_message)
        
        # Broadcast raw line to WebSocket clients (prioritize real-time delivery)
        raw_log_broadcaster.broadcast("auth", line)
        
        # Existing parsing and storage (non-blocking for WebSocket)
        # Parse and store in background to not delay broadcasting
        try:
            log = parse_auth_log(line)
            if log:
                logs_collection.insert_one(log)
        except Exception as e:
            # Don't let parsing errors block broadcasting
            print(f"Error parsing auth log line: {e}")

def ingest_ufw_logs():
    """Ingest UFW (Uncomplicated Firewall) logs"""
    for line in follow(UFW_LOG):
        # Create log message for caching and broadcasting
        log_message = {
            "type": "raw_log",
            "log_source": "ufw",
            "raw_line": line.strip(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache in Redis FIRST (for instant switching)
        redis_log_cache.add_log("ufw", log_message)
        
        # Broadcast raw line to WebSocket clients (prioritize real-time delivery)
        raw_log_broadcaster.broadcast("ufw", line)
        
        # Existing parsing and storage (non-blocking for WebSocket)
        try:
            log = parse_ufw_log(line)
            if log:
                logs_collection.insert_one(log)
        except Exception as e:
            print(f"Error parsing ufw log line: {e}")

def ingest_kern_logs():
    """Ingest kernel logs (iptables/netfilter firewall logs)"""
    for line in follow(KERN_LOG):
        # Create log message for caching and broadcasting
        log_message = {
            "type": "raw_log",
            "log_source": "kern",
            "raw_line": line.strip(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache in Redis FIRST (for instant switching)
        redis_log_cache.add_log("kern", log_message)
        
        # Broadcast raw line to WebSocket clients (prioritize real-time delivery)
        raw_log_broadcaster.broadcast("kern", line)
        
        # Only process iptables-related kernel logs for parsing
        if "kernel:" in line and ("SRC=" in line or "iptables" in line.lower()):
            try:
                log = parse_iptables_log(line)
                if log:
                    logs_collection.insert_one(log)
            except Exception as e:
                print(f"Error parsing kern log line: {e}")

def ingest_syslog():
    """Ingest general syslog entries (security events, SQL access, etc.)"""
    for line in follow(SYSLOG):
        # Create log message for caching and broadcasting
        log_message = {
            "type": "raw_log",
            "log_source": "syslog",
            "raw_line": line.strip(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache in Redis FIRST (for instant switching)
        redis_log_cache.add_log("syslog", log_message)
        
        # Broadcast raw line to WebSocket clients (prioritize real-time delivery)
        raw_log_broadcaster.broadcast("syslog", line)
        
        # Skip if already processed by auth.log or kern.log for parsing
        if "sshd" in line.lower() or "kernel:" in line:
            continue
        try:
            log = parse_syslog(line)
            if log:
                logs_collection.insert_one(log)
        except Exception as e:
            print(f"Error parsing syslog line: {e}")

def ingest_messages():
    """Ingest /var/log/messages (alternative syslog location)"""
    for line in follow(MESSAGES):
        # Create log message for caching and broadcasting
        log_message = {
            "type": "raw_log",
            "log_source": "messages",
            "raw_line": line.strip(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Cache in Redis FIRST (for instant switching)
        redis_log_cache.add_log("messages", log_message)
        
        # Broadcast raw line to WebSocket clients (prioritize real-time delivery)
        raw_log_broadcaster.broadcast("messages", line)
        
        # Skip if already processed by other log files for parsing
        if "sshd" in line.lower() or "kernel:" in line:
            continue
        try:
            log = parse_syslog(line)
            if log:
                logs_collection.insert_one(log)
        except Exception as e:
            print(f"Error parsing messages log line: {e}")

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
