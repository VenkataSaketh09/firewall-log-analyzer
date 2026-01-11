# 🔥 Firewall Log Analyzer - Backend Learning Guide

> **For FastAPI Beginners**: This guide provides a step-by-step learning path to understand the backend codebase, starting from FastAPI fundamentals to advanced features.

---

## 📋 Table of Contents

1. [FastAPI Application Setup](#1-fastapi-application-setup)
2. [Configuration Management](#2-configuration-management)
3. [Database Connection](#3-database-connection)
4. [Data Models & Schemas](#4-data-models--schemas)
5. [Basic API Routes](#5-basic-api-routes)
6. [Services Layer](#6-services-layer)
7. [Middleware](#7-middleware)
8. [Log Ingestion](#8-log-ingestion)
9. [Threat Detection](#9-threat-detection)
10. [Alerts & Notifications](#10-alerts--notifications)
11. [ML Integration](#11-ml-integration)
12. [WebSocket & Real-time](#12-websocket--real-time)
13. [Advanced Features](#13-advanced-features)

---

## 🎯 Learning Path Flowchart

```
START
  │
  ├─► 1. FastAPI Application Setup (main.py)
  │     └─► Understanding app initialization, routers, middleware
  │
  ├─► 2. Configuration (config.py)
  │     └─► Environment variables, validation
  │
  ├─► 3. Database Connection (db/mongo.py)
  │     └─► MongoDB setup, collections, indexes
  │
  ├─► 4. Data Models & Schemas
  │     ├─► models/log_model.py (data structure)
  │     └─► schemas/*.py (API request/response validation)
  │
  ├─► 5. Basic API Routes (routes/logs.py)
  │     └─► GET/POST endpoints, query parameters, response models
  │
  ├─► 6. Services Layer (services/*.py)
  │     └─► Business logic separation
  │
  ├─► 7. Middleware (middleware/*.py)
  │     └─► CORS, rate limiting, authentication
  │
  ├─► 8. Log Ingestion
  │     ├─► routes/logs.py (ingest endpoint)
  │     └─► services/log_parser_service.py
  │
  ├─► 9. Threat Detection
  │     ├─► routes/threats.py
  │     └─► services/*_detection.py
  │
  ├─► 10. Alerts & Notifications
  │     ├─► routes/alerts.py
  │     └─► services/alert_*.py
  │
  ├─► 11. ML Integration
  │     ├─► routes/ml.py
  │     └─► services/ml_*.py
  │
  ├─► 12. WebSocket & Real-time
  │     ├─► routes/websocket.py
  │     └─► services/raw_log_broadcaster.py
  │
  └─► 13. Advanced Features
        ├─► IP Blocking
        ├─► IP Reputation
        ├─► Reports
        └─► Dashboard
```

---

## 1. FastAPI Application Setup

**🎯 Goal**: Understand how FastAPI application is initialized and structured.

**📁 Files to Study**:
- `app/main.py` ⭐ **START HERE**

**🔍 What to Focus On**:

1. **FastAPI App Creation** (lines 34-38)
   - How `FastAPI()` is instantiated
   - Title, description, version parameters

2. **Middleware Setup** (lines 41-50)
   - `CORSMiddleware` - allows frontend to connect
   - `RateLimitMiddleware` - prevents API abuse
   - Order matters: middleware executes in reverse order

3. **Router Registration** (lines 53-61)
   - How routes are included with `app.include_router()`
   - Prefix and tags organization

4. **Startup Events** (lines 64-124)
   - `@app.on_event("startup")` decorator
   - Service initialization order
   - Background workers starting

5. **Health Check Endpoints** (lines 127-148)
   - Simple GET endpoints
   - Status checking pattern

**💡 FastAPI Concepts to Learn**:
- `FastAPI()` - Main application class
- `APIRouter` - Modular route organization
- `@app.on_event()` - Lifecycle hooks
- `@router.get()`, `@router.post()` - HTTP method decorators

**✅ Checkpoint**: Can you explain what happens when the server starts?

---

## 2. Configuration Management

**🎯 Goal**: Understand how environment variables and configuration are handled.

**📁 Files to Study**:
- `app/config.py`

**🔍 What to Focus On**:

1. **Environment Variable Loading** (line 7)
   - `python-dotenv` library usage
   - `.env` file reading

2. **Validation Function** (lines 10-40)
   - Required vs optional variables
   - Error handling with `ValueError`

3. **Configuration Structure**
   - Database URI
   - API keys
   - Feature flags

**💡 FastAPI Concepts to Learn**:
- Environment variable management
- Configuration validation patterns

**✅ Checkpoint**: Where are environment variables loaded from?

---

## 3. Database Connection

**🎯 Goal**: Understand MongoDB connection setup and database structure.

**📁 Files to Study**:
- `app/db/mongo.py`

**🔍 What to Focus On**:

1. **MongoDB Client Setup** (lines 8-11)
   - `MongoClient` initialization
   - Database and collection references

2. **Collection Definitions** (lines 12-24)
   - Different collections for different data types
   - Naming conventions

3. **Index Creation** (lines 27-106)
   - Why indexes are important (query performance)
   - Single field vs compound indexes
   - Unique indexes

4. **Index Types**:
   - `ASCENDING` / `DESCENDING` - sorting direction
   - `unique=True` - prevents duplicates
   - `expireAfterSeconds` - TTL (Time To Live)

**💡 Concepts to Learn**:
- MongoDB connection patterns
- Database indexing strategy
- Collection organization

**✅ Checkpoint**: What collections exist and what is each used for?

---

## 4. Data Models & Schemas

**🎯 Goal**: Understand data structure and API validation.

**📁 Files to Study**:
- `app/models/log_model.py` - Data structure builder
- `app/schemas/log_schema.py` - Pydantic validation models
- `app/schemas/ingestion_schema.py` - Request/response models

**🔍 What to Focus On**:

1. **Model Function** (`models/log_model.py`)
   - Simple function that returns a dictionary
   - Data structure definition

2. **Pydantic Schemas** (`schemas/log_schema.py`)
   - `BaseModel` - Pydantic base class
   - Field types and optional fields
   - `Field()` for validation rules
   - Response models vs request models

3. **Schema Examples**:
   - `LogResponse` - What API returns
   - `LogsResponse` - Paginated response
   - `LogIngestionRequest` - What API accepts

**💡 FastAPI/Pydantic Concepts**:
- `BaseModel` - Data validation class
- `Field()` - Field validation and metadata
- `Optional[]` - Nullable fields
- `response_model=` - Response validation
- `alias` - Field name mapping (`_id` → `id`)

**✅ Checkpoint**: What's the difference between a model and a schema?

---

## 5. Basic API Routes

**🎯 Goal**: Understand how API endpoints are structured.

**📁 Files to Study**:
- `app/routes/logs.py` ⭐ **START HERE** (simplest route file)
- `app/routes/__init__.py` (if exists)

**🔍 What to Focus On**:

1. **Router Setup** (line 19)
   - `APIRouter(prefix="/api/logs", tags=["logs"])`
   - Prefix applies to all routes
   - Tags for API documentation grouping

2. **GET Endpoint** (lines 88-177)
   - `@router.get("")` - HTTP GET method
   - Query parameters with `Query()`
   - Type hints for validation
   - Response model with `response_model=`

3. **POST Endpoint** (lines 25-85)
   - `@router.post("/ingest")`
   - Request body with `Body()`
   - Security dependency with `Security()`
   - Error handling with `HTTPException`

4. **Query Parameters**:
   - `page: int = Query(1, ge=1)` - with validation
   - `Optional[str] = Query(None)` - optional parameter
   - Default values

5. **Response Handling**:
   - Pydantic model validation
   - Error handling patterns
   - Status codes

**💡 FastAPI Concepts to Learn**:
- `@router.get()`, `@router.post()` - Route decorators
- `Query()` - Query parameter validation
- `Body()` - Request body validation
- `Security()` - Dependency injection for auth
- `HTTPException` - Error responses
- `response_model=` - Response validation
- Path parameters: `@router.get("/{log_id}")`

**✅ Checkpoint**: Can you identify all query parameters in the GET endpoint?

---

## 6. Services Layer

**🎯 Goal**: Understand business logic separation from routes.

**📁 Files to Study**:
- `app/services/log_queries.py` - Database query logic
- `app/services/log_parser_service.py` - Log parsing logic
- `app/services/export_service.py` - Export functionality

**🔍 What to Focus On**:

1. **Service Pattern**
   - Routes call services
   - Services contain business logic
   - Services interact with database

2. **Example Flow**:
   ```
   Route (routes/logs.py)
     ↓ calls
   Service (services/log_queries.py)
     ↓ uses
   Database (db/mongo.py)
   ```

3. **Service Functions**:
   - `get_logs()` - Query database with filters
   - `parse_multiple_logs()` - Parse raw log strings
   - `export_logs_to_pdf()` - Generate PDF exports

**💡 Concepts to Learn**:
- Separation of concerns
- Service layer pattern
- Code organization

**✅ Checkpoint**: Why separate routes from services?

---

## 7. Middleware

**🎯 Goal**: Understand cross-cutting concerns.

**📁 Files to Study**:
- `app/middleware/rate_limit.py` - Rate limiting
- `app/middleware/auth_middleware.py` - API key authentication

**🔍 What to Focus On**:

1. **Rate Limiting Middleware** (`middleware/rate_limit.py`)
   - How middleware intercepts requests
   - Request counting logic
   - Response modification

2. **Auth Middleware** (`middleware/auth_middleware.py`)
   - `verify_api_key()` function
   - Used as dependency with `Security()`
   - Header extraction

3. **Middleware Order**:
   - Executes in reverse order of registration
   - CORS → Rate Limit → Routes

**💡 FastAPI Concepts**:
- `BaseHTTPMiddleware` - Custom middleware
   - `async def dispatch()` - Request/response handling
- `Security()` - Dependency for authentication
- `Request` object - Access headers, body

**✅ Checkpoint**: What happens if a request exceeds rate limit?

---

## 8. Log Ingestion

**🎯 Goal**: Understand how logs are received and processed.

**📁 Files to Study**:
- `app/routes/logs.py` (ingest endpoint, lines 25-85)
- `app/services/log_parser_service.py` - Main parser
- `app/services/log_ingestor.py` - Background ingestion
- `app/services/*_parser.py` - Individual parsers:
  - `auth_log_parser.py` - SSH/auth logs
  - `ufw_log_parser.py` - UFW firewall logs
  - `iptables_parser.py` - iptables logs
  - `syslog_parser.py` - Generic syslog
  - `sql_parser.py` - SQL logs

**🔍 What to Focus On**:

1. **Ingestion Endpoint** (`routes/logs.py`, lines 25-85)
   - POST `/api/logs/ingest`
   - Accepts array of log strings
   - Requires API key

2. **Parsing Service** (`services/log_parser_service.py`)
   - Routes to correct parser based on log_source
   - Error handling for unparseable logs
   - Returns structured log dictionaries

3. **Individual Parsers** (`services/*_parser.py`)
   - Each parser handles specific log format
   - Regex patterns for extraction
   - Timestamp parsing
   - Event type detection

4. **Background Ingestion** (`services/log_ingestor.py`)
   - File monitoring (if enabled)
   - Continuous log reading

**💡 Concepts to Learn**:
- Multi-format log parsing
- Error handling patterns
- Background workers
- File monitoring

**✅ Checkpoint**: How does the system know which parser to use?

---

## 9. Threat Detection

**🎯 Goal**: Understand how security threats are detected.

**📁 Files to Study**:
- `app/routes/threats.py` - Threat detection endpoints
- `app/services/brute_force_detection.py` - Brute force detection
- `app/services/port_scan_detection.py` - Port scanning detection
- `app/services/ddos_detection.py` - DDoS detection
- `app/services/sql_injection_detection.py` - SQL injection detection

**🔍 What to Focus On**:

1. **Threat Routes** (`routes/threats.py`)
   - GET `/api/threats/brute-force`
   - GET `/api/threats/port-scan`
   - GET `/api/threats/ddos`
   - Query parameters for time windows and thresholds

2. **Detection Logic** (`services/*_detection.py`)
   - Query patterns for each threat type
   - Time-window analysis
   - Threshold-based detection
   - Aggregation queries

3. **Detection Patterns**:
   - **Brute Force**: Multiple failed login attempts
   - **Port Scan**: Many ports accessed from one IP
   - **DDoS**: High request rate from multiple IPs
   - **SQL Injection**: SQL keywords in logs

**💡 Concepts to Learn**:
- Threat detection algorithms
- Time-window analysis
- MongoDB aggregation queries
- Rule-based detection

**✅ Checkpoint**: How does brute force detection work?

---

## 10. Alerts & Notifications

**🎯 Goal**: Understand alert system and email notifications.

**📁 Files to Study**:
- `app/routes/alerts.py` - Alert endpoints
- `app/services/alert_service.py` - Alert creation/retrieval
- `app/services/alert_notification_service.py` - Notification logic
- `app/services/alert_monitor_worker.py` - Background worker
- `app/services/email_service.py` - Email sending

**🔍 What to Focus On**:

1. **Alert Routes** (`routes/alerts.py`)
   - GET `/api/alerts` - List alerts
   - Query parameters for filtering
   - Dashboard caching

2. **Alert Service** (`services/alert_service.py`)
   - Alert creation and storage
   - Deduplication logic
   - Time-bucketing

3. **Notification Service** (`services/alert_notification_service.py`)
   - When to send notifications
   - Rate limiting per IP/alert type
   - ML score integration

4. **Email Service** (`services/email_service.py`)
   - SendGrid integration
   - Email template generation
   - Recipient management

5. **Monitor Worker** (`services/alert_monitor_worker.py`)
   - Background thread
   - Watches for new alerts
   - Triggers notifications

**💡 Concepts to Learn**:
- Background workers
- Email integration
- Notification rate limiting
- Alert deduplication

**✅ Checkpoint**: When are email notifications sent?

---

## 11. ML Integration

**🎯 Goal**: Understand Machine Learning integration.

**📁 Files to Study**:
- `app/routes/ml.py` - ML endpoints
- `app/services/ml_service.py` - ML service wrapper
- `app/services/ml_storage.py` - ML data storage
- `app/services/ml_auto_retrain_worker.py` - Auto-retraining
- `app/services/ml_retrain_pipeline.py` - Retraining pipeline

**🔍 What to Focus On**:

1. **ML Routes** (`routes/ml.py`)
   - POST `/api/ml/predict` - Get ML predictions
   - GET `/api/ml/status` - ML service status
   - GET `/api/ml/metrics` - Model metrics

2. **ML Service** (`services/ml_service.py`)
   - Initializes ML models on startup
   - Wrapper around ml_engine
   - Fallback to rule-based if ML unavailable

3. **ML Storage** (`services/ml_storage.py`)
   - Stores predictions in MongoDB
   - Feature caching
   - Training history

4. **Auto-Retraining** (`services/ml_auto_retrain_worker.py`)
   - Background worker
   - Periodically retrains models
   - Uses new labeled data

**💡 Concepts to Learn**:
- ML model integration
- Prediction storage
- Feature extraction
- Model versioning

**✅ Checkpoint**: What happens if ML models aren't available?

---

## 12. WebSocket & Real-time

**🎯 Goal**: Understand real-time log streaming.

**📁 Files to Study**:
- `app/routes/websocket.py` - WebSocket endpoint
- `app/services/raw_log_broadcaster.py` - Broadcast manager

**🔍 What to Focus On**:

1. **WebSocket Route** (`routes/websocket.py`)
   - `@router.websocket("/ws/logs")`
   - Connection handling
   - Client subscription

2. **Broadcaster Service** (`services/raw_log_broadcaster.py`)
   - Manages connected clients
   - Broadcasts logs to all clients
   - Filtering by log source

3. **Real-time Flow**:
   ```
   Log Ingested → Broadcaster → All WebSocket Clients
   ```

**💡 FastAPI Concepts**:
- `@router.websocket()` - WebSocket decorator
- `WebSocket` - WebSocket connection object
- `await websocket.accept()` - Accept connection
- `await websocket.send_json()` - Send data
- `await websocket.receive()` - Receive data

**✅ Checkpoint**: How does the frontend receive real-time logs?

---

## 13. Advanced Features

**🎯 Goal**: Explore additional features.

**📁 Files to Study**:

### 13a. IP Blocking
- `app/routes/ip_blocking.py`
- `app/services/ip_blocking_service.py`
- `app/services/auto_ip_blocking_service.py`
- Blocks IPs using iptables/ufw

### 13b. IP Reputation
- `app/routes/ip_reputation.py`
- `app/services/virustotal_service.py`
- VirusTotal API integration

### 13c. Reports
- `app/routes/reports.py`
- `app/services/report_service.py`
- Generated security reports

### 13d. Dashboard
- `app/routes/dashboard.py`
- Dashboard data aggregation

### 13e. Redis Cache
- `app/services/redis_cache.py`
- Caching layer for performance

**💡 Concepts to Learn**:
- System command execution (iptables)
- External API integration (VirusTotal)
- PDF generation (reports)
- Caching strategies (Redis)

---

## 🎓 Learning Tips

### For FastAPI Beginners:

1. **Start Simple**: Begin with `main.py` and `routes/logs.py`
2. **Use Documentation**: FastAPI auto-generates docs at `/docs`
3. **Test Endpoints**: Use the interactive API docs
4. **Read Error Messages**: FastAPI provides helpful validation errors
5. **Follow the Flow**: Route → Service → Database

### Recommended Study Order:

1. ✅ **Week 1**: Setup & Basic Routes (Steps 1-5)
2. ✅ **Week 2**: Services & Middleware (Steps 6-7)
3. ✅ **Week 3**: Log Processing (Step 8)
4. ✅ **Week 4**: Threat Detection (Step 9)
5. ✅ **Week 5**: Alerts & Notifications (Step 10)
6. ✅ **Week 6**: ML & Advanced Features (Steps 11-13)

### Practice Exercises:

1. Add a new endpoint to `routes/logs.py`
2. Create a new service function
3. Add a new query parameter to an existing endpoint
4. Modify a Pydantic schema
5. Add a new log parser

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **MongoDB Python**: https://pymongo.readthedocs.io/
- **WebSocket Guide**: https://fastapi.tiangolo.com/advanced/websockets/

---

## 🆘 Quick Reference

### File Structure Overview:

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration
│   ├── db/
│   │   └── mongo.py         # Database connection
│   ├── models/              # Data models
│   ├── schemas/             # Pydantic schemas
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   └── middleware/          # Middleware
└── requirements.txt         # Dependencies
```

### Common Patterns:

- **Route**: `@router.get("/path")` → calls Service
- **Service**: Function that does work → uses Database
- **Schema**: `BaseModel` for validation
- **Model**: Simple function that builds data structure

---

**Happy Learning! 🚀**
