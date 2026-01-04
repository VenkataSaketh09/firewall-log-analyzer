# Alert Notification Debugging Guide

## Current Configuration (from .env)

✅ **Email Service: ENABLED**
- SendGrid API Key: Configured
- From Address: mvsaketh2005@gmail.com
- Recipients: mvsaketh2020@gmail.com

✅ **Notification Thresholds:**
- Severity Threshold: LOW (will send for all severities)
- ML Risk Threshold: 40 (low threshold, should trigger easily)
- Rate Limit: 15 minutes

## How the Alert Notification System Works

### Process Flow:

1. **Log Ingestion** (Continuous)
   - Logs are ingested from `/var/log/*` files
   - Stored in MongoDB `firewall_logs` collection

2. **Alert Computation** (Every 5 minutes)
   - `alert_service.py` computes alerts from logs
   - Detects: Brute Force, DDoS, Port Scans
   - Stores alerts in MongoDB `alerts` collection

3. **Alert Monitoring** (Every 2 minutes)
   - `alert_monitor_worker.py` checks for new alerts
   - Compares with previously processed alerts
   - Filters out already-notified alerts

4. **ML Scoring** (For each new alert)
   - Runs ML scoring on the alert
   - Gets risk score, anomaly score, confidence

5. **Notification Decision**
   - Checks severity threshold (LOW = all alerts pass)
   - Checks ML risk threshold (40 = low threshold)
   - Checks rate limiting (15 min per IP/type)
   - Checks deduplication (prevents duplicates)

6. **Email Sending**
   - Sends email via SendGrid
   - Records notification in `email_notifications` collection

## Why You Might Not Be Getting Alerts

### Possible Reasons:

1. **No Alerts Being Generated**
   - No logs in database
   - No threats detected (no brute force, DDoS, port scans)
   - Alert thresholds too high

2. **Alerts Already Processed**
   - Alerts were detected and notifications sent previously
   - Deduplication preventing re-sending

3. **Email Service Issues**
   - SendGrid API key invalid
   - Email address not verified in SendGrid
   - Network/firewall blocking SendGrid

4. **Worker Not Running**
   - Alert monitor worker not started
   - Worker crashed/stopped

## Debugging Steps

### Step 1: Check if Alerts Exist

```bash
# Check health endpoint
curl http://localhost:8000/health/notifications
```

This will show:
- Email service status
- Recent alerts count (last 24h)
- Recent notifications count (last 24h)
- Worker status

### Step 2: Check Server Logs

Look for these log messages:
- `✓ Alert monitor worker started`
- `Alert check: Found X total alert(s)`
- `Processing X new alert(s)`
- `✓ Notification sent successfully`

### Step 3: Test Email Directly

```bash
# Test email sending (bypasses alert detection)
curl -X POST http://localhost:8000/test/email
```

This will send a test email to verify SendGrid is working.

### Step 4: Check MongoDB for Alerts

```python
# In Python shell or MongoDB client
from app.db.mongo import alerts_collection
from datetime import datetime, timedelta

# Check recent alerts
recent = alerts_collection.find({
    "computed_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
})
print(f"Recent alerts: {list(recent)}")
```

### Step 5: Check if Logs Exist

```python
from app.db.mongo import logs_collection
from datetime import datetime, timedelta

# Check recent logs
recent_logs = logs_collection.count_documents({
    "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)}
})
print(f"Recent logs (24h): {recent_logs}")
```

## Common Issues & Solutions

### Issue 1: "No alerts found in current time window"

**Cause:** No threats detected or no logs in database

**Solution:**
- Verify logs are being ingested: Check `/var/log/*` files exist
- Check if logs are in MongoDB
- Trigger a test attack (e.g., multiple failed SSH logins)

### Issue 2: "No new alerts to process"

**Cause:** All alerts were already processed/notified

**Solution:**
- This is normal if alerts were already sent
- To test again, you can:
  - Wait for new alerts to be generated
  - Clear `email_notifications` collection (for testing only)
  - Lower alert detection thresholds

### Issue 3: "Notification not sent: ML risk score below threshold"

**Cause:** ML scored the alert as low risk

**Solution:**
- Lower `NOTIFICATION_ML_RISK_THRESHOLD` in .env (currently 40)
- Or set severity threshold to CRITICAL only

### Issue 4: "Failed to send email"

**Cause:** SendGrid API issue

**Solution:**
- Verify SendGrid API key is correct
- Check SendGrid dashboard for errors
- Verify sender email is verified
- Test with `/test/email` endpoint

## Testing the System

### Test 1: Verify Email Service
```bash
curl -X POST http://localhost:8000/test/email
```
Should return `{"success": true}` and you should receive an email.

### Test 2: Trigger a Test Alert
1. Generate multiple failed SSH login attempts:
   ```bash
   # On the VM, try to SSH with wrong password multiple times
   ssh wronguser@localhost
   # (enter wrong password 5+ times)
   ```

2. Wait 5-10 minutes for:
   - Alert to be computed
   - Alert monitor to detect it
   - Email to be sent

### Test 3: Check System Status
```bash
curl http://localhost:8000/health/notifications
```

Look for:
- `email_service.enabled: true`
- `alert_monitor_worker.running: true`
- `recent_alerts_24h: > 0` (if alerts exist)

## Manual Alert Trigger (For Testing)

If you want to force an alert notification for testing:

1. **Option 1: Lower thresholds temporarily**
   - Set `NOTIFICATION_SEVERITY_THRESHOLD=LOW`
   - Set `NOTIFICATION_ML_RISK_THRESHOLD=0`
   - Restart server

2. **Option 2: Create test alert in database**
   ```python
   from app.db.mongo import alerts_collection
   from datetime import datetime
   
   test_alert = {
       "bucket_end": datetime.utcnow(),
       "lookback_seconds": 86400,
       "alert_type": "BRUTE_FORCE",
       "source_ip": "192.168.1.100",
       "severity": "HIGH",
       "first_seen": datetime.utcnow(),
       "last_seen": datetime.utcnow(),
       "count": 10,
       "description": "Test brute force attack",
       "computed_at": datetime.utcnow(),
   }
   alerts_collection.insert_one(test_alert)
   ```

## Next Steps

1. **Check health endpoint**: `GET /health/notifications`
2. **Test email**: `POST /test/email`
3. **Check server logs** for detailed information
4. **Verify logs are being ingested** (check MongoDB)
5. **Trigger a real attack** to test the system

## Log Messages to Look For

**Success:**
- `✓ Alert monitor worker started`
- `Alert check: Found X total alert(s)`
- `Processing X new alert(s)`
- `✓ Notification sent successfully`

**Issues:**
- `No alerts found in current time window` → No threats detected
- `No new alerts to process` → All alerts already processed
- `Notification not sent: [reason]` → Check the reason
- `✗ Failed to send email` → SendGrid issue

