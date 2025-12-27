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

2. Set environment variable:
   ```bash
   export MONGO_URI="your_mongodb_connection_string"
   ```
   Or create a `.env` file:
   ```
   MONGO_URI=your_mongodb_connection_string
   ```

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Access API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

