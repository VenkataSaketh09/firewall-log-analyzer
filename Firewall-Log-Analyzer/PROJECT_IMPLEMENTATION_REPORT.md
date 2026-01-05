# Firewall Log Analyzer - Complete Implementation Report

**Version:** 1.0.0  
**Date:** January 2025

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Threat Detection & Classifications](#threat-detection--classifications)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [Machine Learning Engine](#machine-learning-engine)
7. [Key Features & Capabilities](#key-features--capabilities)
8. [Technology Stack](#technology-stack)

---

## Project Overview

The **Firewall Log Analyzer** is a comprehensive security monitoring and threat detection system that analyzes Linux firewall logs in real-time. It combines rule-based detection algorithms with machine learning models to identify and classify various security threats, providing administrators with actionable insights and automated alerting.

### Core Purpose
- **Real-time Log Analysis**: Process and analyze firewall logs from multiple sources
- **Threat Detection**: Automatically detect brute force attacks, DDoS floods, port scans, and other security threats
- **ML-Enhanced Detection**: Use machine learning to improve detection accuracy and reduce false positives
- **Visualization & Reporting**: Provide intuitive dashboards and automated security reports
- **Live Monitoring**: Stream logs in real-time via WebSocket connections

---

## System Architecture

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React.js)                       │
│  - Dashboard, Logs, Threats, Reports Pages                  │
│  - Real-time WebSocket connections                          │
│  - Interactive charts and visualizations                    │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI - Python)                  │
│  - RESTful APIs for all operations                          │
│  - WebSocket server for live log streaming                   │
│  - Threat detection services                                 │
│  - ML service integration                                    │
│  - Alert & notification services                            │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│         Data Layer (MongoDB Atlas + Redis)                  │
│  - MongoDB: Log storage, threats, alerts                    │
│  - Redis: Real-time log caching for WebSocket              │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              ML Engine (Python - scikit-learn)               │
│  - Anomaly Detection (Isolation Forest)                     │
│  - Threat Classifier (Random Forest)                        │
│  - Feature Engineering                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Threat Detection & Classifications

The system detects and classifies the following security threats:

### 1. **BRUTE_FORCE Attacks**

**Description**: Multiple failed login attempts from a single source IP address attempting to gain unauthorized access.

**Detection Algorithm**:
- **Time Window**: 15 minutes (configurable)
- **Threshold**: 5+ failed login attempts (configurable)
- **Pattern Recognition**: Groups failed SSH login attempts by source IP
- **Attack Windows**: Identifies concentrated attack periods
- **Severity Levels**:
  - **CRITICAL**: 50+ attempts or 10+ unique usernames
  - **HIGH**: 20-49 attempts or 5-9 unique usernames
  - **MEDIUM**: 10-19 attempts or 3-4 unique usernames
  - **LOW**: 5-9 attempts

**Features Detected**:
- Total failed login attempts
- Unique usernames attempted
- Attack timeline with timestamps
- Attack windows (concentrated time periods)
- First and last attempt timestamps
- VirusTotal reputation integration

**Event Types**:
- `SSH_FAILED_LOGIN` - Failed SSH authentication attempts

---

### 2. **DDoS/Flood Attacks**

**Description**: High-volume traffic floods designed to overwhelm network resources or services.

**Detection Types**:

#### a) Single IP Floods
- **Time Window**: 60 seconds (configurable)
- **Threshold**: 100+ requests per window (configurable)
- **Detection**: Identifies single source IP generating excessive requests

#### b) Distributed Floods
- **Time Window**: 60 seconds (configurable)
- **IP Count Threshold**: 10+ unique source IPs (configurable)
- **Request Threshold**: 500+ total requests (configurable)
- **Detection**: Identifies coordinated attacks from multiple IPs targeting same destination/port

**Severity Levels**:
- **CRITICAL**: >1000 requests/sec or >50 distributed IPs
- **HIGH**: 500-1000 requests/sec or 20-50 distributed IPs
- **MEDIUM**: 200-499 requests/sec or 10-19 distributed IPs
- **LOW**: 100-199 requests/sec

**Features Detected**:
- Peak request rate (requests per second)
- Total requests in attack window
- Unique source IPs involved
- Target destination ports
- Protocols used (TCP, UDP, etc.)
- Attack duration and timeline

**Event Types**:
- `DDOS_FLOOD` - Distributed denial of service flood detected

---

### 3. **Port Scanning**

**Description**: Systematic probing of multiple destination ports from a single source IP, typically reconnaissance for potential vulnerabilities.

**Detection Algorithm**:
- **Time Window**: 10 minutes (configurable, sliding window)
- **Unique Ports Threshold**: 10+ unique destination ports (configurable)
- **Minimum Attempts**: 20+ total connection attempts (configurable)
- **Pattern Recognition**: Tracks unique ports accessed by each source IP within time windows

**Severity Levels**:
- **CRITICAL**: 50+ unique ports scanned
- **HIGH**: 30-49 unique ports
- **MEDIUM**: 20-29 unique ports
- **LOW**: 10-19 unique ports

**Features Detected**:
- Unique destination ports scanned
- Total connection attempts
- Ports scanned (list)
- Protocols used
- Scan timeline
- Attack windows

**Event Types**:
- `PORT_SCAN` - Port scanning activity detected
- `SUSPICIOUS_PORT_ACCESS` - Access to high-risk ports (22, 23, 1433, 3306)

---

### 4. **SQL Injection Attempts**

**Description**: Detection of SQL injection patterns in log entries, indicating attempts to exploit database vulnerabilities.

**Detection Method**:
- **Pattern Matching**: Regex-based detection of SQL injection patterns
- **Patterns Detected**:
  - `UNION SELECT`
  - `OR 1=1`, `OR '1'='1'`
  - `DROP TABLE`, `DELETE FROM`
  - `EXEC`, `EXECUTE`
  - `--` (SQL comments)
  - `;` (SQL statement termination)

**Severity**: **CRITICAL**

**Event Types**:
- `SQL_INJECTION_ATTEMPT` - SQL injection pattern detected

---

### 5. **SUSPICIOUS Activity**

**Description**: General suspicious behavior that doesn't fit into specific attack categories but indicates potential security concerns.

**Detection Criteria**:
- Access to high-risk ports (22, 23, 1433, 3306) without proper authentication
- Unusual traffic patterns
- ML anomaly scores above threshold
- Events flagged by ML but not matching specific attack patterns

**Event Types**:
- `SUSPICIOUS_PORT_ACCESS` - Access to sensitive ports
- `SUSPICIOUS` - General suspicious activity

---

### 6. **NORMAL Activity**

**Description**: Legitimate network traffic and authentication events that don't indicate security threats.

**Event Types**:
- `SSH_LOGIN_SUCCESS` - Successful SSH authentication
- `UFW_TRAFFIC` - Normal firewall traffic
- Other routine system events

---

## Backend Implementation

### API Endpoints

#### 1. **Health & System Endpoints**
- `GET /` - API information
- `GET /health` - Backend status
- `GET /health/websocket` - WebSocket health check
- `GET /health/ml` - ML service status
- `GET /health/notifications` - Notification service status

#### 2. **Log Management APIs**
- `POST /api/logs/ingest` - Ingest logs from various sources
- `GET /api/logs` - Query logs with filters (pagination, sorting, filtering)
- `GET /api/logs/{log_id}` - Get specific log details
- `GET /api/logs/statistics` - Get log statistics
- `GET /api/logs/top-ips` - Get top source IPs by activity

**Query Parameters**:
- `source_ip`, `severity`, `event_type`, `log_source`, `protocol`, `port`
- `start_date`, `end_date`
- `search` - Full-text search
- `page`, `page_size`, `sort_by`, `sort_order`

#### 3. **Threat Detection APIs**
- `GET /api/threats/brute-force` - Get brute force detections
- `GET /api/threats/brute-force/{source_ip}` - Get specific brute force attack details
- `GET /api/threats/brute-force/{source_ip}/timeline` - Get attack timeline
- `GET /api/threats/ddos` - Get DDoS/flood detections
- `GET /api/threats/port-scan` - Get port scan detections
- `GET /api/threats/all` - Get all threat detections (combined)
- `POST /api/threats/brute-force/config` - Configure brute force detection parameters

#### 4. **Dashboard APIs**
- `GET /api/dashboard/summary` - Get dashboard summary (threats, system health, active alerts)
- `GET /api/dashboard/stats` - Get statistics (logs by hour, severity distribution, event types, protocols)
- `GET /api/dashboard/recent-logs` - Get recent log entries
- `GET /api/dashboard/ml-status` - Get ML service status

#### 5. **Report APIs**
- `GET /api/reports/generate` - Generate security reports (daily, weekly, custom)
- `GET /api/reports/list` - List available reports
- `GET /api/reports/{report_id}` - Get specific report
- `GET /api/reports/{report_id}/download` - Download report (PDF, CSV, JSON)

#### 6. **IP Reputation APIs**
- `GET /api/ip-reputation/{ip}` - Get IP reputation from VirusTotal
- `POST /api/ip-reputation/batch` - Batch IP reputation lookup

#### 7. **Alert APIs**
- `GET /api/alerts` - Get active alerts
- `GET /api/alerts/{alert_id}` - Get specific alert
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `POST /api/alerts/{alert_id}/resolve` - Resolve alert
- `GET /api/alerts/history` - Get alert history

#### 8. **Machine Learning APIs**
- `POST /api/ml/predict` - Predict threat type and anomaly score for a log entry
- `GET /api/ml/status` - Get ML service status
- `POST /api/ml/retrain` - Trigger model retraining

#### 9. **WebSocket APIs**
- `WS /ws/logs/live` - Live log streaming endpoint
  - Subscribe to specific log sources: `all`, `auth.log`, `ufw.log`, `iptables`, `syslog`, `sql.log`
  - Real-time log delivery with Redis caching

#### 10. **Export APIs**
- `GET /api/export/logs/csv` - Export logs as CSV
- `GET /api/export/logs/json` - Export logs as JSON
- `GET /api/export/logs/pdf` - Export logs as PDF
- `POST /api/export/logs/selected/pdf` - Export selected logs as PDF

### Log Parsing Services

The backend supports parsing logs from multiple sources:

#### 1. **auth.log Parser**
- Parses SSH authentication logs
- Detects: `SSH_FAILED_LOGIN`, `SSH_LOGIN_SUCCESS`
- Extracts: source IP, username, timestamp

#### 2. **ufw.log Parser**
- Parses UFW (Uncomplicated Firewall) logs
- Extracts: source IP, destination IP, ports, protocol
- Detects: `UFW_TRAFFIC`, `SUSPICIOUS_PORT_ACCESS`

#### 3. **iptables Parser**
- Parses iptables/netfilter logs
- Extracts: connection details, blocked traffic
- Detects: `SUSPICIOUS_PORT_ACCESS`

#### 4. **syslog Parser**
- Parses generic syslog format
- Extracts: timestamps, components, messages
- Flexible parsing for various syslog formats

#### 5. **sql.log Parser**
- Parses SQL-related logs
- Detects: `SQL_INJECTION_ATTEMPT`
- Pattern matching for SQL injection signatures

### Background Services

#### 1. **Alert Monitor Worker**
- Continuously monitors for new threats
- Creates alerts for high-severity threats
- Triggers email notifications

#### 2. **ML Auto-Retrain Worker**
- Periodically retrains ML models with new data
- Improves model accuracy over time
- Runs on configurable schedule

#### 3. **Retention Service**
- Manages log data retention policies
- Archives old logs
- Cleans up expired data

### Notification Services

#### Email Notifications
- **SendGrid Integration**: Sends email alerts for critical threats
- **Recipients**: Configurable list of email addresses
- **Rate Limiting**: Prevents email spam (60-minute cooldown per alert type)
- **Alert Types**: Brute force, DDoS, port scans, high-severity threats

---

## Frontend Implementation

### Pages & Components

#### 1. **Dashboard Page** (`/dashboard`)
**Features**:
- **Summary Cards**: Total logs, active threats, security score, system health
- **Active Alerts**: Real-time alert display
- **Threat Summary**: Breakdown by type (brute force, DDoS, port scan) and severity
- **Charts**:
  - Logs over time (line chart)
  - Severity distribution (pie/bar chart)
  - Event types distribution
  - Protocol usage
- **Top Source IPs Table**: Most active IPs
- **Recent Activity Timeline**: Latest log entries
- **ML Status Indicator**: Shows ML availability
- **Auto-refresh**: Configurable refresh intervals

#### 2. **Logs Page** (`/logs`)
**Features**:
- **Log Table**: Sortable, filterable table of all logs
- **Filters Panel**:
  - Date range picker
  - Source IP filter
  - Severity filter
  - Event type filter
  - Log source filter
  - Protocol filter
  - Port filter
  - Search bar (full-text search)
- **Live Monitoring Mode**:
  - Real-time WebSocket connection
  - Log source tabs (all, auth.log, ufw.log, iptables, syslog, sql.log)
  - Raw log viewer with terminal-style display
  - Auto-scroll toggle
  - Clear logs button
  - Connection status indicator
- **Log Details Modal**:
  - Complete log information
  - **ML Analysis Section**:
    - "Analyze" button for on-demand ML prediction
    - Risk score (0-100) with progress bar
    - Anomaly score (0-1) with visualization
    - Predicted label (BRUTE_FORCE, DDOS, PORT_SCAN, NORMAL, etc.)
    - Confidence score (0-1)
    - ML reasoning (detailed analysis)
- **Pagination**: Configurable page size (25, 50, 100, 200)
- **Export Options**: CSV, JSON, PDF
- **Bulk Actions**: Select multiple logs for export

#### 3. **Threats Page** (`/threats`)
**Features**:
- **Threat List**: All detected threats (brute force, DDoS, port scans)
- **Threat Cards**: Visual cards showing:
  - Source IP
  - Threat type
  - Severity badge
  - Attack statistics
  - ML enrichment (if available)
  - VirusTotal reputation
- **Threat Details Modal**:
  - Complete attack information
  - Attack timeline
  - ML insights section
  - IP reputation details
- **Filters**: Filter by threat type, severity, date range
- **Sorting**: Sort by severity, timestamp, attack count
- **ML Status**: Shows ML availability and last error (if any)

#### 4. **Reports Page** (`/reports`)
**Features**:
- **Report Generation**:
  - Daily reports
  - Weekly reports
  - Custom date range reports
- **Report List**: View all generated reports
- **Report Details**: View report contents
- **Download Options**: PDF, CSV, JSON formats
- **Report Contents**:
  - Executive summary
  - Threat statistics
  - Top threats
  - Log statistics
  - Charts and visualizations
  - Recommendations

### Reusable Components

#### Charts
- `LogsOverTimeChart` - Line chart for log trends
- `SeverityDistributionChart` - Pie/bar chart for severity breakdown
- `EventTypesChart` - Bar chart for event type distribution
- `ProtocolUsageChart` - Pie chart for protocol usage

#### Tables
- `LogsTable` - Sortable, filterable log table
- `TopIPsTable` - Top source IPs display

#### Common Components
- `SummaryCard` - Dashboard summary cards
- `AlertCard` - Alert display cards
- `LogFilterPanel` - Advanced filtering panel
- `LogDetailsModal` - Log detail view modal
- `ThreatDetailsModal` - Threat detail view modal

#### Timeline
- `RecentActivityTimeline` - Timeline view of recent logs

### State Management

- **React Query**: Data fetching, caching, and synchronization
- **WebSocket Hooks**: Real-time log streaming
- **Local State**: UI state management with React hooks

---

## Machine Learning Engine

### Model Architecture

#### 1. **Anomaly Detector (Isolation Forest)**
- **Type**: Unsupervised learning
- **Purpose**: Detect unusual patterns in logs
- **Output**: Anomaly score (0-1)
  - 0 = Normal
  - 1 = Highly anomalous
- **Features**: 47 engineered features from log data

#### 2. **Threat Classifier (Random Forest)**
- **Type**: Supervised learning
- **Purpose**: Classify threats into categories
- **Output**: 
  - Predicted label (BRUTE_FORCE, DDOS, PORT_SCAN, NORMAL, SUSPICIOUS, SQL_INJECTION)
  - Confidence score (0-1)
  - Probability distribution across all classes
- **Features**: Same 47 features as anomaly detector

### Feature Engineering

The ML engine extracts **47 features** from log entries:

#### IP-Based Features
- IP hash (anonymized)
- IP frequency count
- IP repetition indicator
- IP frequency category (low/medium/high)
- IP presence indicator

#### Time-Based Features
- Hour of day (0-23)
- Day of week (0-6)
- Month (1-12)
- Cyclical encoding (sin/cos) for hour, day, month
- Weekend indicator
- Business hours indicator
- Night/morning/afternoon/evening indicators

#### Event-Based Features
- EventId hash
- Component hash
- Content length
- Content word count
- Template length
- Authentication failure patterns
- Session event indicators
- Connection event indicators
- Component-specific flags (sshd, ftpd, kernel, su)

#### Frequency-Based Features
- Event frequency per IP
- Unique events per IP
- Total events per IP
- Event frequency overall
- Component frequency
- Events per hour
- Burst detection (multiple events in short time)
- Burst count

### ML Service Integration

#### Prediction API
```python
POST /api/ml/predict
{
  "raw_log": "...",
  "timestamp": "...",
  "log_source": "auth.log",
  "event_type": "SSH_FAILED_LOGIN",
  "severity_hint": "HIGH",
  "threat_type_hint": "BRUTE_FORCE",  # Optional
  "source_ip": "192.168.1.100"
}
```

**Response**:
```json
{
  "ml_available": true,
  "anomaly_score": 0.85,
  "predicted_label": "BRUTE_FORCE",
  "confidence": 0.92,
  "risk_score": 88.5,
  "reasoning": [
    "High anomaly score (0.85) indicates unusual pattern",
    "Event type matches BRUTE_FORCE pattern",
    "Multiple failed login attempts detected",
    "High confidence (92%) in BRUTE_FORCE classification"
  ]
}
```

#### Fallback Mode
If ML models are unavailable:
- Uses rule-based heuristics
- Provides basic threat classification
- Returns lower confidence scores
- Indicates fallback mode in response

### Model Training

#### Training Pipeline
1. **Data Loading**: Loads structured log dataset
2. **Data Labeling**: Labels logs with threat types
3. **Feature Extraction**: Extracts 47 features
4. **Model Training**:
   - Isolation Forest for anomaly detection
   - Random Forest for threat classification
5. **Model Evaluation**: Calculates accuracy, precision, recall
6. **Model Persistence**: Saves models as `.pkl` files

#### Auto-Retraining
- Periodic retraining with new data
- Improves accuracy over time
- Configurable retraining schedule
- Background worker process

---

## Key Features & Capabilities

### 1. **Multi-Source Log Ingestion**
- Supports 5+ log formats (auth.log, ufw.log, iptables, syslog, sql.log)
- Unified parsing and storage
- Automatic timestamp extraction
- Event type detection

### 2. **Real-Time Monitoring**
- WebSocket-based live log streaming
- Source-specific subscriptions
- Redis caching for instant log retrieval
- Connection status monitoring

### 3. **Advanced Threat Detection**
- Rule-based detection algorithms
- ML-enhanced classification
- Configurable detection thresholds
- Multi-level severity classification

### 4. **IP Reputation Integration**
- VirusTotal API integration
- Reputation scoring
- Malicious IP identification
- Historical reputation data

### 5. **Automated Alerting**
- Email notifications via SendGrid
- Configurable alert thresholds
- Rate limiting to prevent spam
- Alert acknowledgment and resolution

### 6. **Comprehensive Reporting**
- Daily, weekly, and custom reports
- PDF, CSV, JSON export formats
- Executive summaries
- Detailed threat analysis
- Charts and visualizations

### 7. **Data Export**
- Export logs in multiple formats
- Filtered exports
- Bulk export of selected logs
- Scheduled report generation

### 8. **Search & Filtering**
- Full-text search across logs
- Advanced filtering (IP, severity, event type, date range, etc.)
- Sortable columns
- Pagination support

### 9. **Security Score Calculation**
- Dynamic security score (0-100)
- Based on threat count and severity
- Real-time updates
- Visual indicators (Good/Fair/Poor)

### 10. **System Health Monitoring**
- Database status checks
- ML service availability
- Notification service status
- WebSocket connection health

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.8+)
- **Database**: MongoDB Atlas
- **Cache**: Redis
- **ML Libraries**: scikit-learn, pandas, numpy
- **Email Service**: SendGrid API
- **IP Reputation**: VirusTotal API
- **WebSocket**: FastAPI WebSocket support

### Frontend
- **Framework**: React 19.2.0
- **Build Tool**: Vite
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router DOM
- **Charts**: Recharts
- **Tables**: TanStack Table
- **Styling**: Tailwind CSS
- **Icons**: React Icons (Feather Icons)

### ML Engine
- **Language**: Python
- **ML Framework**: scikit-learn
- **Models**:
  - Isolation Forest (Anomaly Detection)
  - Random Forest (Classification)
- **Data Processing**: pandas, numpy
- **Model Persistence**: joblib

### Infrastructure
- **Version Control**: Git
- **Package Management**: 
  - Backend: pip, requirements.txt
  - Frontend: npm, package.json
- **Development**: 
  - Backend: Python virtual environment
  - Frontend: Node.js, Vite dev server

---

## Summary

This Firewall Log Analyzer project is a comprehensive security monitoring solution that combines:

1. **Rule-Based Detection**: Fast, reliable detection of known attack patterns (brute force, DDoS, port scans)
2. **Machine Learning**: Advanced anomaly detection and threat classification to identify novel attacks
3. **Real-Time Monitoring**: Live log streaming for immediate threat visibility
4. **User-Friendly Interface**: Intuitive dashboards and detailed threat analysis
5. **Automated Alerting**: Email notifications for critical security events
6. **Comprehensive Reporting**: Automated security reports for compliance and analysis

The system successfully detects and classifies **6 main threat types**:
- **BRUTE_FORCE**: Unauthorized login attempts
- **DDOS**: Network flood attacks
- **PORT_SCAN**: Reconnaissance scanning
- **SQL_INJECTION**: Database exploitation attempts
- **SUSPICIOUS**: General suspicious activity
- **NORMAL**: Legitimate traffic

With **47 ML features** extracted from logs, the system provides accurate threat classification with confidence scores, enabling security teams to prioritize and respond to threats effectively.

---

**Document Version**: 1.0.0  
**Last Updated**: January 2025

