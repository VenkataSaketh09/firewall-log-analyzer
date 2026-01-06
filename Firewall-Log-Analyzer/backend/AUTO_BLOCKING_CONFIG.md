# Automatic IP Blocking Configuration

This document describes the configuration options for the automatic IP blocking feature.

## Overview

The automatic IP blocking system uses a combination of **ML (Machine Learning) + Rules-based** approach to automatically block malicious IPs when threats are detected. When an IP is auto-blocked, an email notification is sent to configured recipients.

## Environment Variables

### Enable/Disable Auto-Blocking

```bash
# Enable or disable automatic IP blocking (default: true)
AUTO_IP_BLOCKING_ENABLED=true
```

### Rules-Based Thresholds

#### Severity-Based Blocking

Control which severity levels trigger automatic blocking:

```bash
# Block CRITICAL severity threats (default: true)
AUTO_BLOCK_CRITICAL=true

# Block HIGH severity threats (default: true)
AUTO_BLOCK_HIGH=true

# Block MEDIUM severity threats (default: false)
AUTO_BLOCK_MEDIUM=false

# Block LOW severity threats (default: false)
AUTO_BLOCK_LOW=false
```

#### Attack-Specific Thresholds

```bash
# Minimum brute force attempts to trigger auto-block (default: 20)
AUTO_BLOCK_BRUTE_FORCE_THRESHOLD=20

# Minimum DDoS requests to trigger auto-block (default: 500)
AUTO_BLOCK_DDOS_THRESHOLD=500

# Minimum port scan ports to trigger auto-block (default: 25)
AUTO_BLOCK_PORT_SCAN_THRESHOLD=25
```

### ML-Based Thresholds

```bash
# ML risk score threshold (0-100, default: 75.0)
# IPs with risk score >= this value will be considered for blocking
AUTO_BLOCK_ML_RISK_THRESHOLD=75.0

# ML anomaly score threshold (0-1, default: 0.7)
# IPs with anomaly score >= this value will be considered for blocking
AUTO_BLOCK_ML_ANOMALY_THRESHOLD=0.7

# ML confidence threshold (0-1, default: 0.7)
# ML predictions with confidence >= this value will be trusted
AUTO_BLOCK_ML_CONFIDENCE_THRESHOLD=0.7

# Require ML confirmation for blocking (default: false)
# If true, both rules AND ML must agree to block an IP
# If false, either rules OR ML can trigger blocking
AUTO_BLOCK_REQUIRE_ML=false
```

### Cooldown Period

```bash
# Cooldown period in hours (default: 24)
# Recently unblocked IPs won't be auto-blocked again within this period
AUTO_BLOCK_COOLDOWN_HOURS=24
```

## How It Works

### Decision Process

1. **Threat Detection**: When a threat is detected (brute force, DDoS, port scan), the system evaluates whether to auto-block.

2. **Rules-Based Evaluation**:
   - Checks if severity level matches configured thresholds
   - Checks if attack metrics exceed attack-specific thresholds
   - Example: If `AUTO_BLOCK_HIGH=true` and threat severity is HIGH, rules-based decision = BLOCK

3. **ML-Based Evaluation**:
   - Checks ML risk score against `AUTO_BLOCK_ML_RISK_THRESHOLD`
   - Checks ML anomaly score against `AUTO_BLOCK_ML_ANOMALY_THRESHOLD`
   - Checks ML predicted label (BRUTE_FORCE, DDOS, PORT_SCAN, etc.)
   - Checks ML confidence against `AUTO_BLOCK_ML_CONFIDENCE_THRESHOLD`

4. **Combined Decision**:
   - If `AUTO_BLOCK_REQUIRE_ML=true`: Both rules AND ML must agree
   - If `AUTO_BLOCK_REQUIRE_ML=false`: Either rules OR ML can trigger blocking

5. **Cooldown Check**: If IP was recently unblocked (within cooldown period), skip blocking

6. **Blocking Action**:
   - Execute UFW command: `sudo ufw deny from <IP>`
   - Store blocking record in database
   - Send email notification

### Email Notifications

When an IP is auto-blocked, an email is sent with:
- IP address that was blocked
- Threat type (BRUTE_FORCE, DDOS, PORT_SCAN)
- Severity level
- Blocking reason (rules-based or ML-based)
- Attack metrics (attempts, ports, requests, etc.)
- ML scores (if available)
- Link to IP blocking page for review/unblocking

Email configuration uses the same settings as regular alerts:
- `EMAIL_ENABLED=true`
- `SENDGRID_API_KEY=your_key`
- `EMAIL_RECIPIENTS=admin@example.com,security@example.com`

## Viewing Auto-Blocked IPs

Auto-blocked IPs appear in the IP Blocking page with:
- **Orange "Auto-Blocked" badge** to distinguish from manually blocked IPs
- **"auto_blocking_service"** as the "Blocked By" field
- **"AUTO-BLOCK: [reason]"** in the reason field

You can manually unblock any auto-blocked IP if you believe it's a false positive.

## Best Practices

1. **Start Conservative**: Begin with `AUTO_BLOCK_CRITICAL=true` and `AUTO_BLOCK_HIGH=true`, keep others false
2. **Monitor False Positives**: Review auto-blocked IPs regularly and adjust thresholds
3. **Use ML Confirmation**: Set `AUTO_BLOCK_REQUIRE_ML=true` for stricter blocking (requires both rules and ML to agree)
4. **Set Appropriate Cooldown**: Adjust `AUTO_BLOCK_COOLDOWN_HOURS` based on your needs (prevents re-blocking recently unblocked IPs)
5. **Email Notifications**: Ensure email notifications are configured to receive alerts about auto-blocked IPs

## Example Configuration

```bash
# Enable auto-blocking
AUTO_IP_BLOCKING_ENABLED=true

# Block CRITICAL and HIGH severity threats
AUTO_BLOCK_CRITICAL=true
AUTO_BLOCK_HIGH=true
AUTO_BLOCK_MEDIUM=false
AUTO_BLOCK_LOW=false

# Attack-specific thresholds
AUTO_BLOCK_BRUTE_FORCE_THRESHOLD=20
AUTO_BLOCK_DDOS_THRESHOLD=500
AUTO_BLOCK_PORT_SCAN_THRESHOLD=25

# ML thresholds (conservative)
AUTO_BLOCK_ML_RISK_THRESHOLD=80.0
AUTO_BLOCK_ML_ANOMALY_THRESHOLD=0.8
AUTO_BLOCK_ML_CONFIDENCE_THRESHOLD=0.75

# Require ML confirmation for extra safety
AUTO_BLOCK_REQUIRE_ML=true

# 24 hour cooldown
AUTO_BLOCK_COOLDOWN_HOURS=24
```

