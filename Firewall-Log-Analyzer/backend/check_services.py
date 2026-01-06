#!/usr/bin/env python3
"""
Diagnostic script to check auto-blocking and alert services
"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

print("=" * 60)
print("SERVICE STATUS CHECK")
print("=" * 60)

# Check Auto-Blocking Service
print("\n1. AUTO IP BLOCKING SERVICE")
print("-" * 60)
try:
    from app.services.auto_ip_blocking_service import auto_ip_blocking_service
    print(f"✓ Service initialized")
    print(f"  Enabled: {auto_ip_blocking_service.enabled}")
    if auto_ip_blocking_service.enabled:
        print(f"  Severity thresholds:")
        print(f"    - CRITICAL: {auto_ip_blocking_service.auto_block_critical}")
        print(f"    - HIGH: {auto_ip_blocking_service.auto_block_high}")
        print(f"    - MEDIUM: {auto_ip_blocking_service.auto_block_medium}")
        print(f"    - LOW: {auto_ip_blocking_service.auto_block_low}")
        print(f"  Attack thresholds:")
        print(f"    - Brute Force: {auto_ip_blocking_service.brute_force_attempt_threshold} attempts")
        print(f"    - DDoS: {auto_ip_blocking_service.ddos_request_threshold} requests")
        print(f"    - Port Scan: {auto_ip_blocking_service.port_scan_ports_threshold} ports")
        print(f"  ML thresholds:")
        print(f"    - Risk Score: {auto_ip_blocking_service.ml_risk_score_threshold}")
        print(f"    - Anomaly Score: {auto_ip_blocking_service.ml_anomaly_score_threshold}")
        print(f"    - Confidence: {auto_ip_blocking_service.ml_confidence_threshold}")
        print(f"    - Require ML: {auto_ip_blocking_service.require_ml_confirmation}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Check Alert Monitor Worker
print("\n2. ALERT MONITOR WORKER")
print("-" * 60)
try:
    from app.services.alert_monitor_worker import alert_monitor_worker
    status = alert_monitor_worker.get_status()
    print(f"✓ Worker status:")
    print(f"  Running: {status['running']}")
    print(f"  Check interval: {status['check_interval_seconds']} seconds ({status['check_interval_seconds']/60:.1f} minutes)")
    print(f"  Last check: {status['last_check_time'] or 'Not yet'}")
    print(f"  Processed alerts (this session): {status['processed_alerts_count']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Check Email Service
print("\n3. EMAIL NOTIFICATION SERVICE")
print("-" * 60)
try:
    from app.services.email_service import email_service
    print(f"✓ Email service:")
    print(f"  Enabled: {email_service.enabled}")
    print(f"  Recipients: {len(email_service.recipients)}")
    if email_service.recipients:
        for recipient in email_service.recipients:
            print(f"    - {recipient}")
    else:
        print("    ⚠ No recipients configured")
except Exception as e:
    print(f"✗ Error: {e}")

# Check Environment Variables
print("\n4. ENVIRONMENT VARIABLES")
print("-" * 60)
env_vars = [
    "AUTO_IP_BLOCKING_ENABLED",
    "AUTO_BLOCK_HIGH",
    "AUTO_BLOCK_CRITICAL",
    "AUTO_BLOCK_BRUTE_FORCE_THRESHOLD",
    "EMAIL_ENABLED",
    "SENDGRID_API_KEY",
    "EMAIL_RECIPIENTS",
    "SUDO_PASSWORD"
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        if "PASSWORD" in var or "API_KEY" in var:
            print(f"  {var}: {'SET' if value else 'NOT SET'}")
        else:
            print(f"  {var}: {value}")
    else:
        print(f"  {var}: NOT SET (using default)")

# Check Database Collections
print("\n5. DATABASE STATUS")
print("-" * 60)
try:
    from app.db.mongo import blacklisted_ips_collection, alerts_collection, email_notifications_collection
    from datetime import datetime, timedelta
    
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    
    total_blocks = blacklisted_ips_collection.count_documents({})
    active_blocks = blacklisted_ips_collection.count_documents({"is_active": True})
    auto_blocks = blacklisted_ips_collection.count_documents({"blocked_by": "auto_blocking_service", "is_active": True})
    recent_auto_blocks = blacklisted_ips_collection.count_documents({
        "blocked_by": "auto_blocking_service",
        "blocked_at": {"$gte": recent_cutoff}
    })
    
    total_alerts = alerts_collection.count_documents({})
    recent_alerts = alerts_collection.count_documents({"computed_at": {"$gte": recent_cutoff}})
    
    recent_emails = email_notifications_collection.count_documents({
        "email_sent_at": {"$gte": recent_cutoff}
    })
    
    print(f"  Blocked IPs:")
    print(f"    - Total: {total_blocks}")
    print(f"    - Active: {active_blocks}")
    print(f"    - Auto-blocked (active): {auto_blocks}")
    print(f"    - Auto-blocked (last 24h): {recent_auto_blocks}")
    print(f"  Alerts:")
    print(f"    - Total: {total_alerts}")
    print(f"    - Last 24h: {recent_alerts}")
    print(f"  Email notifications:")
    print(f"    - Last 24h: {recent_emails}")
    
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("✓ All services checked. Review the output above for any issues.")
print("\nTo test:")
print("  1. Check auto-blocking: GET /health/auto-blocking")
print("  2. Check alerts: GET /health/notifications")
print("  3. Test email: POST /test/email")

