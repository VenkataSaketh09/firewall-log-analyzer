# Complete API Documentation Report
## Firewall Log Analyzer Backend

**Base URL:** `http://localhost:8000`

**Version:** 1.0.0

---

## Table of Contents
1. [Health & System Endpoints](#health--system-endpoints)
2. [Log Management APIs](#log-management-apis)
3. [Threat Detection APIs](#threat-detection-apis)
4. [Dashboard APIs](#dashboard-apis)
5. [Report APIs](#report-apis)
6. [IP Reputation APIs](#ip-reputation-apis)
7. [Alert APIs](#alert-apis)
8. [Machine Learning APIs](#machine-learning-apis)
9. [WebSocket APIs](#websocket-apis)

---

## Health & System Endpoints

### 1. Root Endpoint
- **GET** `/`
- **Description:** Returns API information
- **Response:**
```json
{
  "message": "Firewall Log Analyzer API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 2. Health Check
- **GET** `/health`
- **Description:** Returns backend status
- **Response:**
```json
{
  "status": "Backend is running"
}
```

### 3. WebSocket Health Check
- **GET** `/health/websocket`
- **Description:** Check if WebSocket routes are registered
- **Response:**
```json
{
  "status": "WebSocket routes registered",
  "routes": ["/ws/logs/live"],
  "connection_count": 0
}
```

### 4. ML Health Check
- **GET** `/health/ml`
- **Description:** Check ML service status
- **Response:**
```json
{
  "ml": {
    "enabled": true,
    "available": true,
    "anomaly_detector": "loaded",
    "classifier": "loaded"
  }
}
```

### 5. Notification Health Check
- **GET** `/health/notifications`
- **Description:** Check notification service status
- **Response:**
```json
{
  "email_service": {
    "enabled": true,
    "recipients_count": 2,
    "recipients": ["admin@example.com"]
  },
  "notification_service": {
    "enabled": true,
    "severity_threshold": "HIGH",
    "ml_risk_threshold": 75.0,
    "rate_limit_minutes": 60
  },
  "alert_monitor_worker": {
    "running": true,
    "last_check": "2024-01-01T10:00:00"
  },
  "recent_notifications_24h": 5,
  "recent_alerts_24h": 10
}
```

### 6. Test Email Notification
- **POST** `/test/email`
- **Description:** Test email notification functionality
- **Response:**
```json
{
  "success": true,
  "message": "Test email sent",
  "recipients": ["admin@example.com"]
}
```

### 7. Test Database Connection
- **POST** `/test-db`
- **Description:** Test MongoDB Atlas connection
- **Response:**
```json
{
  "status": "Inserted into Atlas"
}
```

---

## Log Management APIs

### 8. Ingest Logs
- **POST** `/api/logs/ingest`
- **Authentication:** Required (`X-API-Key` header)
- **Description:** Ingest raw firewall logs from remote VMs or log sources
- **Request Body:**
```json
{
  "logs": [
    "Jan  1 10:00:00 hostname sshd[12345]: Failed password for admin from 192.168.1.100",
    "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.1 DST=192.168.1.100 PROTO=TCP DPT=22"
  ],
  "log_source": "auth.log"
}
```
- **Response:**
```json
{
  "success": true,
  "ingested_count": 2,
  "failed_count": 0,
  "total_received": 2,
  "message": "Successfully ingested 2 log(s). 0 failed to parse."
}
```
- **Supported Log Sources:** `auth.log`, `ufw.log`, `iptables`, `syslog`, `sql.log`
- **Rate Limit:** 100 requests per 60 seconds per IP (configurable)

### 9. Get Logs (Paginated)
- **GET** `/api/logs`
- **Description:** Get paginated logs with filtering and sorting
- **Query Parameters:**
  - `page` (int, default: 1): Page number
  - `page_size` (int, default: 50, max: 500): Number of logs per page
  - `source_ip` (string, optional): Filter by source IP
  - `severity` (string, optional): Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
  - `event_type` (string, optional): Filter by event type
  - `destination_port` (int, optional): Filter by destination port
  - `protocol` (string, optional): Filter by protocol
  - `log_source` (string, optional): Filter by log source
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
  - `search` (string, optional): Search in source_ip, raw_log, or username
  - `sort_by` (string, default: "timestamp"): Field to sort by
  - `sort_order` (string, default: "desc"): Sort order (asc or desc)
  - `include_reputation` (bool, default: false): Include VirusTotal IP reputation
- **Response:**
```json
{
  "logs": [
    {
      "id": "...",
      "timestamp": "2024-01-01T10:00:00",
      "source_ip": "192.168.1.1",
      "destination_ip": "192.168.1.100",
      "source_port": 54321,
      "destination_port": 22,
      "protocol": "TCP",
      "log_source": "auth.log",
      "event_type": "SSH_FAILED_LOGIN",
      "severity": "HIGH",
      "username": "admin",
      "raw_log": "...",
      "virustotal": {
        "detected": true,
        "reputation_score": 75,
        "threat_level": "HIGH"
      }
    }
  ],
  "total": 1000,
  "page": 1,
  "page_size": 50,
  "total_pages": 20
}
```

### 10. Get Single Log by ID
- **GET** `/api/logs/{log_id}`
- **Description:** Get a single log entry by ID
- **Query Parameters:**
  - `include_reputation` (bool, default: false): Include VirusTotal IP reputation
- **Response:**
```json
{
  "id": "...",
  "timestamp": "2024-01-01T10:00:00",
  "source_ip": "192.168.1.1",
  "destination_port": 22,
  "protocol": "TCP",
  "log_source": "auth.log",
  "event_type": "SSH_FAILED_LOGIN",
  "severity": "HIGH",
  "username": "admin",
  "raw_log": "..."
}
```

### 11. Export Logs (CSV/JSON)
- **GET** `/api/logs/export`
- **Description:** Export logs in CSV or JSON format with filtering
- **Query Parameters:** Same as GET `/api/logs` plus:
  - `format` (string, default: "csv"): Export format (csv or json)
- **Response:** File download (CSV or JSON)

### 12. Export Logs to PDF
- **GET** `/api/logs/export/pdf`
- **Description:** Export logs to PDF with color-coding per row
- **Query Parameters:** Same as GET `/api/logs` plus:
  - `limit` (int, default: 1000, max: 5000): Maximum number of logs
- **Response:** PDF file download

### 13. Export Selected Logs to PDF
- **POST** `/api/logs/export/pdf`
- **Description:** Export specific selected logs to PDF
- **Request Body:**
```json
{
  "log_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
}
```
- **Response:** PDF file download

### 14. Get Statistics Summary
- **GET** `/api/logs/stats/summary`
- **Description:** Get aggregated statistics about logs
- **Query Parameters:**
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
- **Response:**
```json
{
  "total_logs": 10000,
  "severity_counts": {
    "CRITICAL": 50,
    "HIGH": 500,
    "MEDIUM": 2000,
    "LOW": 7450
  },
  "event_type_counts": {
    "SSH_FAILED_LOGIN": 300,
    "SSH_LOGIN_SUCCESS": 100,
    "UFW_TRAFFIC": 5000,
    "SUSPICIOUS_PORT_ACCESS": 200
  },
  "protocol_counts": {
    "TCP": 8000,
    "UDP": 2000
  },
  "logs_by_hour": [
    {"hour": "2024-01-01T10:00:00", "count": 100}
  ],
  "top_source_ips": [
    {
      "source_ip": "192.168.1.1",
      "count": 500,
      "severity_breakdown": {
        "HIGH": 50,
        "MEDIUM": 200,
        "LOW": 250
      }
    }
  ],
  "top_ports": [
    {
      "port": 22,
      "count": 1000,
      "protocol": "TCP"
    }
  ]
}
```

### 15. Get Top Source IPs
- **GET** `/api/logs/stats/top-ips`
- **Description:** Get top source IPs by log count
- **Query Parameters:**
  - `limit` (int, default: 10, max: 100): Number of top IPs
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
  - `include_reputation` (bool, default: false): Include VirusTotal reputation
- **Response:**
```json
[
  {
    "source_ip": "192.168.1.1",
    "count": 500,
    "severity_breakdown": {
      "HIGH": 50,
      "MEDIUM": 200,
      "LOW": 250
    },
    "virustotal": {
      "detected": true,
      "reputation_score": 75,
      "threat_level": "HIGH"
    }
  }
]
```

### 16. Get Top Ports
- **GET** `/api/logs/stats/top-ports`
- **Description:** Get top destination ports by log count
- **Query Parameters:**
  - `limit` (int, default: 10, max: 100): Number of top ports
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
- **Response:**
```json
[
  {
    "port": 22,
    "count": 1000,
    "protocol": "TCP"
  }
]
```

### 17. Get Cached Logs
- **GET** `/api/logs/cache/{log_source}`
- **Description:** Get cached logs for a specific source from Redis
- **Path Parameters:**
  - `log_source` (string): Source of logs (auth, ufw, kern, syslog, messages, all)
- **Query Parameters:**
  - `limit` (int, optional, max: 10000): Maximum number of logs
- **Response:**
```json
{
  "log_source": "auth",
  "count": 100,
  "logs": [...],
  "cache_enabled": true
}
```

### 18. Get Cache Statistics
- **GET** `/api/logs/cache/stats`
- **Description:** Get Redis cache statistics
- **Response:**
```json
{
  "cache_enabled": true,
  "sources": {
    "auth": 100,
    "ufw": 50,
    "kern": 25
  }
}
```

### 19. Clear Cache
- **DELETE** `/api/logs/cache`
- **Description:** Clear cached logs for a specific source or all sources
- **Query Parameters:**
  - `log_source` (string, optional): Source to clear (auth, ufw, kern, syslog, messages, all)
- **Response:**
```json
{
  "success": true,
  "message": "Cache cleared for all sources"
}
```

---

## Threat Detection APIs

### 20. Detect Brute Force Attacks (GET)
- **GET** `/api/threats/brute-force`
- **Description:** Detect brute force attacks based on failed login attempts
- **Query Parameters:**
  - `time_window_minutes` (int, default: 15, max: 1440): Time window in minutes
  - `threshold` (int, default: 5, max: 1000): Failed attempts threshold
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
  - `source_ip` (string, optional): Specific IP to check
  - `severity` (string, optional): Filter by severity
  - `include_reputation` (bool, default: false): Include VirusTotal reputation
  - `include_ml` (bool, default: true): Include ML scoring
  - `format` (string, optional): Export format (csv/json)
- **Response:**
```json
{
  "detections": [
    {
      "source_ip": "192.168.1.100",
      "total_attempts": 25,
      "unique_usernames_attempted": 3,
      "usernames_attempted": ["admin", "root", "user"],
      "first_attempt": "2024-01-01T10:00:00",
      "last_attempt": "2024-01-01T10:30:00",
      "attack_windows": [
        {
          "window_start": "2024-01-01T10:00:00",
          "window_end": "2024-01-01T10:14:30",
          "attempt_count": 8,
          "attempts": [
            {
              "timestamp": "2024-01-01T10:00:00",
              "username": "admin",
              "log_id": "..."
            }
          ]
        }
      ],
      "severity": "HIGH",
      "virustotal": {...},
      "ml_anomaly_score": 0.85,
      "ml_predicted_label": "BRUTE_FORCE",
      "ml_confidence": 0.92,
      "ml_risk_score": 88.5,
      "ml_reasoning": ["High anomaly score", "Multiple username attempts"]
    }
  ],
  "total_detections": 1,
  "time_window_minutes": 15,
  "threshold": 5,
  "time_range": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-02T00:00:00"
  }
}
```

### 21. Detect Brute Force Attacks (POST)
- **POST** `/api/threats/brute-force`
- **Description:** Detect brute force attacks with configuration in request body
- **Request Body:**
```json
{
  "time_window_minutes": 15,
  "threshold": 5,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-02T00:00:00",
  "source_ip": "192.168.1.100"
}
```
- **Query Parameters:**
  - `include_reputation` (bool, default: false)
  - `include_ml` (bool, default: true)
- **Response:** Same as GET endpoint

### 22. Get Brute Force Timeline for IP
- **GET** `/api/threats/brute-force/{ip}/timeline`
- **Description:** Get detailed timeline of brute force attempts for a specific IP
- **Path Parameters:**
  - `ip` (string): Source IP address
- **Query Parameters:**
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
- **Response:**
```json
{
  "source_ip": "192.168.1.100",
  "total_attempts": 25,
  "timeline": [
    {
      "timestamp": "2024-01-01T10:00:00",
      "username": "admin",
      "log_id": "..."
    }
  ],
  "time_range": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-02T00:00:00"
  }
}
```

### 23. Detect DDoS/Flood Attacks
- **GET** `/api/threats/ddos`
- **Description:** Detect DDoS/flood attacks based on traffic patterns
- **Query Parameters:**
  - `time_window_seconds` (int, default: 60, max: 3600): Time window in seconds
  - `single_ip_threshold` (int, default: 100, max: 100000): Single IP flood threshold
  - `distributed_ip_count` (int, default: 10, max: 1000): Min unique IPs for distributed attack
  - `distributed_request_threshold` (int, default: 500, max: 1000000): Distributed attack threshold
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
  - `destination_port` (int, optional): Filter by destination port
  - `protocol` (string, optional): Filter by protocol
  - `severity` (string, optional): Filter by severity
  - `include_reputation` (bool, default: false): Include VirusTotal reputation
  - `include_ml` (bool, default: true): Include ML scoring
  - `format` (string, optional): Export format (csv/json)
- **Response:**
```json
{
  "detections": [
    {
      "attack_type": "SINGLE_IP_FLOOD",
      "source_ips": ["192.168.1.100"],
      "source_ip_count": 1,
      "total_requests": 5000,
      "peak_request_rate": 1200.5,
      "avg_request_rate": 800.2,
      "target_ports": [80, 443],
      "target_protocols": ["TCP"],
      "first_request": "2024-01-01T10:00:00",
      "last_request": "2024-01-01T10:30:00",
      "attack_windows": [
        {
          "window_start": "2024-01-01T10:00:00",
          "window_end": "2024-01-01T10:01:00",
          "request_count": 1200,
          "request_rate_per_min": 1200.0,
          "target_ports": {80: 600, 443: 600},
          "protocols": {"TCP": 1200}
        }
      ],
      "severity": "HIGH",
      "source_ip_reputations": {
        "192.168.1.100": {...}
      },
      "ml_anomaly_score": 0.90,
      "ml_predicted_label": "DDOS",
      "ml_confidence": 0.95,
      "ml_risk_score": 92.0
    }
  ],
  "total_detections": 1,
  "time_window_seconds": 60,
  "single_ip_threshold": 100,
  "distributed_ip_count": 10,
  "distributed_request_threshold": 500,
  "time_range": {
    "start": "2024-01-01T09:00:00",
    "end": "2024-01-01T10:00:00"
  }
}
```

### 24. Detect Port Scanning
- **GET** `/api/threats/port-scan`
- **Description:** Detect port scanning based on single IP probing many ports
- **Query Parameters:**
  - `time_window_minutes` (int, default: 10, max: 1440): Sliding window size
  - `unique_ports_threshold` (int, default: 10, max: 65535): Min unique ports to flag
  - `min_total_attempts` (int, default: 20, max: 1000000): Min total attempts
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
  - `source_ip` (string, optional): Specific IP to check
  - `protocol` (string, optional): Protocol filter (TCP/UDP)
  - `severity` (string, optional): Filter by severity
  - `include_reputation` (bool, default: false): Include VirusTotal reputation
  - `include_ml` (bool, default: true): Include ML scoring
  - `format` (string, optional): Export format (csv/json)
- **Response:**
```json
{
  "detections": [
    {
      "source_ip": "192.168.1.100",
      "total_attempts": 150,
      "unique_ports_attempted": 45,
      "ports_attempted": [22, 23, 80, 443, 1433, ...],
      "first_attempt": "2024-01-01T10:00:00",
      "last_attempt": "2024-01-01T10:30:00",
      "attack_windows": [
        {
          "window_start": "2024-01-01T10:00:00",
          "window_end": "2024-01-01T10:10:00",
          "attempt_count": 45,
          "unique_ports": 45,
          "ports": [22, 23, 80, ...],
          "attempts": [...]
        }
      ],
      "severity": "HIGH",
      "virustotal": {...},
      "ml_anomaly_score": 0.88,
      "ml_predicted_label": "PORT_SCAN",
      "ml_confidence": 0.90,
      "ml_risk_score": 89.5
    }
  ],
  "total_detections": 1,
  "time_window_minutes": 10,
  "unique_ports_threshold": 10,
  "min_total_attempts": 20,
  "time_range": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-02T00:00:00"
  }
}
```

### 25. Detect Port Scanning (POST)
- **POST** `/api/threats/port-scan`
- **Description:** Detect port scans with configuration in request body
- **Request Body:**
```json
{
  "time_window_minutes": 10,
  "unique_ports_threshold": 10,
  "min_total_attempts": 20,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-02T00:00:00",
  "source_ip": "192.168.1.100",
  "protocol": "TCP"
}
```
- **Query Parameters:**
  - `include_reputation` (bool, default: false)
- **Response:** Same as GET endpoint

---

## Dashboard APIs

### 26. Get Dashboard Summary
- **GET** `/api/dashboard/summary`
- **Description:** Get comprehensive dashboard overview
- **Response:**
```json
{
  "active_alerts": [
    {
      "type": "BRUTE_FORCE",
      "source_ip": "192.168.1.100",
      "severity": "HIGH",
      "detected_at": "2024-01-01T10:30:00",
      "description": "Brute force attack: 25 failed login attempts",
      "threat_count": 25
    }
  ],
  "threats": {
    "total_brute_force": 5,
    "total_ddos": 2,
    "total_port_scan": 3,
    "critical_count": 1,
    "high_count": 5,
    "medium_count": 3,
    "low_count": 1
  },
  "top_ips": [
    {
      "source_ip": "192.168.1.1",
      "total_logs": 500,
      "severity_breakdown": {
        "HIGH": 50,
        "MEDIUM": 200,
        "LOW": 250
      },
      "last_seen": "2024-01-01T10:30:00"
    }
  ],
  "system_health": {
    "database_status": "healthy",
    "total_logs_24h": 10000,
    "total_logs_all_time": 50000,
    "high_severity_logs_24h": 500,
    "last_log_timestamp": "2024-01-01T10:30:00",
    "uptime_seconds": null
  },
  "generated_at": "2024-01-01T10:30:00"
}
```

---

## Report APIs

### 27. Get Daily Report
- **GET** `/api/reports/daily`
- **Description:** Generate daily security report
- **Query Parameters:**
  - `date` (string, optional): Date (YYYY-MM-DD, default: today)
  - `include_charts` (bool, default: true): Include charts/statistics
  - `include_summary` (bool, default: true): Include executive summary
  - `include_threats` (bool, default: true): Include threats sections
  - `include_logs` (bool, default: false): Include detailed logs
- **Response:**
```json
{
  "report": {
    "report_type": "DAILY",
    "report_date": "2024-01-01T00:00:00",
    "period": {
      "start": "2024-01-01T00:00:00",
      "end": "2024-01-01T23:59:59"
    },
    "summary": {
      "total_logs": 10000,
      "security_score": 75,
      "security_status": "MODERATE",
      "threat_summary": {
        "total_brute_force_attacks": 5,
        "total_ddos_attacks": 2,
        "total_port_scan_attacks": 3,
        "total_threats": 10,
        "critical_threats": 1,
        "high_threats": 5,
        "medium_threats": 3,
        "low_threats": 1
      }
    },
    "log_statistics": {...},
    "threat_detections": {...},
    "top_threat_sources": [...],
    "recommendations": [...],
    "time_breakdown": [...]
  }
}
```

### 28. Get Weekly Report
- **GET** `/api/reports/weekly`
- **Description:** Generate weekly security report
- **Query Parameters:**
  - `start_date` (string, optional): Start date (YYYY-MM-DD, default: 7 days ago)
  - `include_charts` (bool, default: true)
  - `include_summary` (bool, default: true)
  - `include_threats` (bool, default: true)
  - `include_logs` (bool, default: false)
- **Response:** Same structure as daily report

### 29. Get Custom Report
- **GET** `/api/reports/custom`
- **Description:** Generate custom date range security report
- **Query Parameters:**
  - `start_date` (string, required): Start date (ISO format)
  - `end_date` (string, required): End date (ISO format)
  - `include_charts` (bool, default: true)
  - `include_summary` (bool, default: true)
  - `include_threats` (bool, default: true)
  - `include_logs` (bool, default: false)
- **Response:** Same structure as daily report

### 30. Export Report
- **POST** `/api/reports/export`
- **Description:** Export reports in JSON, CSV, or PDF format
- **Request Body:**
```json
{
  "report_type": "DAILY",
  "format": "pdf",
  "date": "2024-01-01",
  "start_date": "2024-01-01",
  "end_date": "2024-01-07",
  "include_charts": true,
  "include_summary": true,
  "include_threats": true,
  "include_logs": false
}
```
- **Response:** File download (JSON, CSV, or PDF)

### 31. Save Report
- **POST** `/api/reports/save`
- **Description:** Save a generated report to database
- **Request Body:**
```json
{
  "report_name": "Daily Security Report - Jan 1",
  "report": {...},
  "notes": "Important security incidents detected"
}
```
- **Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "message": "Report saved successfully"
}
```

### 32. Get Report History
- **GET** `/api/reports/history`
- **Description:** Get list of saved reports
- **Query Parameters:**
  - `limit` (int, default: 50, max: 100): Maximum number of reports
  - `skip` (int, default: 0): Number to skip for pagination
  - `report_type` (string, optional): Filter by type (DAILY, WEEKLY, CUSTOM)
- **Response:**
```json
{
  "reports": [
    {
      "id": "507f1f77bcf86cd799439011",
      "report_name": "Daily Security Report - Jan 1",
      "report_type": "DAILY",
      "report_date": "2024-01-01",
      "period": {
        "start": "2024-01-01T00:00:00",
        "end": "2024-01-01T23:59:59"
      },
      "summary": {...},
      "created_at": "2024-01-01T10:00:00",
      "notes": "Important security incidents"
    }
  ],
  "total": 10
}
```

### 33. Get Saved Report
- **GET** `/api/reports/history/{report_id}`
- **Description:** Get a specific saved report by ID
- **Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "report_name": "Daily Security Report - Jan 1",
  "report": {...},
  "created_at": "2024-01-01T10:00:00",
  "notes": "Important security incidents"
}
```

### 34. Delete Saved Report
- **DELETE** `/api/reports/history/{report_id}`
- **Description:** Delete a saved report by ID
- **Response:**
```json
{
  "message": "Report deleted successfully",
  "id": "507f1f77bcf86cd799439011"
}
```

---

## IP Reputation APIs

### 35. Get IP Reputation
- **GET** `/api/ip-reputation/{ip_address}`
- **Description:** Get VirusTotal reputation for a specific IP
- **Query Parameters:**
  - `use_cache` (bool, default: true): Use cached results
- **Response:**
```json
{
  "ip": "192.168.1.100",
  "reputation": {
    "detected": true,
    "reputation_score": 75,
    "threat_level": "HIGH",
    "malicious_count": 8,
    "suspicious_count": 2,
    "total_engines": 50,
    "last_analysis_date": "2024-01-01T10:00:00",
    "country": "US",
    "asn": 12345,
    "as_owner": "Example ISP",
    "categories": ["malware", "phishing"],
    "detection_names": ["Trojan", "Malware"],
    "virustotal_url": "https://www.virustotal.com/gui/ip-address/..."
  }
}
```

### 36. Get Multiple IP Reputations
- **POST** `/api/ip-reputation/batch`
- **Description:** Get VirusTotal reputation for multiple IPs
- **Request Body:**
```json
["192.168.1.1", "10.0.0.1", "172.16.0.1"]
```
- **Response:**
```json
{
  "reputations": {
    "192.168.1.1": {
      "detected": true,
      "reputation_score": 75,
      "threat_level": "HIGH",
      ...
    },
    "10.0.0.1": {
      "detected": false,
      "reputation_score": 5,
      "threat_level": "CLEAN",
      ...
    }
  }
}
```

---

## Alert APIs

### 37. Get Latest Alerts
- **GET** `/api/alerts/latest`
- **Description:** Get latest computed alerts (cached in MongoDB)
- **Query Parameters:**
  - `lookback_seconds` (int, default: 86400, max: 604800): Lookback window in seconds
  - `bucket_minutes` (int, default: 5, max: 60): Bucket size for caching
  - `include_details` (bool, default: false): Include detector details
- **Response:**
```json
{
  "time_range": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-02T00:00:00"
  },
  "count": 10,
  "alerts": [
    {
      "id": "...",
      "bucket_end": "2024-01-01T10:00:00",
      "lookback_seconds": 86400,
      "alert_type": "BRUTE_FORCE",
      "source_ip": "192.168.1.100",
      "severity": "HIGH",
      "first_seen": "2024-01-01T09:00:00",
      "last_seen": "2024-01-01T10:00:00",
      "count": 25,
      "description": "Brute force attack detected",
      "computed_at": "2024-01-01T10:05:00",
      "details": {...}
    }
  ]
}
```

---

## Machine Learning APIs

### 38. ML Status
- **GET** `/api/ml/status`
- **Description:** Get ML service status and last retrain information
- **Response:**
```json
{
  "ml": {
    "enabled": true,
    "available": true,
    "anomaly_detector": "loaded",
    "classifier": "loaded"
  },
  "retrain": {
    "status": "completed",
    "started_at": "2024-01-01T10:00:00",
    "finished_at": "2024-01-01T10:30:00",
    "error": null,
    "versions": {
      "pre": "v1.0",
      "post": "v1.1"
    }
  }
}
```

### 39. Manual Predict
- **POST** `/api/ml/predict`
- **Description:** Manually predict threat for a log entry
- **Request Body:**
```json
{
  "raw_log": "Jan  1 10:00:00 hostname sshd[12345]: Failed password for admin from 192.168.1.100",
  "timestamp": "2024-01-01T10:00:00",
  "log_source": "auth.log",
  "event_type": "SSH_FAILED_LOGIN",
  "threat_type_hint": "BRUTE_FORCE",
  "severity_hint": "HIGH",
  "source_ip": "192.168.1.100"
}
```
- **Response:**
```json
{
  "ml_enabled": true,
  "ml_available": true,
  "anomaly_score": 0.85,
  "predicted_label": "BRUTE_FORCE",
  "confidence": 0.92,
  "risk_score": 88.5,
  "reasoning": ["High anomaly score", "Multiple failed attempts"],
  "error": null
}
```

### 40. ML Metrics
- **GET** `/api/ml/metrics`
- **Description:** Get ML model metrics and metadata
- **Response:**
```json
{
  "metadata": {
    "version": "v1.1",
    "trained_at": "2024-01-01T10:00:00",
    "training_samples": 10000
  },
  "anomaly": {
    "accuracy": 0.95,
    "precision": 0.92,
    "recall": 0.88
  },
  "classifier": {
    "accuracy": 0.90,
    "f1_score": 0.88
  }
}
```

### 41. Retrain Models
- **POST** `/api/ml/retrain`
- **Description:** Schedule model retraining
- **Request Body:**
```json
{
  "train_anomaly": true,
  "train_classifier": true
}
```
- **Response:**
```json
{
  "status": "scheduled",
  "requested": {
    "train_anomaly": true,
    "train_classifier": true
  },
  "retrain": {
    "status": "running",
    "started_at": "2024-01-01T10:00:00"
  }
}
```

### 42. List Model Versions
- **GET** `/api/ml/versions`
- **Description:** List all model versions
- **Query Parameters:**
  - `limit` (int, default: 50): Maximum number of versions
- **Response:**
```json
{
  "active_version": "v1.1",
  "versions": [
    {
      "version_id": "v1.1",
      "created_at": "2024-01-01T10:00:00",
      "metrics": {...}
    },
    {
      "version_id": "v1.0",
      "created_at": "2023-12-01T10:00:00",
      "metrics": {...}
    }
  ]
}
```

### 43. Rollback Models
- **POST** `/api/ml/rollback`
- **Description:** Rollback to a previous model version
- **Request Body:**
```json
{
  "version_id": "v1.0"
}
```
- **Response:**
```json
{
  "status": "rolled_back",
  "active_version": "v1.0"
}
```

---

## WebSocket APIs

### 44. Live Log Streaming
- **WebSocket** `/ws/logs/live`
- **Description:** WebSocket endpoint for live raw log streaming
- **Connection:** Client connects to WebSocket endpoint
- **Client Messages:**
  - Subscribe: `{"type": "subscribe", "log_source": "auth"}`
  - Unsubscribe: `{"type": "unsubscribe", "log_source": "auth"}`
- **Supported Log Sources:** `auth`, `ufw`, `kern`, `syslog`, `messages`, `all`
- **Server Messages:**
  - Connection: `{"type": "connected", "message": "Connected to live log stream", "connection_id": "..."}`
  - Subscribed: `{"type": "subscribed", "log_source": "auth", "message": "Subscribed to auth logs"}`
  - Log Entry: `{"type": "log", "log_source": "auth", "raw_log": "...", "timestamp": "..."}`
  - Error: `{"type": "error", "message": "..."}`

---

## Authentication

### API Key Authentication
The log ingestion endpoint (`POST /api/logs/ingest`) requires API key authentication.

**Header:**
```
X-API-Key: your-api-key-here
```

**Environment Variable:**
```
INGESTION_API_KEY=your-secure-api-key
```

---

## Rate Limiting

The ingestion endpoint has rate limiting enabled:
- **Default:** 100 requests per 60 seconds per IP
- **Configurable via environment variables:**
  - `RATE_LIMIT_REQUESTS` - Maximum requests per window
  - `RATE_LIMIT_WINDOW` - Time window in seconds

---

## Event Types

The system recognizes the following event types:

### SSH Events
- `SSH_FAILED_LOGIN` - Failed SSH login attempt
- `SSH_LOGIN_SUCCESS` - Successful SSH login

### SQL Events
- `SQL_ACCESS_ATTEMPT` - SQL port access attempt
- `SQL_CONNECTION_ATTEMPT` - SQL connection attempt
- `SQL_AUTH_FAILED` - SQL authentication failure
- `SQL_INJECTION_ATTEMPT` - SQL injection attempt detected (CRITICAL)
- `SQL_PORT_ACCESS` - Access to SQL port detected

### Firewall Events
- `UFW_TRAFFIC` - UFW firewall traffic
- `IPTABLES_TRAFFIC` - iptables traffic
- `IPTABLES_BLOCKED` - iptables blocked/rejected traffic
- `SUSPICIOUS_PORT_ACCESS` - Access to suspicious port
- `CONNECTION_ATTEMPT` - Connection attempt detected

### Generic Events
- `SYSLOG_ENTRY` - Generic syslog entry
- `SYSLOG_SECURITY_EVENT` - Security-related syslog event

---

## Database Indexes

The following indexes are automatically created for optimized queries:

### Single Field Indexes:
- `timestamp` (descending)
- `source_ip` (ascending)
- `severity` (ascending)
- `event_type` (ascending)
- `destination_port` (ascending)
- `protocol` (ascending)
- `log_source` (ascending)

### Compound Indexes:
- `timestamp + severity`
- `source_ip + timestamp`
- `severity + event_type + timestamp`
- `destination_port + timestamp`

---

## Summary

**Total APIs:** 44 endpoints
- Health & System: 7 endpoints
- Log Management: 12 endpoints
- Threat Detection: 6 endpoints
- Dashboard: 1 endpoint
- Reports: 8 endpoints
- IP Reputation: 2 endpoints
- Alerts: 1 endpoint
- Machine Learning: 6 endpoints
- WebSocket: 1 endpoint

