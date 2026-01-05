#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta, timezone

API_KEY = "WRx7nN_Nfj18W6B56XAkbejUDWQ9ChcNJIh65JM5VRs"
BASE_URL = "http://localhost:8000"

def ingest_logs(logs, log_source):
    """Ingest logs into the system"""
    response = requests.post(
        f"{BASE_URL}/api/logs/ingest",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json={
            "logs": logs,
            "log_source": log_source
        }
    )
    return response.json()

def test_brute_force():
    """Generate and test brute force detection"""
    print("=== Testing Brute Force Detection ===")
    
    # Generate 25 failed logins within 15 minutes to get HIGH severity
    # (HIGH requires >= 20 attempts or >= 3 windows)
    now = datetime.now(timezone.utc)
    logs = []
    for i in range(25):
        timestamp = now - timedelta(minutes=14-i)  # Spread over 14 minutes
        log_line = f"{timestamp.strftime('%b %d %H:%M:%S')} hostname sshd[1234{i}]: Failed password for admin from 192.168.1.100 port 54321 ssh2"
        logs.append(log_line)
    
    print(f"1. Ingesting {len(logs)} brute force logs...")
    result = ingest_logs(logs, "auth.log")
    print(f"   Result: {result.get('ingested_count', 0)} ingested, {result.get('failed_count', 0)} failed")
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Test detection
    print("2. Testing brute force detection API...")
    response = requests.get(
        f"{BASE_URL}/api/threats/brute-force",
        params={
            "threshold": 5,
            "time_window_minutes": 15
        }
    )
    data = response.json()
    detections = data.get("detections", [])
    print(f"   Found {len(detections)} brute force detections")
    if detections:
        for det in detections[:3]:
            print(f"   - IP: {det.get('source_ip')}, Attempts: {det.get('total_attempts')}, Severity: {det.get('severity')}")
    else:
        print("   ⚠ No detections found. Check if logs have correct timestamps.")
    
    return len(detections) > 0

def test_ddos():
    """Generate and test DDoS detection"""
    print("\n=== Testing DDoS Detection ===")
    
    # Generate 120 requests from same IP within 60 seconds
    # Use proper UFW log format with timestamp that can be parsed
    now = datetime.now(timezone.utc)
    logs = []
    for i in range(120):
        timestamp = now - timedelta(seconds=59-i)  # Spread over 59 seconds (within 60s window)
        # UFW log format: timestamp hostname kernel: [UFW AUDIT] ...
        log_line = f"{timestamp.strftime('%b %d %H:%M:%S')} hostname kernel: [UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.300 DST=192.168.1.10 PROTO=TCP DPT=80"
        logs.append(log_line)
    
    print(f"1. Ingesting {len(logs)} DDoS logs...")
    # Ingest in batches of 50 (API limit is 1000, but let's be safe)
    for i in range(0, len(logs), 50):
        batch = logs[i:i+50]
        result = ingest_logs(batch, "ufw.log")
        print(f"   Batch {i//50 + 1}: {result.get('ingested_count', 0)} ingested")
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Test detection
    print("2. Testing DDoS detection API...")
    response = requests.get(
        f"{BASE_URL}/api/threats/ddos",
        params={
            "single_ip_threshold": 100,
            "time_window_seconds": 60
        }
    )
    data = response.json()
    detections = data.get("detections", [])
    print(f"   Found {len(detections)} DDoS detections")
    if detections:
        for det in detections[:3]:
            print(f"   - Type: {det.get('attack_type')}, Requests: {det.get('total_requests')}, Severity: {det.get('severity')}")
    else:
        print("   ⚠ No detections found. Check if logs have correct timestamps.")
    
    return len(detections) > 0

if __name__ == "__main__":
    try:
        brute_force_ok = test_brute_force()
        ddos_ok = test_ddos()
        
        print("\n=== Summary ===")
        print(f"Brute Force: {'✓ Working' if brute_force_ok else '✗ Not detected'}")
        print(f"DDoS: {'✓ Working' if ddos_ok else '✗ Not detected'}")
        
        if brute_force_ok and ddos_ok:
            print("\n✓ Both detections working! Check the Threats page.")
        else:
            print("\n⚠ Some detections failed. Check:")
            print("  1. Log timestamps are within detection windows")
            print("  2. Backend is running and accessible")
            print("  3. Database has the logs (check /api/logs endpoint)")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()