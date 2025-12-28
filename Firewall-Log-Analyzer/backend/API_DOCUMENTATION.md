# Firewall Log Analyzer API Documentation

## Base URL
```
http://localhost:8000
```

## API Endpoints

### 1. Health Check
- **GET** `/health`
- Returns the backend status

### 2. Get Logs (Paginated with Filters)
- **GET** `/api/logs`
- **Query Parameters:**
  - `page` (int, default: 1): Page number
  - `page_size` (int, default: 50, max: 500): Number of logs per page
  - `source_ip` (string, optional): Filter by source IP
  - `severity` (string, optional): Filter by severity (HIGH, MEDIUM, LOW)
  - `event_type` (string, optional): Filter by event type
  - `destination_port` (int, optional): Filter by destination port
  - `protocol` (string, optional): Filter by protocol
  - `log_source` (string, optional): Filter by log source (e.g., "auth.log", "ufw.log")
  - `start_date` (datetime, optional): Start date (ISO format)
  - `end_date` (datetime, optional): End date (ISO format)
  - `search` (string, optional): Search in source_ip, raw_log, or username
  - `sort_by` (string, default: "timestamp"): Field to sort by (timestamp, severity, source_ip, event_type)
  - `sort_order` (string, default: "desc"): Sort order (asc or desc)

- **Example:**
  ```
  GET /api/logs?page=1&page_size=50&severity=HIGH&sort_by=timestamp&sort_order=desc
  ```

- **Response:**
  ```json
  {
    "logs": [
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
    ],
    "total": 1000,
    "page": 1,
    "page_size": 50,
    "total_pages": 20
  }
  ```

### 3. Get Single Log by ID
- **GET** `/api/logs/{log_id}`
- Returns a single log entry

### 4. Get Statistics Summary
- **GET** `/api/logs/stats/summary`
- **Query Parameters:**
  - `start_date` (datetime, optional): Start date for statistics
  - `end_date` (datetime, optional): End date for statistics

- **Response:**
  ```json
  {
    "total_logs": 10000,
    "severity_counts": {
      "HIGH": 500,
      "MEDIUM": 2000,
      "LOW": 7500
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
      {"hour": "2024-01-01T10:00:00", "count": 100},
      {"hour": "2024-01-01T11:00:00", "count": 150}
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

### 5. Get Top Source IPs
- **GET** `/api/logs/stats/top-ips`
- **Query Parameters:**
  - `limit` (int, default: 10, max: 100): Number of top IPs to return
  - `start_date` (datetime, optional): Start date
  - `end_date` (datetime, optional): End date

### 6. Get Top Ports
- **GET** `/api/logs/stats/top-ports`
- **Query Parameters:**
  - `limit` (int, default: 10, max: 100): Number of top ports to return
  - `start_date` (datetime, optional): Start date
  - `end_date` (datetime, optional): End date

### 7. Ingest Logs (Remote Log Collection)
- **POST** `/api/logs/ingest`
- **Authentication:** Requires `X-API-Key` header
- **Request Body:**
  ```json
  {
    "logs": [
      "Jan  1 10:00:00 hostname sshd[12345]: Failed password for admin from 192.168.1.100",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.1 DST=192.168.1.100 PROTO=TCP DPT=22",
      "Jan  1 10:00:00 kernel: [12345.123] IN=eth0 OUT= SRC=192.168.1.1 DST=192.168.1.100 PROTO=TCP DPT=1433"
    ],
    "log_source": "auth.log"
  }
  ```
- **Query Parameters:**
  - `logs` (array, required): List of raw log lines to ingest (max 1000 per request)
  - `log_source` (string, optional): Hint about log source (auth.log, ufw.log, iptables, syslog, sql.log)
- **Response:**
  ```json
  {
    "success": true,
    "ingested_count": 2,
    "failed_count": 1,
    "total_received": 3,
    "message": "Successfully ingested 2 log(s). 1 failed to parse."
  }
  ```
- **Note:** This endpoint supports automatic parsing of multiple log formats:
  - `auth.log` - SSH authentication logs
  - `ufw.log` - UFW firewall logs
  - `iptables` - iptables/netfilter logs
  - `syslog` - Generic syslog format
  - `sql.log` - SQL-related logs

## Threat Detection Endpoints

### 8. Detect Brute Force Attacks (GET)
- **GET** `/api/threats/brute-force`
- **Query Parameters:**
  - `time_window_minutes` (int, default: 15, max: 1440): Time window in minutes to check for failed attempts
  - `threshold` (int, default: 5, max: 1000): Number of failed attempts to trigger detection
  - `start_date` (datetime, optional): Start date for analysis (ISO format, default: last 24 hours)
  - `end_date` (datetime, optional): End date for analysis (ISO format, default: now)
  - `source_ip` (string, optional): Specific IP address to check

- **Example:**
  ```
  GET /api/threats/brute-force?time_window_minutes=15&threshold=5&start_date=2024-01-01T00:00:00
  ```

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
        "severity": "HIGH"
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

### 9. Detect Brute Force Attacks (POST)
- **POST** `/api/threats/brute-force`
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
- Returns the same response format as GET endpoint

### 10. Get Brute Force Timeline for IP
- **GET** `/api/threats/brute-force/{ip}/timeline`
- **Path Parameters:**
  - `ip` (string): Source IP address
- **Query Parameters:**
  - `start_date` (datetime, optional): Start date for timeline (ISO format, default: last 24 hours)
  - `end_date` (datetime, optional): End date for timeline (ISO format, default: now)

- **Example:**
  ```
  GET /api/threats/brute-force/192.168.1.100/timeline?start_date=2024-01-01T00:00:00
  ```

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

### 11. Detect DDoS/Flood Attacks
- **GET** `/api/threats/ddos`
- **Query Parameters:**
  - `time_window_seconds` (int, default: 60, max: 3600): Time window in seconds for rate calculation
  - `single_ip_threshold` (int, default: 100, max: 100000): Minimum requests per window to flag single IP flood
  - `distributed_ip_count` (int, default: 10, max: 1000): Minimum unique IPs to consider distributed attack
  - `distributed_request_threshold` (int, default: 500, max: 1000000): Total requests threshold for distributed attack
  - `start_date` (datetime, optional): Start date for analysis (ISO format, default: last hour)
  - `end_date` (datetime, optional): End date for analysis (ISO format, default: now)
  - `destination_port` (int, optional): Optional destination port to filter by
  - `protocol` (string, optional): Optional protocol to filter by (TCP, UDP, etc.)
  - `include_reputation` (bool, default: false): Include VirusTotal IP reputation data

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
        "attack_windows": [...],
        "severity": "HIGH"
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

### 12. Detect Port Scanning
- **GET** `/api/threats/port-scan`
- **Query Parameters:**
  - `time_window_minutes` (int, default: 10, max: 1440): Sliding window size in minutes
  - `unique_ports_threshold` (int, default: 10, max: 65535): Minimum unique ports in window to flag scan
  - `min_total_attempts` (int, default: 20, max: 1000000): Minimum total attempts from IP in period
  - `start_date` (datetime, optional): Start date for analysis (ISO format, default: last 24 hours)
  - `end_date` (datetime, optional): End date for analysis (ISO format, default: now)
  - `source_ip` (string, optional): Optional specific IP to check
  - `protocol` (string, optional): Optional protocol filter (TCP/UDP)
  - `include_reputation` (bool, default: false): Include VirusTotal IP reputation data

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
        "attack_windows": [...],
        "severity": "HIGH"
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

- **POST** `/api/threats/port-scan` - Same as GET but with configuration in request body

## Dashboard Endpoints

### 13. Get Dashboard Summary
- **GET** `/api/dashboard/summary`
- Returns comprehensive dashboard overview including:
  - Active alerts (recent high-severity threats)
  - Threat summary (counts by type and severity)
  - Top source IPs with statistics
  - System health metrics

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
    "top_ips": [...],
    "system_health": {
      "database_status": "healthy",
      "total_logs_24h": 10000,
      "high_severity_logs_24h": 500,
      "last_log_timestamp": "2024-01-01T10:30:00"
    },
    "generated_at": "2024-01-01T10:30:00"
  }
  ```

## Report Endpoints

### 14. Get Daily Report
- **GET** `/api/reports/daily`
- **Query Parameters:**
  - `date` (string, optional): Date for the report (YYYY-MM-DD format, default: today)

- **Response:** Comprehensive daily security report with statistics, threat detections, and recommendations

### 15. Get Weekly Report
- **GET** `/api/reports/weekly`
- **Query Parameters:**
  - `start_date` (string, optional): Start date of the week (YYYY-MM-DD format, default: 7 days ago)

- **Response:** Comprehensive weekly security report

### 16. Get Custom Report
- **GET** `/api/reports/custom`
- **Query Parameters:**
  - `start_date` (string, required): Start date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
  - `end_date` (string, required): End date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)

- **Response:** Custom date range security report

### 17. Export Report
- **POST** `/api/reports/export`
- **Request Body:**
  ```json
  {
    "report_type": "DAILY",
    "format": "pdf",
    "date": "2024-01-01"
  }
  ```
- **Formats:** `json`, `csv`, `pdf`
- **Report Types:** `DAILY`, `WEEKLY`, `CUSTOM`
- Returns downloadable file in requested format

## IP Reputation Endpoints

### 18. Get IP Reputation
- **GET** `/api/ip-reputation/{ip_address}`
- **Path Parameters:**
  - `ip_address` (string): IP address to check
- **Query Parameters:**
  - `use_cache` (bool, default: true): Use cached results if available

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
      "country": "US",
      "asn": 12345,
      "categories": ["malware", "phishing"],
      "virustotal_url": "https://www.virustotal.com/gui/ip-address/..."
    }
  }
  ```

### 19. Get Multiple IP Reputations
- **POST** `/api/ip-reputation/batch`
- **Request Body:**
  ```json
  ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
  ```
- **Response:**
  ```json
  {
    "reputations": {
      "192.168.1.1": { ... },
      "10.0.0.1": { ... }
    }
  }
  ```

## Event Types

The system recognizes the following event types:

### SSH Events
- `SSH_FAILED_LOGIN` - Failed SSH login attempt
- `SSH_LOGIN_SUCCESS` - Successful SSH login

### SQL Events
- `SQL_ACCESS_ATTEMPT` - SQL port access attempt
- `SQL_CONNECTION_ATTEMPT` - SQL connection attempt
- `SQL_AUTH_FAILED` - SQL authentication failure
- `SQL_INJECTION_ATTEMPT` - SQL injection attempt detected
- `SQL_PORT_ACCESS` - Access to SQL port detected

### Firewall Events
- `UFW_TRAFFIC` - UFW firewall traffic
- `IPTABLES_TRAFFIC` - iptables traffic
- `IPTABLES_BLOCKED` - iptables blocked/rejected traffic
- `SUSPICIOUS_PORT_ACCESS` - Access to suspicious port (22, 23, 1433, 3306, etc.)
- `CONNECTION_ATTEMPT` - Connection attempt detected

### Generic Events
- `SYSLOG_ENTRY` - Generic syslog entry
- `SYSLOG_SECURITY_EVENT` - Security-related syslog event

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

## Rate Limiting

The ingestion endpoint has rate limiting enabled:
- **Default:** 100 requests per 60 seconds per IP
- **Configurable via environment variables:**
  - `RATE_LIMIT_REQUESTS` - Maximum requests per window
  - `RATE_LIMIT_WINDOW` - Time window in seconds

## Database Indexes

The following indexes are automatically created on startup for optimized queries:

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

## Running the API

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export MONGO_URI="your_mongodb_connection_string"
   export INGESTION_API_KEY="your-secure-api-key"
   export VIRUS_TOTAL_API_KEY="your-virustotal-api-key"  # Optional
   ```
   Or create a `.env` file:
   ```
   MONGO_URI=your_mongodb_connection_string
   INGESTION_API_KEY=your-secure-api-key
   VIRUS_TOTAL_API_KEY=your-virustotal-api-key
   LOG_RETENTION_ENABLED=true
   LOG_RETENTION_MAX_MB=450
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_WINDOW=60
   ```

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Access API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

