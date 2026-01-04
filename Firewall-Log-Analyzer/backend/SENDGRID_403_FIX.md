# Fix SendGrid 403 Forbidden Error

## Problem
You're seeing this error in logs:
```
✗ Error sending email to mvsaketh2020@gmail.com: HTTP Error 403: Forbidden
```

## Root Cause
SendGrid requires you to **verify the sender email address** before you can send emails. This is a security measure to prevent spam.

## Solution: Verify Sender Email in SendGrid

### Step 1: Log in to SendGrid
1. Go to https://app.sendgrid.com
2. Log in with your SendGrid account

### Step 2: Verify Single Sender
1. Go to **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender** (for testing/development)
3. Fill in the form:
   - **From Email Address**: `mvsaketh2005@gmail.com` (must match `EMAIL_FROM_ADDRESS` in your .env)
   - **From Name**: `Firewall Log Analyzer` (optional)
   - **Reply To**: Same as from email
   - **Company Address**: Your address (required)
   - **City, State, Zip, Country**: Fill in your details
4. Click **Create**

### Step 3: Verify Email
1. Check your email inbox (`mvsaketh2005@gmail.com`)
2. Look for an email from SendGrid with subject "Verify your Single Sender"
3. Click the verification link in the email
4. You should see "Sender Verified" in SendGrid dashboard

### Step 4: Test Again
1. Restart your backend server (if needed)
2. Test email: `curl -X POST http://localhost:8000/test/email`
3. Or wait for next alert to trigger automatically

## Alternative: Use Sandbox Mode (For Testing Only)

If you want to test without verifying, SendGrid has a sandbox mode, but it's limited:
- Only sends to verified recipient emails
- Shows "Sent via SendGrid Sandbox" in email
- Not recommended for production

## Verification Checklist

✅ SendGrid account created
✅ API key generated and added to `.env`
✅ Sender email verified in SendGrid dashboard
✅ `EMAIL_FROM_ADDRESS` in `.env` matches verified sender email
✅ Backend server restarted after changes

## After Verification

Once the sender is verified:
- The 403 error should disappear
- Emails will be sent successfully
- You'll see: `✓ Alert email sent to [recipient]` in logs

## Still Getting 403?

1. **Double-check sender email**: Must match exactly (case-sensitive)
2. **Check API key permissions**: Must have "Mail Send" permission
3. **Wait a few minutes**: Verification can take 1-2 minutes to propagate
4. **Check SendGrid dashboard**: Look for any warnings or restrictions

## Quick Test

After verification, test with:
```bash
curl -X POST http://localhost:8000/test/email
```

You should receive a test email within seconds.

