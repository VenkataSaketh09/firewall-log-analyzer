import time
import threading
from app.services.auth_log_parser import parse_auth_log
from app.services.ufw_log_parser import parse_ufw_log
from app.db.mongo import logs_collection

AUTH_LOG = "/var/log/auth.log"
UFW_LOG = "/var/log/ufw.log"

def follow(file_path):
    with open(file_path, "r") as f:
        f.seek(0, 2)  # go to end
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            yield line

def ingest_auth_logs():
    for line in follow(AUTH_LOG):
        log = parse_auth_log(line)
        if log:
            logs_collection.insert_one(log)
            print("AUTH LOG STORED:", log)

def ingest_ufw_logs():
    for line in follow(UFW_LOG):
        log = parse_ufw_log(line)
        if log:
            logs_collection.insert_one(log)
            print("UFW LOG STORED:", log)

def start_log_ingestion():
    auth_thread = threading.Thread(target=ingest_auth_logs, daemon=True)
    ufw_thread = threading.Thread(target=ingest_ufw_logs, daemon=True)

    auth_thread.start()
    ufw_thread.start()

    # keep main thread alive
    while True:
        time.sleep(10)
