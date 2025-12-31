# Firewall Log Analyzer and Monitoring Tool
## PPT Content for Review Presentation

---

## 1. Introduction

### Project Overview
- **Project Name**: Firewall Log Analyzer and Monitoring Tool
- **Type**: Real-Time Cybersecurity Monitoring System
- **Purpose**: Automated analysis and monitoring of firewall logs to detect suspicious activities and potential cyberattacks

### Domain
- **Primary Domain**: Cybersecurity & Network Security
- **Sub-domains**: 
  - Log Analysis & Monitoring
  - Threat Detection
  - Network Security Operations
  - Intrusion Detection Systems (IDS)

### Motivation
- **Problem**: Network engineers spend excessive time manually analyzing firewall logs using complex CLI commands (`cat`, `grep`, `tail -f`)
- **Impact**: Delayed threat detection, inefficient monitoring, human error in log analysis
- **Solution**: Automated real-time log analysis with ML-based threat detection and user-friendly dashboard
- **Value**: Enables instant threat identification, reduces response time, and provides actionable security insights

---

## 2. Problem Identification

### Background
- Linux Virtual Machines (VMs) running critical applications generate continuous firewall logs
- Logs include:
  - Incoming IP addresses
  - Port access attempts
  - Failed SSH login attempts
  - SQL server access attempts
  - Suspicious traffic patterns
- Traditional monitoring requires manual log inspection on each VM

### Current Challenges
1. **Manual Log Analysis**: Network engineers must log into each VM and use CLI commands
2. **Time-Consuming**: Analyzing thousands of log lines manually is inefficient
3. **Error-Prone**: Human analysis can miss critical security events
4. **No Real-Time Monitoring**: Delayed threat detection increases security risk
5. **Storage Management**: Log files grow continuously, requiring manual cleanup
6. **Lack of Centralized View**: No unified dashboard for all security events

### Need for Project
- **Automation**: Replace manual log analysis with automated processing
- **Real-Time Detection**: Immediate identification of attack patterns
- **Centralized Monitoring**: Single dashboard for all security events
- **Intelligent Analysis**: ML-based detection of unknown attack patterns
- **Automated Storage Management**: Smart log retention to prevent database overflow
- **Actionable Alerts**: Email notifications for critical security events

---

## 3. Problem Statement & Objectives

### Problem Statement
"Firewall logs are generated continuously and are difficult to analyze manually. This leads to delayed threat detection and inefficient security monitoring. There is a need for an automated solution that can collect, analyze, and monitor firewall logs in real-time to detect suspicious activities and potential cyberattacks, while providing a user-friendly interface for network engineers."

### Objectives
1. **Automated Log Collection**: Automatically collect firewall logs from the local VM (auth.log, ufw.log, iptables, syslog)
2. **Real-Time Analysis**: Process and analyze logs in real-time using rule-based and ML-based detection
3. **Threat Detection**: Identify attack patterns including:
   - Brute force SSH attacks
   - Port scanning attempts
   - SQL injection attempts
   - Unauthorized access attempts
   - Suspicious IP behavior
4. **Intelligent Storage**: Implement automated log retention in MongoDB (delete oldest logs when limit reached)
5. **Real-Time Alerting**: Send email alerts for critical security events
6. **User-Friendly Dashboard**: Provide web-based interface with filtering and visualization
7. **Report Generation**: Export logs as PDF reports with color-coded severity levels

---

## 4. Literature Survey

### Existing Systems
1. **ELK Stack (Elasticsearch, Logstash, Kibana)**
   - Pros: Powerful search, visualization, scalable
   - Cons: Complex setup, resource-intensive, requires expertise
   - Limitation: Not specifically designed for firewall log analysis

2. **Splunk**
   - Pros: Enterprise-grade, comprehensive analytics
   - Cons: Expensive licensing, complex configuration
   - Limitation: Cost-prohibitive for small to medium organizations

3. **Graylog**
   - Pros: Open-source, good log management
   - Cons: Requires significant infrastructure, complex setup
   - Limitation: Lacks specialized firewall log analysis features

4. **Manual CLI Tools (grep, tail, awk)**
   - Pros: Available on all Linux systems, no additional software
   - Cons: Time-consuming, error-prone, no real-time alerts
   - Limitation: Not suitable for continuous monitoring

### Related Work
- **Research Papers**:
  - "Machine Learning for Network Intrusion Detection" - Various ML approaches for IDS
  - "Anomaly Detection in Network Logs" - Isolation Forest for log analysis
  - "Real-Time Security Event Correlation" - Rule-based detection systems

### Limitations of Existing Solutions
1. **Complexity**: Most solutions require extensive setup and maintenance
2. **Cost**: Enterprise solutions are expensive
3. **Specialization**: Generic log analyzers lack firewall-specific features
4. **Real-Time Processing**: Limited real-time threat detection capabilities
5. **Storage Management**: No automated log retention mechanisms
6. **User Interface**: Complex interfaces not suitable for network engineers

### Our Contribution
- **Hybrid Detection**: Combines rule-based and ML-based (Isolation Forest) detection
- **Automated Retention**: Smart MongoDB-based log retention (auto-delete oldest logs)
- **Firewall-Specific**: Designed specifically for firewall log analysis
- **Real-Time Processing**: Continuous log monitoring with instant threat detection
- **User-Friendly**: Modern React.js dashboard replacing CLI commands

---

## 5. Proposed System

### Overview
A comprehensive firewall log analysis system that:
- Runs on the local VM and collects logs from multiple sources (auth.log, ufw.log, iptables, syslog)
- Processes logs in real-time using Python backend (FastAPI)
- Detects threats using rule-based patterns and ML algorithms (Isolation Forest)
- Stores logs in MongoDB Atlas with automated retention
- Provides React.js dashboard for visualization and filtering
- Sends email alerts for critical security events
- Generates PDF reports for documentation

### Key Features
1. **Multi-Source Log Collection**
   - Authentication logs (SSH, login attempts)
   - UFW firewall logs
   - iptables/netfilter logs
   - System logs (syslog)
   - SQL access logs

2. **Real-Time Threat Detection**
   - Brute force attack detection (repeated failed SSH attempts)
   - Port scanning detection (multiple port access attempts)
   - SQL attack detection (unauthorized database access)
   - Anomaly detection using Isolation Forest ML algorithm

3. **Automated Log Retention**
   - MongoDB Atlas storage (512MB/1GB cluster)
   - Automatic deletion of oldest logs when limit reached (5-10 MB batches)
   - Continuous monitoring without manual cleanup

4. **Advanced Filtering**
   - Date/Time filters (daily, weekly, monthly, yearly)
   - IP address filtering
   - Port filtering
   - Severity-based filtering
   - Event type filtering

5. **Real-Time Alerting**
   - Email notifications for critical events
   - Instant alerts for brute force attacks
   - Port scanning notifications
   - Unauthorized access alerts

6. **PDF Report Generation**
   - Color-coded logs (Green: Safe, Red: Attack/Suspicious)
   - Filtered reports
   - Export for security audits and documentation

7. **IP Reputation Integration**
   - VirusTotal API integration
   - Enhanced threat severity based on IP reputation

### Advantages
1. **Automation**: Eliminates manual log analysis
2. **Real-Time**: Instant threat detection and alerts
3. **Cost-Effective**: Open-source stack, minimal infrastructure
4. **User-Friendly**: Web dashboard replaces complex CLI commands
5. **Scalable**: MongoDB Atlas handles large log volumes
6. **Intelligent**: ML-based detection identifies unknown attack patterns
7. **Comprehensive**: Multiple log sources for complete security visibility
8. **Documentation-Ready**: PDF reports for audits and management

---

## 6. System Architecture / Methodology

### Architecture Diagram Components
```
┌─────────────────────────────────────────────────────────────┐
│                    Local Linux VM                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  auth.log    │  │   ufw.log    │  │  kern.log    │      │
│  │  (SSH logs)  │  │  (Firewall)  │  │ (iptables)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │ Log Ingestor │                          │
│                    │  (Real-Time)  │                          │
│                    └──────┬───────┘                          │
└───────────────────────────┼─────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  FastAPI Backend│
                    │  ┌──────────┐  │
                    │  │  Parser  │  │
                    │  │  Service │  │
                    │  └────┬─────┘  │
                    │  ┌────▼─────┐  │
                    │  │   ML     │  │
                    │  │ Detection│  │
                    │  └────┬─────┘  │
                    │  ┌────▼─────┐  │
                    │  │  Alert   │  │
                    │  │  Service │  │
                    │  └────┬─────┘  │
                    └───────┼────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
│   MongoDB    │   │  Email Service  │  │  React.js   │
│    Atlas     │   │   (SMTP)        │  │  Frontend   │
│              │   │                 │  │  Dashboard  │
│ ┌──────────┐ │   └─────────────────┘  └─────────────┘
│ │ Logs     │ │
│ │ Storage  │ │
│ └──────────┘ │
│ ┌──────────┐ │
│ │Retention │ │
│ │ Worker   │ │
│ └──────────┘ │
└──────────────┘
```

### Workflow
1. **Log Collection Phase**
   - Log ingestor monitors local VM log files in real-time
   - Reads from: `/var/log/auth.log`, `/var/log/ufw.log`, `/var/log/kern.log`, `/var/log/syslog`
   - Uses tail-like functionality to follow log files

2. **Parsing Phase**
   - Raw log lines are parsed by appropriate parser (auth, ufw, iptables, syslog)
   - Extracts: timestamp, source IP, destination port, protocol, event type
   - Normalizes log format for storage

3. **Detection Phase**
   - **Rule-Based Detection**: Checks for known attack patterns
     - Multiple failed SSH attempts → Brute Force
     - Multiple port access → Port Scanning
     - SQL port access (1433, 3306, 5432) → SQL Attack
   - **ML-Based Detection**: Isolation Forest algorithm identifies anomalies
     - Unsupervised learning detects unknown attack patterns
     - Reduces false positives

4. **Storage Phase**
   - Parsed logs stored in MongoDB Atlas
   - Indexes created for fast querying (timestamp, IP, severity, port)
   - Retention worker monitors database size
   - Automatically deletes oldest logs when limit exceeded

5. **Alerting Phase**
   - Critical events trigger email alerts
   - Alerts include: IP address, event type, timestamp, severity

6. **Visualization Phase**
   - React.js dashboard displays logs in real-time
   - Filters applied for date, time, IP, port, severity
   - Statistics and charts show attack trends

7. **Reporting Phase**
   - Users can export filtered logs as PDF
   - Color-coded by severity (Green: Safe, Red: Attack)

---

## 7. Module Description

### Module 1: Log Collection Module
**Purpose**: Real-time collection of firewall logs from local VM

**Components**:
- Log Ingestor Service
- File Monitoring (tail-like functionality)
- Multi-threaded log reading

**Functionality**:
- Monitors multiple log files simultaneously
- Reads logs in real-time as they are written
- Handles log file rotation
- Supports: auth.log, ufw.log, kern.log, syslog, messages

**Input**: Raw log files from `/var/log/`
**Output**: Log lines to parsing module

---

### Module 2: Log Parsing Module
**Purpose**: Parse raw log lines into structured format

**Components**:
- Auth Log Parser (SSH events)
- UFW Log Parser (firewall rules)
- iptables Parser (netfilter logs)
- Syslog Parser (general system logs)
- SQL Parser (database access logs)

**Functionality**:
- Identifies log source automatically
- Extracts: timestamp, IP addresses, ports, protocols, usernames
- Normalizes different log formats
- Handles parsing errors gracefully

**Input**: Raw log lines
**Output**: Structured log objects

---

### Module 3: Threat Detection Module
**Purpose**: Detect security threats and attacks

**Components**:
- Rule-Based Detection Engine
- ML-Based Detection (Isolation Forest)
- Brute Force Detector
- Port Scan Detector
- SQL Attack Detector

**Functionality**:
- **Rule-Based**: Predefined patterns for known attacks
  - Brute Force: 5+ failed SSH attempts from same IP
  - Port Scanning: Access to 10+ different ports from same IP
  - SQL Attack: Access to SQL ports (1433, 3306, 5432)
- **ML-Based**: Isolation Forest algorithm
  - Unsupervised anomaly detection
  - Identifies unknown attack patterns
  - Reduces false positives

**Input**: Parsed log objects
**Output**: Logs with severity levels (CRITICAL, HIGH, MEDIUM, LOW) and event types

---

### Module 4: Storage & Retention Module
**Purpose**: Store logs in MongoDB with automated retention

**Components**:
- MongoDB Atlas Connection
- Log Storage Service
- Retention Worker
- Database Indexes

**Functionality**:
- Stores parsed logs in MongoDB
- Creates indexes for fast queries (timestamp, IP, severity, port)
- Retention worker monitors database size
- Automatically deletes oldest logs when size exceeds limit (450MB default)
- Deletes in batches (2000 documents) until under limit

**Input**: Parsed and analyzed logs
**Output**: Stored logs in MongoDB, retention statistics

---

### Module 5: Alerting Module
**Purpose**: Send real-time email alerts for critical events

**Components**:
- Email Service (SMTP)
- Alert Configuration
- Alert Queue

**Functionality**:
- Monitors logs for critical events (CRITICAL, HIGH severity)
- Sends email alerts to administrators
- Alert includes: IP address, event type, timestamp, severity, raw log
- Configurable alert thresholds

**Input**: High-severity log events
**Output**: Email notifications

---

### Module 6: API & Backend Module
**Purpose**: RESTful API for frontend and external access

**Components**:
- FastAPI Application
- Log Query Service
- Statistics Service
- Export Service
- Authentication Middleware

**Functionality**:
- RESTful endpoints for log retrieval
- Pagination and filtering support
- Statistics aggregation (top IPs, top ports, summary)
- PDF/CSV/JSON export
- API key authentication
- Rate limiting

**Input**: HTTP requests
**Output**: JSON responses, file exports

---

### Module 7: Frontend Dashboard Module
**Purpose**: User-friendly web interface for log visualization

**Components**:
- React.js Application
- Log Table Component
- Filter Components
- Statistics Dashboard
- Chart Components

**Functionality**:
- Real-time log display
- Advanced filtering (date, time, IP, port, severity, event type)
- Statistics visualization (charts, graphs)
- Top IPs and ports display
- PDF export functionality
- Responsive design

**Input**: API responses
**Output**: Interactive web dashboard

---

## 8. Technology Stack

### Languages
- **Python 3.9+**: Backend development, ML algorithms, log parsing
- **JavaScript (ES6+)**: Frontend development
- **TypeScript** (optional): Type-safe frontend development

### Tools & Frameworks
**Backend**:
- **FastAPI**: High-performance Python web framework
- **Pydantic**: Data validation and settings management
- **PyMongo**: MongoDB driver for Python
- **Scikit-learn**: Machine learning library (Isolation Forest)
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing

**Frontend**:
- **React.js**: Modern UI library
- **HTML5/CSS3**: Markup and styling
- **Axios**: HTTP client for API calls
- **Chart.js / Recharts**: Data visualization

**Database**:
- **MongoDB Atlas**: Cloud-hosted NoSQL database
- **MongoDB**: Document-based storage for logs

**Security & Monitoring**:
- **VirusTotal API**: IP reputation checking
- **SMTP**: Email alerting
- **API Key Authentication**: Secure API access

**Development Tools**:
- **Git**: Version control
- **Docker** (optional): Containerization
- **Uvicorn**: ASGI server for FastAPI

### Database
- **MongoDB Atlas**: 
  - Cloud-hosted (512MB or 1GB free tier)
  - Document-based storage
  - Automatic backups
  - Indexes for fast queries
  - Automated retention support

---

## 9. System Requirements

### Hardware Requirements
**Minimum**:
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 10 GB free space
- **Network**: Internet connection for MongoDB Atlas

**Recommended**:
- **CPU**: 4 cores, 2.5 GHz+
- **RAM**: 8 GB
- **Storage**: 20 GB free space
- **Network**: Stable internet connection

### Software Requirements
**Operating System**:
- Linux (Ubuntu 20.04+, Debian 10+, CentOS 7+)
- Windows 10+ (for development)
- macOS (for development)

**Backend**:
- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (venv)

**Frontend**:
- Node.js 16+ and npm
- Modern web browser (Chrome, Firefox, Edge, Safari)

**Database**:
- MongoDB Atlas account (free tier available)
- Internet connection for database access

**System Logs**:
- Access to `/var/log/` directory (requires appropriate permissions)
- Log files: auth.log, ufw.log, kern.log, syslog

**Email Service** (for alerts):
- SMTP server credentials (Gmail, SendGrid, etc.)

---

## 10. Project Plan & Timeline

### Gantt Chart Overview

**Phase 1: Planning & Design (Weeks 1-2)**
- Requirements gathering
- System design
- Technology stack selection
- Database schema design

**Phase 2: Backend Development (Weeks 3-6)**
- Week 3-4: Log collection and parsing modules
- Week 5: Threat detection module (rule-based)
- Week 6: ML integration (Isolation Forest)

**Phase 3: Database & Storage (Weeks 7-8)**
- Week 7: MongoDB setup and integration
- Week 8: Log retention implementation

**Phase 4: API Development (Weeks 9-10)**
- Week 9: FastAPI endpoints
- Week 10: Authentication and security

**Phase 5: Frontend Development (Weeks 11-14)**
- Week 11-12: React.js dashboard setup
- Week 13: Filtering and visualization
- Week 14: PDF export functionality

**Phase 6: Alerting & Integration (Weeks 15-16)**
- Week 15: Email alerting system
- Week 16: VirusTotal API integration

**Phase 7: Testing & Deployment (Weeks 17-18)**
- Week 17: Unit testing, integration testing
- Week 18: Deployment and documentation

### Task Allocation
- **Backend Development**: Python developer
- **Frontend Development**: React.js developer
- **ML Integration**: Data scientist / ML engineer
- **Database Design**: Backend developer
- **Testing**: QA engineer / Developer
- **Documentation**: Technical writer / Developer

---

## 11. Current Status

### Completed Work
- ✅ Project planning and requirements gathering
- ✅ Technology stack selection (FastAPI + React.js + MongoDB)
- ✅ System architecture design
- ✅ Database schema design
- ✅ Literature survey and research on existing systems
- ✅ ML algorithm selection (Isolation Forest)

### In Progress
- 🔄 Gathering required details and specifications
- 🔄 Finalizing log sources and collection methods
- 🔄 Setting up development environment
- 🔄 Preparing for implementation phase

### Next Steps
1. **Environment Setup**
   - Install Python dependencies
   - Set up MongoDB Atlas cluster
   - Configure development environment
   - Set up React.js project structure

2. **Backend Implementation**
   - Implement log collection module
   - Develop log parsers (auth, ufw, iptables, syslog)
   - Build threat detection engine
   - Integrate ML model (Isolation Forest)

3. **Database Integration**
   - Connect to MongoDB Atlas
   - Implement log storage
   - Set up automated retention worker
   - Create database indexes

4. **API Development**
   - Develop FastAPI endpoints
   - Implement filtering and pagination
   - Add authentication middleware
   - Create export functionality (PDF, CSV, JSON)

5. **Frontend Development**
   - Build React.js dashboard
   - Implement log table with filtering
   - Add statistics visualization
   - Create PDF export feature

6. **Testing & Deployment**
   - Unit testing
   - Integration testing
   - Performance testing
   - Deployment to production

---

## 12. Conclusion

### Summary of Review I
This presentation outlined the **Firewall Log Analyzer and Monitoring Tool**, a comprehensive cybersecurity solution designed to automate firewall log analysis and provide real-time threat detection.

**Key Highlights**:
- **Problem Solved**: Replaces manual CLI-based log analysis with automated real-time monitoring
- **Innovation**: Hybrid detection approach combining rule-based and ML-based (Isolation Forest) methods
- **Practical Value**: Addresses real-world network security challenges faced by network engineers
- **Technology**: Modern stack (FastAPI, React.js, MongoDB) ensuring scalability and performance
- **Automation**: Smart log retention eliminates manual database management

**Project Status**: Currently in planning and design phase, ready to begin implementation.

**Expected Outcomes**:
- Automated real-time log monitoring
- Instant threat detection and alerting
- User-friendly dashboard replacing CLI commands
- Comprehensive security visibility
- Reduced response time to security incidents

**Next Milestone**: Begin backend implementation and log collection module development.

---

## 13. References

### Research Papers
1. Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). "Isolation Forest." *2008 Eighth IEEE International Conference on Data Mining*.
2. Garcia-Teodoro, P., et al. (2009). "Anomaly-based network intrusion detection: Techniques, systems and challenges." *Computers & Security*.
3. Hodge, V., & Austin, J. (2004). "A Survey of Outlier Detection Methodologies." *Artificial Intelligence Review*.

### Journals
1. *IEEE Transactions on Network and Service Management*
2. *Computers & Security Journal*
3. *Journal of Network and Computer Applications*

### Websites & Documentation
1. FastAPI Documentation: https://fastapi.tiangolo.com/
2. MongoDB Atlas: https://www.mongodb.com/cloud/atlas
3. React.js Documentation: https://react.dev/
4. Scikit-learn Documentation: https://scikit-learn.org/
5. VirusTotal API: https://developers.virustotal.com/
6. UFW Documentation: https://help.ubuntu.com/community/UFW
7. iptables Documentation: https://www.netfilter.org/documentation/

### Related Projects
1. ELK Stack: https://www.elastic.co/elk-stack
2. Graylog: https://www.graylog.org/
3. Splunk: https://www.splunk.com/

---

## Additional Notes for Presentation

### Key Points to Emphasize
1. **Real-World Application**: Solves actual problems faced by network engineers
2. **Automation**: Eliminates manual, time-consuming log analysis
3. **Intelligence**: ML-based detection identifies unknown threats
4. **User-Friendly**: Modern dashboard replaces complex CLI commands
5. **Cost-Effective**: Open-source stack, minimal infrastructure costs
6. **Scalable**: MongoDB Atlas handles large log volumes
7. **Comprehensive**: Multiple log sources for complete security visibility

### Demo Scenarios (For Future Presentations)
1. Real-time log ingestion demonstration
2. Brute force attack detection
3. Port scanning detection
4. PDF report generation
5. Email alert demonstration
6. Dashboard filtering and visualization

### Viva Questions Preparation
1. **Why FastAPI + React instead of MERN?**
   - ML algorithms require Python
   - FastAPI provides high performance and async support
   - Single backend reduces complexity

2. **How does Isolation Forest work?**
   - Unsupervised anomaly detection algorithm
   - Creates isolation trees to identify outliers
   - No labeled data required

3. **How does log retention work?**
   - Monitors MongoDB collection size
   - Deletes oldest logs (by timestamp) when limit exceeded
   - Deletes in batches until under limit

4. **What logs are collected?**
   - auth.log (SSH, authentication)
   - ufw.log (UFW firewall)
   - kern.log (iptables/netfilter)
   - syslog (general system logs)

---

**End of PPT Content**

