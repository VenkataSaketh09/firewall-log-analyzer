# 📊 Logs Page - Complete Flow Explanation

> **For Review/Presentation**: Comprehensive explanation of the Logs page functionality, components, and backend integration.

---

## 🎯 Overview

The **Logs Page** is the main interface for viewing, filtering, sorting, and analyzing firewall logs. It provides both **normal table view** and **live monitoring mode** for real-time log viewing.

---

## 📁 Frontend Components Structure

### Main Page Component
- **File**: `frontend/src/pages/Logs.jsx`
- **Lines**: 1-634
- **Purpose**: Main container component that orchestrates all log-related functionality

### Sub-Components

1. **LogFilterPanel.jsx** (Lines 1-193)
   - Filter UI for date range, IP, severity, event type, etc.
   - Quick date range buttons (Last Week, Month, Year)

2. **LogsTable.jsx** (Lines 1-234)
   - Displays logs in a sortable, selectable table
   - Shows: Timestamp, Source IP, Destination Port, Protocol, Log Source, Event Type, Severity
   - Clickable rows for details

3. **LogDetailsModal.jsx** (Lines 1-409)
   - Modal popup showing full log details
   - ML Analysis button for ML predictions
   - Displays all log fields

4. **LogSourceTabs.jsx** (Lines 1-47)
   - Tabs for switching log sources (auth, ufw, kern, syslog, messages, all)
   - Used in live monitoring mode

5. **RawLogViewer.jsx** (Lines 1-200+)
   - Displays raw log lines in live monitoring mode
   - Scrollable log viewer

### Hooks (React Query)

1. **useLogsQueries.js** (Lines 1-167)
   - `useLogs()` - Fetch logs with filters/pagination
   - `useLogById()` - Fetch single log
   - `useExportLogsCSV()` - Export as CSV
   - `useExportLogsJSON()` - Export as JSON
   - `useExportLogsPDF()` - Export as PDF
   - `useExportSelectedLogsPDF()` - Export selected logs as PDF

2. **useRawLogWebSocket.js** (Lines 1-194)
   - `useRawLogWebSocket()` - WebSocket hook for live monitoring
   - Manages connection, subscriptions, log caching

### Services

1. **logsService.js** (Lines 1-159)
   - `getLogs()` - API call to GET /api/logs
   - `getLogById()` - API call to GET /api/logs/{id}
   - `exportLogsCSV()` - API call to GET /api/logs/export?format=csv
   - `exportLogsJSON()` - API call to GET /api/logs/export?format=json
   - `exportLogsPDF()` - API call to GET /api/logs/export/pdf
   - `exportSelectedLogsPDF()` - API call to POST /api/logs/export/pdf
   - `getCachedLogs()` - API call to GET /api/logs/cache/{source}

2. **api.js** (Lines 1-75)
   - Axios instance with base URL configuration
   - Request/response interceptors
   - Error handling

---

## 🔄 Flow Explanations

### 1. Initial Page Load

**Sequence**: Browser → Logs.jsx → useLogs() → logsService.js → Backend API → MongoDB

**Step-by-Step**:

1. **User navigates** to `/logs` route
2. **Logs.jsx component mounts** (Lines 18-634)
   - Initializes state (pagination, filters, sorting)
3. **useLogs hook called** (Lines 63-77 in Logs.jsx)
   - React Query hook with parameters
4. **getLogs() service function** (useLogsQueries.js, line 79)
   - Builds query parameters
5. **API call** (logsService.js, line 46)
   - `GET /api/logs?page=1&page_size=50&sort_by=timestamp&sort_order=desc`
6. **Backend route** (routes/logs.py, lines 88-177)
   - `get_logs_endpoint()` function
7. **Query service** (services/log_queries.py, lines 56-146)
   - `get_logs()` function
   - Builds MongoDB query
   - Fetches paginated results
8. **MongoDB query** (db/mongo.py)
   - `logs_collection.find(query).sort().skip().limit()`
9. **Response flows back** through all layers
10. **LogsTable renders** with fetched data

**Key Functions**:
- `Logs.jsx`: Component initialization (lines 18-61)
- `useLogs()`: React Query hook (useLogsQueries.js, lines 16-90)
- `getLogs()`: Service function (logsService.js, lines 6-48)
- `get_logs_endpoint()`: Backend route (routes/logs.py, lines 88-177)
- `get_logs()`: Backend service (log_queries.py, lines 56-146)

---

### 2. Filtering Logs

**Sequence**: User input → LogFilterPanel → Logs.jsx → useLogs() → Backend → MongoDB

**Step-by-Step**:

1. **User changes filter** (e.g., selects severity "HIGH" in LogFilterPanel)
2. **LogFilterPanel calls** `onFilterChange('severity', 'HIGH')` (LogFilterPanel.jsx, line 98)
3. **Logs.jsx receives** `handleFilterChange('severity', 'HIGH')` (Logs.jsx, lines 185-187)
4. **State updates** `setFilters(prev => {...prev, severity: 'HIGH'})`
5. **React Query detects dependency change** (useLogs hook refetches automatically)
6. **New API call** with filter parameters
   - `GET /api/logs?severity=HIGH&page=1&page_size=50`
7. **Backend filters** logs using MongoDB query
8. **Filtered results** returned and displayed

**Key Functions**:
- `LogFilterPanel`: Filter UI component (LogFilterPanel.jsx, lines 1-193)
- `handleFilterChange()`: Update filter state (Logs.jsx, lines 185-187)
- `build_log_query()`: Build MongoDB query (log_queries.py, lines 7-53)
- `get_logs()`: Execute filtered query (log_queries.py, lines 56-146)

**Filter Options**:
- Date range (start_date, end_date)
- Source IP
- Severity (HIGH, MEDIUM, LOW, CRITICAL)
- Event Type
- Log Source (auth.log, ufw.log, etc.)
- Protocol (TCP, UDP)
- Destination Port
- Search (text search in source_ip, raw_log, username)

---

### 3. Sorting Logs

**Sequence**: User clicks column → LogsTable → Logs.jsx → useLogs() → Backend → MongoDB

**Step-by-Step**:

1. **User clicks column header** (e.g., "Source IP" in LogsTable)
2. **LogsTable calls** `onSort('source_ip', 'asc')` (LogsTable.jsx, line 95)
3. **Logs.jsx receives** `handleSort('source_ip', 'asc')` (Logs.jsx, lines 203-206)
4. **State updates**: `setSortBy('source_ip')` and `setSortOrder('asc')`
5. **React Query refetches** with new sort parameters
6. **API call** with sort parameters
   - `GET /api/logs?sort_by=source_ip&sort_order=asc`
7. **Backend sorts** using MongoDB sort
8. **Sorted results** returned

**Key Functions**:
- `LogsTable`: Table component with sortable headers (LogsTable.jsx, lines 17-234)
- `handleSort()`: Update sort state (Logs.jsx, lines 203-206)
- `get_logs()`: Backend sorting logic (log_queries.py, lines 121-132)

**Sortable Columns**:
- Timestamp (default: desc)
- Source IP
- Event Type
- Severity (custom order: CRITICAL > HIGH > MEDIUM > LOW)

---

### 4. Pagination

**Sequence**: User clicks page button → Logs.jsx → useLogs() → Backend → MongoDB

**Step-by-Step**:

1. **User clicks "Next"** or page number
2. **Logs.jsx handles** `handlePageChange(newPage)` (Logs.jsx, lines 213-215)
3. **State updates**: `setPagination(prev => {...prev, page: newPage})`
4. **React Query refetches** with new page number
5. **API call** with page parameter
   - `GET /api/logs?page=2&page_size=50`
6. **Backend calculates skip** `skip = (page - 1) * page_size`
7. **MongoDB query** with skip and limit
8. **Next page results** returned

**Key Functions**:
- `handlePageChange()`: Update page state (Logs.jsx, lines 213-215)
- `handlePageSizeChange()`: Change items per page (Logs.jsx, lines 217-219)
- `get_logs()`: Pagination calculation (log_queries.py, lines 84-85, 114-115, 131)

**Pagination Features**:
- Page navigation (Previous/Next buttons)
- Page size selection (25, 50, 100, 200 per page)
- Total count and page information display

---

### 5. View Log Details

**Sequence**: User clicks "View" → LogsTable → Logs.jsx → LogDetailsModal → ML Service (optional)

**Step-by-Step**:

1. **User clicks "View" button** on a log row
2. **LogsTable calls** `onViewDetails(log)` (LogsTable.jsx, line 216)
3. **Logs.jsx handles** `handleViewDetails(log)` (Logs.jsx, lines 208-211)
   - Sets `selectedLog` state
   - Sets `isModalOpen` to true
4. **LogDetailsModal renders** (LogDetailsModal.jsx, lines 8-409)
   - Displays all log fields
   - Shows formatted values
5. **User clicks "ML Analyze"** (optional)
   - Modal calls `predictWithML()` (LogDetailsModal.jsx, lines 77-80)
   - API call: `POST /api/ml/predict`
   - Backend returns ML prediction (risk score, anomaly score, confidence)
   - Modal displays ML analysis results
6. **User closes modal** by clicking X
   - `setIsModalOpen(false)`
   - Modal unmounts

**Key Functions**:
- `handleViewDetails()`: Open modal (Logs.jsx, lines 208-211)
- `LogDetailsModal`: Modal component (LogDetailsModal.jsx, lines 8-409)
- `predictWithML()`: ML service call (mlService.js)
- `@router.post('/predict')`: ML endpoint (routes/ml.py)

**Displayed Fields**:
- Timestamp (formatted)
- Source IP / Destination IP
- Ports (source/destination)
- Protocol
- Log Source
- Event Type
- Severity (with color badge)
- Username
- Raw Log (full text)
- ML Analysis (if requested)

---

### 6. Export Logs

**Sequence**: User clicks Export → Logs.jsx → Export hook → Backend → File download

**Step-by-Step**:

#### Export All Logs (with filters)

1. **User clicks "Export" button** → selects format (CSV/JSON/PDF)
2. **Logs.jsx handles** `handleExport(format)` (Logs.jsx, lines 255-288)
   - Builds export parameters from current filters
   - Calls appropriate export hook
3. **Export hook** (useLogsQueries.js)
   - `useExportLogsCSV()`, `useExportLogsJSON()`, or `useExportLogsPDF()`
4. **Service function** (logsService.js)
   - `exportLogsCSV()`, `exportLogsJSON()`, or `exportLogsPDF()`
5. **API call**:
   - CSV/JSON: `GET /api/logs/export?format=csv&...filters`
   - PDF: `GET /api/logs/export/pdf?limit=1000&...filters`
6. **Backend route** (routes/logs.py)
   - CSV: Lines 180-316 (`export_logs_endpoint()`)
   - JSON: Lines 304-314
   - PDF: Lines 319-402 (`export_logs_pdf_endpoint()`)
7. **Backend processing**:
   - CSV: Generates CSV using `csv.writer`
   - JSON: Serializes with `json.dumps()`
   - PDF: Calls `export_service.export_logs_to_pdf()`
8. **Response** with file content (blob)
9. **Frontend downloads** file using `downloadBlob()` (Logs.jsx, lines 244-253)

#### Export Selected Logs

1. **User selects logs** (checkboxes)
2. **User clicks "Export Selected"**
3. **Logs.jsx handles**:
   - CSV/JSON: Client-side export (Logs.jsx, lines 290-341)
   - PDF: Server-side export (Logs.jsx, lines 343-357)
4. **PDF export**:
   - Calls `exportSelectedLogsPDF()` hook
   - API: `POST /api/logs/export/pdf` with `{log_ids: [...]}`
   - Backend: Lines 405-445 (`export_selected_logs_pdf_endpoint()`)

**Key Functions**:
- `handleExport()`: Export handler (Logs.jsx, lines 255-288)
- `exportSelectedLogs()`: Client-side selected export (Logs.jsx, lines 290-341)
- `exportSelectedLogsPDFHandler()`: Server-side selected PDF (Logs.jsx, lines 343-357)
- `downloadBlob()`: File download helper (Logs.jsx, lines 244-253)
- `export_logs_endpoint()`: CSV/JSON export (routes/logs.py, lines 180-316)
- `export_logs_pdf_endpoint()`: PDF export (routes/logs.py, lines 319-402)
- `export_selected_logs_pdf_endpoint()`: Selected PDF export (routes/logs.py, lines 405-445)
- `export_logs_to_pdf()`: PDF generation (services/export_service.py)

---

### 7. Live Monitoring Mode

**Sequence**: User enables Live Mode → WebSocket connection → Real-time log updates

**Step-by-Step**:

#### Enable Live Mode

1. **User clicks "Live Monitoring" button**
2. **Logs.jsx handles** `handleToggleLiveMode()` (Logs.jsx, lines 158-160)
   - Sets `liveMode` to true
3. **useEffect triggers** (Logs.jsx, lines 101-108)
   - Calls `connect()` from `useRawLogWebSocket` hook
4. **WebSocket connection** (useRawLogWebSocket.js, lines 19-35)
   - Creates `new WebSocket('ws://localhost:8000/ws/logs/live')`
   - Sets up event handlers (onopen, onmessage, onerror, onclose)
5. **Backend accepts** WebSocket connection (routes/websocket.py)
   - `@router.websocket('/ws/logs/live')`
   - Adds client to `raw_log_broadcaster`
6. **Subscribe to log source** (Logs.jsx, lines 111-120)
   - Calls `subscribe(activeLogSource)` (e.g., 'auth')
   - Sends subscription message via WebSocket
7. **Backend confirms** subscription
8. **UI switches** to RawLogViewer component (Logs.jsx, lines 447-468)

#### Receive Live Logs

1. **Backend ingests new log** (log_ingestor.py or POST /api/logs/ingest)
2. **Backend broadcasts** via `raw_log_broadcaster.broadcast(log_source, log_line)`
3. **Broadcaster filters** clients subscribed to that log_source
4. **WebSocket sends** log to subscribed clients
5. **Frontend receives** log in `onmessage` handler (useRawLogWebSocket.js, lines 38-82)
6. **Hook updates state** (adds log to logs array)
7. **RawLogViewer renders** new log in real-time

#### Disable Live Mode

1. **User clicks "Stop Live"**
2. **Logs.jsx handles** `handleToggleLiveMode()` (sets liveMode to false)
3. **useEffect triggers** (Logs.jsx, lines 101-108)
   - Calls `disconnect()` and `clearLogs()`
4. **WebSocket closes**
5. **UI switches back** to normal table view

**Key Functions**:
- `handleToggleLiveMode()`: Toggle live mode (Logs.jsx, lines 158-160)
- `useRawLogWebSocket()`: WebSocket hook (useRawLogWebSocket.js, lines 5-194)
- `connect()`: Establish WebSocket (useRawLogWebSocket.js, lines 19-35)
- `subscribe()`: Subscribe to log source (useRawLogWebSocket.js, lines 107-130)
- `@router.websocket('/ws/logs/live')`: WebSocket route (routes/websocket.py)
- `raw_log_broadcaster.broadcast()`: Broadcast logs (services/raw_log_broadcaster.py)
- `RawLogViewer`: Live log viewer component (RawLogViewer.jsx)

---

## 🔗 Backend Integration

### API Endpoints Used

1. **GET /api/logs** - Fetch logs with pagination/filtering
   - **Route**: `routes/logs.py`, lines 88-177
   - **Function**: `get_logs_endpoint()`
   - **Service**: `services/log_queries.py`, `get_logs()`

2. **GET /api/logs/{log_id}** - Get single log
   - **Route**: `routes/logs.py`, lines 448-494
   - **Function**: `get_log_endpoint()`
   - **Service**: `services/log_queries.py`, `get_log_by_id()`

3. **GET /api/logs/export** - Export CSV/JSON
   - **Route**: `routes/logs.py`, lines 180-316
   - **Function**: `export_logs_endpoint()`

4. **GET /api/logs/export/pdf** - Export PDF
   - **Route**: `routes/logs.py`, lines 319-402
   - **Function**: `export_logs_pdf_endpoint()`
   - **Service**: `services/export_service.py`, `export_logs_to_pdf()`

5. **POST /api/logs/export/pdf** - Export selected logs PDF
   - **Route**: `routes/logs.py`, lines 405-445
   - **Function**: `export_selected_logs_pdf_endpoint()`

6. **POST /api/ml/predict** - ML prediction
   - **Route**: `routes/ml.py`
   - **Function**: ML prediction endpoint

7. **WebSocket /ws/logs/live** - Live monitoring
   - **Route**: `routes/websocket.py`
   - **Service**: `services/raw_log_broadcaster.py`

### Key Backend Functions

1. **log_queries.py**:
   - `build_log_query()` - Build MongoDB query from filters
   - `get_logs()` - Fetch paginated, filtered, sorted logs
   - `get_log_by_id()` - Fetch single log

2. **export_service.py**:
   - `export_logs_to_pdf()` - Generate PDF with reportlab

3. **raw_log_broadcaster.py**:
   - `broadcast()` - Broadcast logs to WebSocket clients
   - `add_client()` - Register WebSocket client
   - `remove_client()` - Unregister WebSocket client

---

## 📋 Summary for Review

### Features Implemented

1. ✅ **Log Viewing**: Paginated table view with sortable columns
2. ✅ **Filtering**: Multiple filter options (date, IP, severity, event type, etc.)
3. ✅ **Sorting**: Sort by timestamp, source IP, event type, severity
4. ✅ **Pagination**: Navigate through pages, change page size
5. ✅ **Log Details**: Modal popup with full log information
6. ✅ **ML Analysis**: ML prediction integration in log details
7. ✅ **Export**: CSV, JSON, PDF export (all logs or selected)
8. ✅ **Live Monitoring**: WebSocket-based real-time log viewing
9. ✅ **Log Source Tabs**: Switch between different log sources
10. ✅ **Bulk Selection**: Select multiple logs for bulk export

### Technologies Used

- **Frontend**: React, React Query, React Table, WebSocket API
- **Backend**: FastAPI, MongoDB, WebSocket, reportlab (PDF)
- **State Management**: React Query (caching, auto-refetch)
- **Real-time**: WebSocket for live monitoring
- **Export**: CSV, JSON, PDF formats

---

**This completes the comprehensive explanation of the Logs page flow!** 🎉
