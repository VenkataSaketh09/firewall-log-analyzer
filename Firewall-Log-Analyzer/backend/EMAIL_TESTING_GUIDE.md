# Email Notification & Auto-Blocking Testing Guide

This guide explains how to test both email notification types and verify that auto-blocking works correctly with interface updates.

## Prerequisites

1. **Backend server running**: Make sure your FastAPI backend is running on `http://localhost:8000`
2. **Email configuration**: Ensure email is configured in your `.env` file:
   ```env
   EMAIL_ENABLED=true
   SENDGRID_API_KEY=your_sendgrid_api_key
   EMAIL_FROM_ADDRESS=alerts@yourdomain.com
   EMAIL_RECIPIENTS=your-email@example.com,another-email@example.com
   ```
3. **Auto-blocking enabled**: Ensure auto-blocking is enabled:
   ```env
   AUTO_IP_BLOCKING_ENABLED=true
   ```

## Testing Methods

### Method 1: Automated Test Script (Recommended)

Run the comprehensive test script:

```bash
cd backend
python test_email_notifications.py
```

This script will:
1. ✅ Check system health
2. ✅ Test basic email service
3. ✅ Test alert notification (threat detection emails)
4. ✅ Test auto-blocking with email notification
5. ✅ Verify blocked IP appears in interface

**Unblock a test IP after testing:**
```bash
python test_email_notifications.py --unblock 192.168.200.50
```

### Method 2: Manual API Testing

#### Test 1: Basic Email Service
```bash
curl -X POST http://localhost:8000/test/email
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Test email sent",
  "recipients": ["your-email@example.com"]
}
```

#### Test 2: Alert Notification (Threat Detection)
```bash
curl -X POST http://localhost:8000/test/alert-notification
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Alert notification test completed",
  "result": {
    "sent": true,
    "ml_scored": true,
    "ml_risk_score": 85.0
  }
}
```

**What this tests:**
- Alert notification service processes threats
- Email is sent for detected threats (brute force, DDoS, port scans)
- ML scoring is applied
- Deduplication and rate limiting work

#### Test 3: Auto-Blocking with Email Notification
```bash
curl -X POST http://localhost:8000/test/auto-block
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Auto-blocking test completed",
  "ip_address": "192.168.200.50",
  "is_blocked_verified": true,
  "email_sent": true,
  "block_result": {
    "success": true,
    "message": "IP 192.168.200.50 automatically blocked due to BRUTE_FORCE"
  }
}
```

**What this tests:**
- IP is automatically blocked via UFW
- Email notification is sent when IP is auto-blocked
- IP is stored in database
- Interface can retrieve blocked IPs

#### Test 4: Verify Blocked IP in Interface
```bash
# Check if IP is blocked
curl http://localhost:8000/api/ip-blocking/check/192.168.200.50

# Get list of all blocked IPs
curl http://localhost:8000/api/ip-blocking/list?active_only=true
```

**Expected Response:**
```json
{
  "ip_address": "192.168.200.50",
  "is_blocked": true
}
```

#### Cleanup: Unblock Test IP
```bash
curl -X POST http://localhost:8000/test/auto-block-cleanup/192.168.200.50
```

### Method 3: Using the Web Interface

1. **Check Email Status:**
   - Navigate to: `http://localhost:8000/health/notifications`
   - Verify email service is enabled and recipients are configured

2. **Check Auto-Blocking Status:**
   - Navigate to: `http://localhost:8000/health/auto-blocking`
   - Verify auto-blocking service is enabled

3. **View Blocked IPs:**
   - Navigate to: `http://localhost:8000/api/ip-blocking/list`
   - Or use the frontend interface at the IP Blocking page

## Email Notification Types

### Type 1: Alert Notifications (Threat Detection)

**Triggered by:**
- Brute force attacks detected
- DDoS attacks detected
- Port scanning detected
- Other suspicious activities

**Email Subject:** `[ALERT] HIGH BRUTE_FORCE detected from 192.168.1.100`

**Email Content:**
- Alert type and severity
- Source IP address
- Description of the threat
- ML analysis (risk score, anomaly score, confidence)
- Event count and timestamps
- Link to dashboard

**Service:** `alert_notification_service` → `email_service`

### Type 2: Auto-Blocking Notifications

**Triggered by:**
- IP automatically blocked due to threat detection
- Auto-blocking service determines IP should be blocked

**Email Subject:** `[AUTO-BLOCKED] IP 192.168.1.100 has been automatically blocked - HIGH threat detected`

**Email Content:**
- IP address that was blocked
- Threat type (BRUTE_FORCE, DDOS, PORT_SCAN)
- Blocking reason
- Attack details (attempts, ports, etc.)
- ML analysis scores
- Instructions to unblock if false positive

**Service:** `auto_ip_blocking_service` → `email_service`

## Verifying Interface Updates

### Check Blocked IPs API
```bash
GET /api/ip-blocking/list?active_only=true
```

### Check Specific IP Status
```bash
GET /api/ip-blocking/check/{ip_address}
```

### Frontend Interface
1. Open the Firewall Log Analyzer frontend
2. Navigate to "IP Blocking" page
3. Verify the blocked IP appears in the list
4. Check that the IP shows:
   - Blocked timestamp
   - Reason for blocking
   - Status (Active)
   - Blocked by (auto_blocking_service)

## Troubleshooting

### Email Not Sending

1. **Check email service status:**
   ```bash
   curl http://localhost:8000/health/notifications
   ```

2. **Verify environment variables:**
   - `EMAIL_ENABLED=true`
   - `SENDGRID_API_KEY` is set
   - `EMAIL_RECIPIENTS` is set

3. **Check SendGrid:**
   - Verify sender email is verified in SendGrid
   - Check SendGrid dashboard for delivery status
   - Verify API key has "Mail Send" permissions

### Auto-Blocking Not Working

1. **Check auto-blocking status:**
   ```bash
   curl http://localhost:8000/health/auto-blocking
   ```

2. **Verify environment variables:**
   - `AUTO_IP_BLOCKING_ENABLED=true`
   - `SUDO_PASSWORD` is set (for UFW commands)

3. **Check UFW:**
   - Verify UFW is installed: `sudo ufw status`
   - Check if IP blocking commands work manually

### Interface Not Updating

1. **Check database:**
   - Verify IP is in `blacklisted_ips` collection
   - Check `is_active` field is `true`

2. **Check API:**
   - Test `/api/ip-blocking/list` endpoint
   - Verify response includes the blocked IP

3. **Check frontend:**
   - Refresh the page
   - Check browser console for errors
   - Verify WebSocket connection (if using real-time updates)

## Test Checklist

- [ ] Email service is enabled and configured
- [ ] Auto-blocking service is enabled
- [ ] Test alert notification email received
- [ ] Test auto-blocking email received
- [ ] IP is blocked in UFW (`sudo ufw status | grep <ip>`)
- [ ] IP appears in database
- [ ] IP appears in `/api/ip-blocking/list` response
- [ ] IP appears in frontend interface
- [ ] Email contains correct information
- [ ] Interface updates when IP is blocked

## Next Steps

After testing:
1. Unblock any test IPs using the cleanup endpoint
2. Monitor email delivery in SendGrid dashboard
3. Check application logs for any errors
4. Verify both notification types work in production

## Support

If you encounter issues:
1. Check application logs: `tail -f logs/app.log`
2. Check email service logs in console output
3. Verify all environment variables are set correctly
4. Test email service independently: `/test/email` endpoint

