# Email Notification Setup Guide

This guide explains how to set up email notifications for security alerts using SendGrid.

## Prerequisites

1. **SendGrid Account**: Sign up for a free SendGrid account at https://sendgrid.com
2. **SendGrid API Key**: Generate an API key from SendGrid dashboard

## SendGrid Setup Steps

### 1. Create SendGrid Account
- Go to https://signup.sendgrid.com
- Sign up for a free account (100 emails/day forever)
- Verify your email address

### 2. Generate API Key
1. Log in to SendGrid dashboard
2. Go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Name it (e.g., "Firewall Analyzer")
5. Select **Full Access** or **Restricted Access** with Mail Send permissions
6. Copy the API key (you'll only see it once!)

### 3. Verify Sender Identity (REQUIRED for sending emails)
- Go to **Settings** → **Sender Authentication**
- Click **Verify a Single Sender** (for testing) or **Authenticate Your Domain** (for production)
- Enter your email address (the one in `EMAIL_FROM_ADDRESS`)
- Check your email inbox and click the verification link
- **IMPORTANT:** You MUST verify the sender email, otherwise you'll get 403 Forbidden errors

## Environment Variables

Add these variables to your `.env` file in the `backend/` directory:

```env
# Email Notification Settings
EMAIL_ENABLED=true
SENDGRID_API_KEY=SG.your_api_key_here
EMAIL_FROM_ADDRESS=alerts@yourdomain.com
EMAIL_FROM_NAME=Firewall Log Analyzer
EMAIL_RECIPIENTS=admin@example.com,security@example.com

# Notification Thresholds
NOTIFICATION_SEVERITY_THRESHOLD=HIGH
NOTIFICATION_ML_RISK_THRESHOLD=70
NOTIFICATION_RATE_LIMIT_MINUTES=15
```

### Configuration Options

#### Email Settings
- `EMAIL_ENABLED`: Enable/disable email notifications (true/false)
- `SENDGRID_API_KEY`: Your SendGrid API key (required if EMAIL_ENABLED=true)
- `EMAIL_FROM_ADDRESS`: Email address to send from (must be verified in SendGrid)
- `EMAIL_FROM_NAME`: Display name for email sender
- `EMAIL_RECIPIENTS`: Comma-separated list of recipient email addresses

#### Notification Thresholds
- `NOTIFICATION_SEVERITY_THRESHOLD`: Minimum severity to send notifications
  - Options: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
  - Default: `HIGH` (sends for HIGH and CRITICAL only)
  
- `NOTIFICATION_ML_RISK_THRESHOLD`: Minimum ML risk score (0-100) to send notifications
  - Default: `70`
  - For MEDIUM/LOW severity alerts, ML risk must exceed this threshold
  
- `NOTIFICATION_RATE_LIMIT_MINUTES`: Minimum minutes between emails for same IP/alert type
  - Default: `15` (prevents email spam)
  - Prevents sending multiple emails for the same threat within this window

## How It Works

### Alert Detection Flow
1. **Log Ingestion**: Logs are continuously ingested from system log files
2. **Alert Computation**: Every 5 minutes, alerts are computed (brute force, DDoS, port scans)
3. **Alert Monitoring**: Every 2 minutes, the alert monitor worker checks for new alerts
4. **ML Scoring**: Each new alert is scored using ML to get risk score
5. **Notification Decision**: 
   - Check severity threshold
   - Check ML risk threshold
   - Check rate limiting
   - Check deduplication
6. **Email Sending**: If all criteria met, email is sent via SendGrid

### Notification Logic

#### CRITICAL Severity
- Always sends email (regardless of ML score)

#### HIGH Severity
- Sends if ML risk score ≥ threshold OR ML unavailable
- If ML risk < threshold, email is not sent

#### MEDIUM/LOW Severity
- Only sends if ML risk score ≥ threshold
- ML must flag it as high risk to warrant notification

### Deduplication
- Prevents duplicate emails for the same alert
- Uses alert type + source IP + time bucket as unique key
- Tracks sent notifications in MongoDB

### Rate Limiting
- Prevents email spam from same IP/alert type
- Default: Max 1 email per 15 minutes per IP/alert type
- Configurable via `NOTIFICATION_RATE_LIMIT_MINUTES`

## Testing

### Test Email Sending
1. Set `EMAIL_ENABLED=true` in `.env`
2. Add your SendGrid API key
3. Add your email to `EMAIL_RECIPIENTS`
4. Restart the backend server
5. Trigger a test alert (e.g., failed SSH login attempts)
6. Check your email inbox

### Verify Configuration
Check the server logs on startup:
```
✓ Email service initialized. Recipients: 1
✓ Alert monitor worker started
```

### Check Notification Status
- View notification history in MongoDB `email_notifications` collection
- Check server logs for notification processing messages

## Troubleshooting

### Emails Not Sending

1. **Check EMAIL_ENABLED**: Must be `true`
2. **Check SendGrid API Key**: Must be valid and have Mail Send permissions
3. **Check Recipients**: Must be valid email addresses
4. **Check Server Logs**: Look for error messages
5. **Check SendGrid Dashboard**: View email activity and delivery status

### Common Issues

#### "EMAIL_ENABLED=true but SENDGRID_API_KEY not set"
- Add `SENDGRID_API_KEY` to your `.env` file

#### "No email recipients configured"
- Add at least one email to `EMAIL_RECIPIENTS`

#### "Failed to send email. Status: 403"
- **Most Common:** Sender email address not verified in SendGrid
  - Solution: Go to SendGrid → Settings → Sender Authentication → Verify Single Sender
  - Enter the email address from `EMAIL_FROM_ADDRESS` in your .env
  - Check your email and click the verification link
- API key doesn't have Mail Send permissions
  - Solution: Regenerate API key with "Mail Send" permissions

#### "Failed to send email. Status: 400"
- Invalid email address format
- From address not verified in SendGrid

## Free Tier Limits

SendGrid Free Tier:
- **100 emails per day** (forever)
- Perfect for student projects and low-volume monitoring
- No credit card required

If you exceed the limit:
- Emails will fail to send
- Check SendGrid dashboard for usage
- Consider upgrading or using alternative service

## Security Notes

- Never commit API keys to version control
- Use environment variables for all sensitive data
- Rotate API keys periodically
- Monitor SendGrid dashboard for suspicious activity

## Support

For SendGrid issues:
- SendGrid Documentation: https://docs.sendgrid.com
- SendGrid Support: support@sendgrid.com

For application issues:
- Check server logs for detailed error messages
- Verify all environment variables are set correctly

