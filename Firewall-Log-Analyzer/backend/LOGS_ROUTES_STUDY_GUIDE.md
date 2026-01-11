# 📚 Logs Routes Study Guide

> **Study Guide for `routes/logs.py`** - Line-by-line learning path with sequence diagram reference

## 🎯 How to Use This Guide

1. **Open the sequence diagram**: `logs_routes_sequence_diagram.puml`
   - Use PlantUML viewer or VS Code extension
   - Or view at: http://www.plantuml.com/plantuml/uml/

2. **Follow the sections below** - Study each endpoint in order
3. **Reference line numbers** - Each section shows exact lines to focus on
4. **Understand the flow** - Use the sequence diagram to visualize the interactions

---

## 📋 Study Order (Recommended)

### Phase 1: Understanding Basic Structure (15 minutes)
1. ✅ Router Setup (lines 19-22)
2. ✅ Imports (lines 1-17)

### Phase 2: Simple Endpoints (30 minutes)
3. ✅ POST `/ingest` - Log Ingestion (lines 25-85)
4. ✅ GET `/{log_id}` - Single Log (lines 448-494)

### Phase 3: Main Query Endpoint (45 minutes)
5. ✅ GET `` (empty path) - Get Logs with Pagination (lines 88-177)

### Phase 4: Export Endpoints (30 minutes)
6. ✅ GET `/export` - CSV/JSON Export (lines 180-316)
7. ✅ GET `/export/pdf` - PDF Export (lines 319-402)

### Phase 5: Statistics (20 minutes)
8. ✅ GET `/stats/summary` - Summary Stats (lines 497-507)
9. ✅ GET `/stats/top-ips` - Top IPs (lines 510-539)
10. ✅ GET `/stats/top-ports` - Top Ports (lines 542-553)

### Phase 6: Cache Endpoints (20 minutes)
11. ✅ GET `/cache/{log_source}` - Get Cached Logs (lines 556-593)
12. ✅ GET `/cache/stats` - Cache Statistics (lines 596-606)
13. ✅ DELETE `/cache` - Clear Cache (lines 609-632)

---

## 🔍 Detailed Study Guide

### 1. Router Setup & Imports

**📍 Location**: Lines 1-22

**What to Study**:

```python
# Lines 1-17: Imports
from fastapi import APIRouter, Query, HTTPException, Body, Security, Response
from app.services.log_queries import get_logs, get_log_by_id, ...
from app.schemas.log_schema import LogResponse, LogsResponse, ...
```

**Key Concepts**:
- `APIRouter` - FastAPI router for grouping routes
- `Query()` - Query parameter validation
- `Body()` - Request body validation
- `Security()` - Dependency injection for authentication
- `Response` - Custom HTTP response

```python
# Line 19: Router creation
router = APIRouter(prefix="/api/logs", tags=["logs"])
```

**Why**: 
- `prefix="/api/logs"` - All routes in this file will have `/api/logs` prefix
- `tags=["logs"]` - Groups routes in API documentation

**Sequence Diagram Reference**: See "Router Setup" section

---

### 2. POST /api/logs/ingest - Log Ingestion Endpoint

**📍 Location**: Lines 25-85

**Sequence Diagram Section**: "1. POST /api/logs/ingest - Log Ingestion"

**Line-by-Line Study**:

#### Step 1: Endpoint Definition (lines 25-28)
```python
@router.post("/ingest", response_model=LogIngestionResponse)
def ingest_logs_endpoint(
    request: LogIngestionRequest = Body(...),
    api_key: str = Security(verify_api_key)
):
```

**Study Focus**:
- `@router.post()` - HTTP POST decorator
- `response_model=` - Response validation
- `Body(...)` - Request body (required)
- `Security(verify_api_key)` - API key authentication

**FastAPI Concepts**:
- Route decorators
- Request body parsing
- Dependency injection for auth

#### Step 2: Request Validation (lines 50-55)
```python
if not request.logs:
    raise HTTPException(status_code=400, detail="Logs list cannot be empty")

if len(request.logs) > 1000:
    raise HTTPException(status_code=400, detail="Maximum 1000 log lines per request")
```

**Study Focus**:
- Input validation patterns
- `HTTPException` - Error responses
- Status codes (400 = Bad Request)

#### Step 3: Log Parsing (line 58)
```python
parsed_logs = parse_multiple_logs(request.logs, request.log_source)
```

**Sequence Flow**:
1. Route → `parse_multiple_logs()` (log_parser_service.py)
2. Parser → Individual parsers (auth_log_parser.py, ufw_log_parser.py, etc.)
3. Parsers → Extract fields, determine severity
4. Parsers → Return structured log dictionaries

**Study Focus**:
- Service layer pattern (route calls service)
- Multi-format parsing
- Error handling (None returned for unparseable logs)

#### Step 4: Database Insertion (lines 69-71)
```python
if parsed_logs:
    logs_collection.insert_many(parsed_logs)
```

**Sequence Flow**:
1. Route → MongoDB collection
2. Insert all parsed logs in batch

**Study Focus**:
- MongoDB operations
- Batch insertion
- Error handling

#### Step 5: Response (lines 75-81)
```python
return LogIngestionResponse(
    success=True,
    ingested_count=len(parsed_logs),
    failed_count=failed_count,
    total_received=len(request.logs),
    message=f"Successfully ingested {len(parsed_logs)} log(s)..."
)
```

**Study Focus**:
- Response model usage
- Calculated fields
- Response structure

**Related Files to Study**:
- `app/services/log_parser_service.py` - Parsing logic
- `app/services/auth_log_parser.py` - Example parser
- `app/schemas/ingestion_schema.py` - Request/response models
- `app/middleware/auth_middleware.py` - API key verification

---

### 3. GET /api/logs - Get Logs with Pagination

**📍 Location**: Lines 88-177

**Sequence Diagram Section**: "2. GET /api/logs - Get Logs with Pagination"

**Line-by-Line Study**:

#### Step 1: Endpoint Definition (lines 88-104)
```python
@router.get("", response_model=LogsResponse)
def get_logs_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Number of logs per page"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP"),
    # ... more parameters
):
```

**Study Focus**:
- Empty path `""` means root of router (`/api/logs`)
- `Query()` - Query parameter validation
  - `ge=1` - Greater than or equal to 1
  - `le=500` - Less than or equal to 500
  - `None` - Optional parameter
- Many query parameters for filtering

**FastAPI Concepts**:
- Query parameter validation
- Optional parameters
- Default values
- Type hints

#### Step 2: Call Service Layer (lines 107-121)
```python
result = get_logs(
    page=page,
    page_size=page_size,
    source_ip=source_ip,
    # ... pass all parameters
)
```

**Sequence Flow**:
1. Route → `get_logs()` (log_queries.py)
2. Service → `build_log_query()` - Build MongoDB query
3. Service → MongoDB queries (count, find/aggregate)
4. Service → Pagination calculations
5. Service → Return result dict

**Study Focus**:
- Separation of concerns (route vs service)
- Service function signature
- Parameter passing

#### Step 3: VirusTotal Reputation (lines 123-127)
```python
reputation_data = {}
if include_reputation:
    unique_ips = list(set(log.get("source_ip") for log in result["logs"] if log.get("source_ip")))
    reputation_data = get_multiple_ip_reputations(unique_ips)
```

**Sequence Flow**:
1. Extract unique IPs from logs
2. Call VirusTotal service
3. Get reputation data for all IPs

**Study Focus**:
- Conditional feature (optional reputation)
- External API integration
- Data extraction patterns

#### Step 4: Convert to Response Models (lines 129-167)
```python
log_responses = []
for log in result["logs"]:
    try:
        log_dict = dict(log)
        
        # Ensure required fields have default values
        if "timestamp" not in log_dict or log_dict["timestamp"] is None:
            continue  # Skip logs without timestamp
        if "source_ip" not in log_dict or not log_dict["source_ip"]:
            log_dict["source_ip"] = "Unknown"
        # ... more defaults
        
        # Add reputation if requested
        if include_reputation:
            # ... reputation logic
        
        log_responses.append(LogResponse(**log_dict))
    except ValidationError as e:
        continue  # Skip invalid logs
```

**Study Focus**:
- Data transformation
- Default value handling
- Error handling per item (skip invalid, don't fail entire request)
- Pydantic validation (`LogResponse(**log_dict)`)
- Reputation enhancement

**Pattern**: Transform database documents → Response models

#### Step 5: Return Response (lines 169-175)
```python
return LogsResponse(
    logs=log_responses,
    total=result["total"],
    page=result["page"],
    page_size=result["page_size"],
    total_pages=result["total_pages"]
)
```

**Study Focus**:
- Response model structure
- Pagination metadata
- Response composition

**Related Files to Study**:
- `app/services/log_queries.py` - Query logic (lines 56-146)
- `app/services/virustotal_service.py` - Reputation service
- `app/schemas/log_schema.py` - Response models

---

### 4. GET /api/logs/{log_id} - Get Single Log

**📍 Location**: Lines 448-494

**Sequence Diagram Section**: "3. GET /api/logs/{log_id} - Get Single Log"

**Line-by-Line Study**:

#### Step 1: Endpoint Definition (lines 448-452)
```python
@router.get("/{log_id}", response_model=LogResponse)
def get_log_endpoint(
    log_id: str,
    include_reputation: bool = Query(False, description="Include VirusTotal IP reputation data")
):
```

**Study Focus**:
- Path parameter: `/{log_id}` - Extracts from URL
- Query parameter: `include_reputation` - Optional boolean
- Type: `log_id` is `str` (will be converted to ObjectId in service)

**FastAPI Concepts**:
- Path parameters
- Path + query parameters together

#### Step 2: Get Log by ID (lines 456-458)
```python
log = get_log_by_id(log_id)
if not log:
    raise HTTPException(status_code=404, detail="Log not found")
```

**Sequence Flow**:
1. Route → `get_log_by_id()` (log_queries.py)
2. Service → Convert string to ObjectId
3. Service → MongoDB find_one()
4. Service → Convert ObjectId to string
5. Service → Return log dict or None

**Study Focus**:
- 404 Not Found handling
- ObjectId conversion (string ↔ ObjectId)
- Single document query

#### Step 3: Default Values & Reputation (lines 460-488)
```python
log_dict = dict(log)

# Ensure required fields
if "timestamp" not in log_dict or log_dict["timestamp"] is None:
    raise HTTPException(status_code=500, detail="Log entry is missing required timestamp field")
# ... more defaults

# Add reputation if requested
if include_reputation:
    ip = log_dict.get("source_ip")
    if ip:
        reputation = get_ip_reputation(ip)
        if reputation:
            log_dict["virustotal"] = reputation
            # Enhance severity
```

**Study Focus**:
- Similar pattern to GET logs endpoint
- Single IP reputation lookup
- Severity enhancement

#### Step 4: Return Response (lines 490-494)
```python
return LogResponse(**log_dict)
```

**Study Focus**:
- Simple response (single object, not list)
- Pydantic validation

**Related Files to Study**:
- `app/services/log_queries.py` - get_log_by_id() (lines 149-156)
- `app/services/virustotal_service.py` - get_ip_reputation()

---

### 5. GET /api/logs/export - Export Logs (CSV/JSON)

**📍 Location**: Lines 180-316

**Sequence Diagram Section**: "4. GET /api/logs/export - Export Logs (CSV/JSON)"

**Line-by-Line Study**:

#### Step 1: Endpoint Definition (lines 180-194)
```python
@router.get("/export")
def export_logs_endpoint(
    format: str = Query("csv", regex="^(csv|json)$", description="Export format (csv or json)"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP"),
    # ... many filter parameters
):
```

**Study Focus**:
- `regex="^(csv|json)$"` - Validate format parameter
- Many filter parameters (same as GET logs)
- No `response_model=` - Returns custom Response

**FastAPI Concepts**:
- Regex validation
- File downloads
- Custom Response objects

#### Step 2: Build Query & Fetch Logs (lines 197-252)
```python
query = build_log_query(...)  # Same as GET logs

# Special handling for severity sorting
if sort_by == "severity":
    # Aggregation pipeline
    pipeline = [...]
    logs = list(logs_collection.aggregate(pipeline))
else:
    # Standard find with sort
    logs = list(logs_collection.find(query).sort(sort_criteria))
```

**Study Focus**:
- Reuses `build_log_query()` function
- MongoDB aggregation pipeline (for custom severity sorting)
- No pagination (exports all matching logs)
- Sorting logic

**Sequence Flow**: Similar to GET logs, but no pagination

#### Step 3: Format Data (lines 254-263)
```python
for log in logs:
    log["_id"] = str(log["_id"])
    if "timestamp" in log and isinstance(log["timestamp"], datetime):
        timestamp_str = log["timestamp"].isoformat()
        log["timestamp"] = timestamp_str
```

**Study Focus**:
- Data formatting for export
- ObjectId to string
- Timestamp formatting (ISO format)

#### Step 4: CSV Export (lines 265-303)
```python
if format.lower() == "csv":
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(headers)
    
    # Write data rows
    for log in logs:
        writer.writerow([...])
    
    csv_content = output.getvalue()
    
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=logs_export_{...}.csv"
        }
    )
```

**Study Focus**:
- `io.StringIO()` - In-memory string buffer
- `csv.writer()` - CSV writing
- `Response` object - Custom HTTP response
- `Content-Disposition` header - Triggers file download
- Filename generation with timestamp

**FastAPI Concepts**:
- File downloads
- Response headers
- Media types
- Content-Disposition header

#### Step 5: JSON Export (lines 304-314)
```python
else:
    json_content = json.dumps(logs, indent=2, default=str, ensure_ascii=False)
    
    return Response(
        content=json_content.encode('utf-8'),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=logs_export_{...}.json"
        }
    )
```

**Study Focus**:
- `json.dumps()` - JSON serialization
- `default=str` - Handle datetime objects
- Similar Response pattern as CSV

**Related Files to Study**:
- Python `csv` module documentation
- Python `json` module documentation
- FastAPI Response class

---

### 6. GET /api/logs/export/pdf - PDF Export

**📍 Location**: Lines 319-402

**Sequence Diagram Section**: "5. GET /api/logs/export/pdf - Export Logs to PDF"

**Line-by-Line Study**:

#### Step 1: Endpoint Definition (lines 319-333)
```python
@router.get("/export/pdf")
def export_logs_pdf_endpoint(
    limit: int = Query(1000, ge=1, le=5000, description="Maximum number of logs to export to PDF"),
    # ... filter parameters
):
```

**Study Focus**:
- Separate endpoint for PDF (different from CSV/JSON)
- `limit` parameter - PDFs can be large, so limit results
- Same filter parameters as other endpoints

#### Step 2: Query & Fetch (lines 336-382)
```python
query = build_log_query(...)

# Same sorting logic as /export endpoint
if sort_by == "severity":
    # Aggregation pipeline
    logs = list(logs_collection.aggregate(pipeline))
else:
    # Standard find with sort
    logs = list(logs_collection.find(query).sort(sort_criteria).limit(limit))
```

**Study Focus**:
- Similar to CSV/JSON export
- But applies `limit` to results
- Same sorting logic

#### Step 3: Normalize Data (lines 384-391)
```python
normalized = []
for log in logs:
    d = dict(log)
    d["_id"] = str(d.get("_id"))
    ts = d.get("timestamp")
    if isinstance(ts, datetime):
        d["timestamp"] = ts.isoformat()
    normalized.append(d)
```

**Study Focus**:
- Data normalization
- ObjectId and timestamp conversion
- Build normalized list

#### Step 4: Generate PDF (lines 393-400)
```python
pdf_bytes = export_logs_to_pdf(normalized, title="Firewall Logs Export")

return Response(
    content=pdf_bytes,
    media_type="application/pdf",
    headers={
        "Content-Disposition": f"attachment; filename=logs_export_{...}.pdf"
    }
)
```

**Sequence Flow**:
1. Route → `export_logs_to_pdf()` (export_service.py)
2. Service → Generate PDF using reportlab
3. Service → Color-code rows by severity
4. Service → Return PDF bytes

**Study Focus**:
- Service call for PDF generation
- Binary content (PDF bytes)
- PDF-specific media type

**Related Files to Study**:
- `app/services/export_service.py` - PDF generation logic
- Python `reportlab` library documentation

---

### 7. Statistics Endpoints

**📍 Location**: Lines 497-553

**Sequence Diagram Section**: "6. GET /api/logs/stats/* - Statistics Endpoints"

#### GET /api/logs/stats/summary (lines 497-507)

**Study Focus**:
```python
@router.get("/stats/summary", response_model=StatsResponse)
def get_stats_endpoint(
    start_date: Optional[datetime] = Query(None, ...),
    end_date: Optional[datetime] = Query(None, ...)
):
    stats = get_statistics(start_date=start_date, end_date=end_date)
    return StatsResponse(**stats)
```

**Pattern**: Simple wrapper around service function

**Sequence Flow**:
1. Route → `get_statistics()` (log_queries.py)
2. Service → MongoDB aggregation queries
3. Service → Count documents, group by fields
4. Service → Return statistics dict
5. Route → Convert to StatsResponse model

#### GET /api/logs/stats/top-ips (lines 510-539)

**Study Focus**:
```python
@router.get("/stats/top-ips", response_model=list[TopIPResponse])
def get_top_ips_endpoint(
    limit: int = Query(10, ge=1, le=100, ...),
    include_reputation: bool = Query(False, ...)
):
    top_ips = get_top_ips(limit=limit, ...)
    
    # Optional reputation lookup
    if include_reputation:
        reputation_data = get_multiple_ip_reputations(unique_ips)
        # Add reputation to each IP
    
    return [TopIPResponse(**ip) for ip in top_ips]
```

**Pattern**: Similar to GET logs endpoint
- Call service function
- Optional reputation enhancement
- Convert to response models

**Sequence Flow**: Similar to GET logs with reputation

#### GET /api/logs/stats/top-ports (lines 542-553)

**Study Focus**:
```python
@router.get("/stats/top-ports", response_model=list[TopPortResponse])
def get_top_ports_endpoint(...):
    top_ports = get_top_ports(limit=limit, ...)
    return [TopPortResponse(**port) for port in top_ports]
```

**Pattern**: Simplest endpoint - no reputation, just query and return

**Related Files to Study**:
- `app/services/log_queries.py` - Statistics functions
- `app/schemas/log_schema.py` - StatsResponse, TopIPResponse, TopPortResponse

---

### 8. Cache Endpoints

**📍 Location**: Lines 556-632

**Sequence Diagram Section**: "7. GET /api/logs/cache/* - Redis Cache Endpoints"

#### GET /api/logs/cache/{log_source} (lines 556-593)

**Study Focus**:
```python
@router.get("/cache/{log_source}")
def get_cached_logs_endpoint(
    log_source: str,
    limit: Optional[int] = Query(None, ...)
):
    # Validate log_source
    valid_sources = ["auth", "ufw", "kern", "syslog", "messages", "all"]
    if log_source not in valid_sources:
        raise HTTPException(status_code=400, ...)
    
    # Get from Redis cache
    cached_logs = redis_log_cache.get_logs(log_source, limit=limit)
    
    return {
        "log_source": log_source,
        "count": len(cached_logs),
        "logs": cached_logs,
        "cache_enabled": redis_log_cache.enabled
    }
```

**Pattern**: Simple cache retrieval

**Sequence Flow**:
1. Route → Validate log_source
2. Route → `redis_log_cache.get_logs()`
3. Cache → Redis lrange() operation
4. Cache → JSON deserialize
5. Route → Return cached logs

#### GET /api/logs/cache/stats (lines 596-606)

**Study Focus**:
```python
@router.get("/cache/stats")
def get_cache_stats_endpoint():
    stats = redis_log_cache.get_cache_stats()
    return stats
```

**Pattern**: Simplest possible endpoint - just call service and return

#### DELETE /api/logs/cache (lines 609-632)

**Study Focus**:
```python
@router.delete("/cache")
def clear_cache_endpoint(
    log_source: Optional[str] = Query(None, ...)
):
    success = redis_log_cache.clear_cache(log_source)
    
    if success:
        return {
            "success": True,
            "message": f"Cache cleared for {log_source if log_source else 'all sources'}"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")
```

**Pattern**: DELETE endpoint
- Optional query parameter
- Service call
- Success/error handling

**FastAPI Concepts**:
- HTTP DELETE method
- Optional query parameters

**Related Files to Study**:
- `app/services/redis_cache.py` - Redis cache operations
- `docs/redis_log_flow_sequence.puml` - Redis flow diagram

---

## 📊 Summary: Common Patterns

### Pattern 1: Simple Service Wrapper
```python
@router.get("/path")
def endpoint(...):
    result = service_function(...)
    return ResponseModel(**result)
```

**Examples**: `/stats/summary`, `/stats/top-ports`, `/cache/stats`

### Pattern 2: Service + Data Transformation
```python
@router.get("/path")
def endpoint(...):
    result = service_function(...)
    
    # Transform data
    responses = []
    for item in result["items"]:
        # Add defaults, enhancement, etc.
        responses.append(ResponseModel(**item))
    
    return ListResponse(items=responses, ...)
```

**Examples**: GET `/api/logs`, GET `/stats/top-ips`

### Pattern 3: Service + File Export
```python
@router.get("/export")
def endpoint(...):
    # Query and fetch
    logs = fetch_logs(...)
    
    # Format data
    formatted = format_data(logs)
    
    # Generate file
    file_content = generate_file(formatted)
    
    # Return as download
    return Response(
        content=file_content,
        media_type="...",
        headers={"Content-Disposition": "attachment; filename=..."}
    )
```

**Examples**: `/export`, `/export/pdf`

### Pattern 4: Request → Service → Database → Response
```python
@router.post("/path")
def endpoint(request: RequestModel):
    # Validate
    if not valid:
        raise HTTPException(400)
    
    # Process
    result = service_function(request.data)
    
    # Store
    database.insert(result)
    
    # Return
    return ResponseModel(...)
```

**Example**: POST `/ingest`

---

## 🎓 Study Checklist

- [ ] Understand router setup and imports
- [ ] Understand POST `/ingest` endpoint (authentication, parsing, database)
- [ ] Understand GET `` endpoint (pagination, filtering, reputation)
- [ ] Understand GET `/{log_id}` endpoint (single document query)
- [ ] Understand export endpoints (CSV, JSON, PDF)
- [ ] Understand statistics endpoints (aggregation queries)
- [ ] Understand cache endpoints (Redis operations)
- [ ] Recognize common patterns across endpoints
- [ ] Understand FastAPI concepts: Query, Body, Security, Response
- [ ] Understand service layer pattern
- [ ] Understand Pydantic validation
- [ ] Understand error handling patterns

---

## 🔗 Next Steps

After studying `logs.py`, move on to:
1. **Threat Detection** (`routes/threats.py`)
2. **Alerts** (`routes/alerts.py`)
3. **ML Integration** (`routes/ml.py`)

---

**Happy Learning! 🚀**
