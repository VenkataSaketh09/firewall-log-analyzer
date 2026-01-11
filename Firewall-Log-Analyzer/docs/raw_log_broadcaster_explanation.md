# Step-by-Step Explanation: `raw_log_broadcaster.py`

## 🎯 **What Does This File Do?**

This file creates a **real-time log broadcasting system** using WebSockets. Think of it like a TV station:
- **Log files** (like `/var/log/auth.log`) are constantly producing new log lines
- **WebSocket clients** (like a frontend dashboard) want to watch these logs in real-time
- This broadcaster **sends each new log line** to all connected clients who are subscribed

---

## 🔌 **FastAPI & WebSocket Basics**

### What is a WebSocket?
- **Normal HTTP**: Client asks → Server responds → Connection closes
- **WebSocket**: Client connects → Connection stays open → Server can push data anytime

### Why WebSockets for Logs?
- Logs arrive continuously (every second, or even faster)
- We can't have clients constantly asking "any new logs?" (inefficient)
- Instead, server **pushes** logs to clients when they arrive

---

## 📦 **The Class Structure**

### `RawLogBroadcaster` Class

This is a **singleton pattern** - only ONE instance exists for the entire application (created at line 171).

---

## 🔧 **Initialization (`__init__` method)**

```python
def __init__(self):
```

### What Each Variable Does:

1. **`self.connections: Dict[str, WebSocket]`**
   - Stores all active WebSocket connections
   - Key: `"conn_1"`, `"conn_2"`, etc. (unique ID)
   - Value: The actual WebSocket object
   - **Why?** We need to remember who is connected so we can send them messages

2. **`self.subscriptions: Dict[str, Set[str]]`**
   - Tracks what each connection is subscribed to
   - Key: Connection ID (e.g., `"conn_1"`)
   - Value: Set of log sources (e.g., `{"auth", "ufw"}` or `{"all"}`)
   - **Why?** Not everyone wants all logs - some only want "auth" logs, some want "all"

3. **`self.lock = threading.Lock()`**
   - **Thread safety** - prevents race conditions
   - **Why?** Multiple threads might try to add/remove connections at the same time
   - **How?** `with self.lock:` ensures only ONE thread can modify data at a time

4. **`self.connection_counter = 0`**
   - Generates unique IDs: `conn_1`, `conn_2`, `conn_3`, etc.
   - **Why?** Each connection needs a unique identifier

5. **`self.loop: Optional[asyncio.AbstractEventLoop]`**
   - Stores the async event loop
   - **Why?** WebSockets are async, but log ingestion runs in sync threads
   - **How?** We'll use this to bridge sync → async

6. **`self.executor = ThreadPoolExecutor(...)`**
   - A thread pool for running async code from sync threads
   - **Why?** Fallback if event loop isn't available

---

## 🔌 **Connection Management**

### `add_connection(websocket: WebSocket) -> str`

**What it does:**
- Adds a new WebSocket connection to our list
- Returns a unique connection ID

**Step by step:**
```python
def add_connection(self, websocket: WebSocket) -> str:
    with self.lock:  # ← Thread-safe: only one thread can do this at a time
        self.connection_counter += 1  # Increment counter: 1, 2, 3...
        connection_id = f"conn_{self.connection_counter}"  # Create ID: "conn_1"
        self.connections[connection_id] = websocket  # Store the websocket
        self.subscriptions[connection_id] = set()  # Initialize empty subscriptions
        return connection_id  # Return the ID
```

**When is this called?**
- When a client connects via WebSocket (see `websocket.py` line 29)

---

### `remove_connection(connection_id: str)`

**What it does:**
- Removes a connection when client disconnects
- Cleans up both the connection and its subscriptions

**Step by step:**
```python
def remove_connection(self, connection_id: str):
    with self.lock:  # Thread-safe
        if connection_id in self.connections:
            del self.connections[connection_id]  # Remove websocket
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]  # Remove subscriptions
```

**When is this called?**
- When client disconnects (see `websocket.py` line 108)

---

## 📡 **Subscription Management**

### `subscribe(connection_id: str, log_source: str)`

**What it does:**
- Adds a log source to a connection's subscription list

**Example:**
- Connection `conn_1` subscribes to `"auth"` logs
- Now `self.subscriptions["conn_1"] = {"auth"}`

**Step by step:**
```python
def subscribe(self, connection_id: str, log_source: str):
    with self.lock:
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].add(log_source)  # Add to set
```

**When is this called?**
- Client sends: `{"type": "subscribe", "log_source": "auth"}` (see `websocket.py` line 53)

---

### `unsubscribe(connection_id: str, log_source: str)`

**What it does:**
- Removes a log source from a connection's subscription list

**Step by step:**
```python
def unsubscribe(self, connection_id: str, log_source: str):
    with self.lock:
        if connection_id in self.subscriptions:
            self.subscriptions[connection_id].discard(log_source)  # Remove from set
```

---

### `is_subscribed(connection_id: str, log_source: str) -> bool`

**What it does:**
- Checks if a connection should receive logs from a specific source
- Returns `True` if:
  - Connection is subscribed to that specific source, OR
  - Connection is subscribed to `"all"`

**Step by step:**
```python
def is_subscribed(self, connection_id: str, log_source: str) -> bool:
    with self.lock:
        if connection_id in self.subscriptions:
            subscriptions = self.subscriptions[connection_id]
            # Check if subscribed to specific source OR "all"
            return log_source in subscriptions or "all" in subscriptions
        return False
```

---

## 🚀 **The Core: Broadcasting Logs**

### `broadcast(log_source: str, raw_line: str)` - **SYNC Method**

**What it does:**
- This is the **main entry point** called from log ingestion threads
- It's **synchronous** (not async) because log ingestion runs in regular threads
- It bridges sync → async to actually send the logs

**When is this called?**
- From `log_ingestor.py` when a new log line is read (line 77, 100, etc.)

**Step by step:**
```python
def broadcast(self, log_source: str, raw_line: str):
    # 1. Validate input
    if not raw_line or not raw_line.strip():
        return  # Skip empty lines
    
    # 2. Check if we have an event loop
    if self.loop and self.loop.is_running():
        # 3. Schedule async broadcast (from sync thread!)
        asyncio.run_coroutine_threadsafe(
            self._broadcast_async(log_source, raw_line),
            self.loop
        )
    else:
        # 4. Fallback: run in executor thread
        self.executor.submit(
            lambda: asyncio.run(self._broadcast_async(log_source, raw_line))
        )
```

**Key Concept: `asyncio.run_coroutine_threadsafe()`**
- Allows a **sync thread** to schedule an **async function** to run in the event loop
- This is the bridge between sync (log ingestion) and async (WebSocket sending)

---

### `_broadcast_async(log_source: str, raw_line: str)` - **ASYNC Method**

**What it does:**
- Actually sends the log to all subscribed WebSocket clients
- This is **async** because WebSocket operations are async

**Step by step:**

#### Step 1: Create the message
```python
message = {
    "type": "raw_log",
    "log_source": log_source,  # e.g., "auth"
    "raw_line": raw_line.strip(),  # The actual log line
    "timestamp": datetime.utcnow().isoformat() + "Z"  # When it was received
}
message_json = json.dumps(message)  # Convert to JSON string
```

#### Step 2: Find all subscribed connections (WITH lock)
```python
connections_to_send = []
websockets_to_send = []
with self.lock:  # Thread-safe access
    for conn_id, subscriptions in self.subscriptions.items():
        # Check if subscribed to this source or "all"
        if "all" in subscriptions or log_source in subscriptions:
            websocket = self.connections.get(conn_id)
            if websocket:
                connections_to_send.append(conn_id)
                websockets_to_send.append(websocket)
```

**Why get the list first?**
- We want to **minimize lock time**
- Get the list quickly, then release the lock
- Send messages **without** holding the lock (sending can be slow)

#### Step 3: Send to all connections in parallel (WITHOUT lock)
```python
if websockets_to_send:
    send_tasks = []
    for websocket in websockets_to_send:
        send_tasks.append(self._send_safe(websocket, message_json))
    
    # Wait for all sends to complete (or fail)
    results = await asyncio.gather(*send_tasks, return_exceptions=True)
```

**Key Concept: `asyncio.gather()`**
- Sends to all WebSockets **concurrently** (in parallel)
- Much faster than sending one-by-one
- `return_exceptions=True` means errors won't crash the whole operation

#### Step 4: Clean up disconnected connections
```python
disconnected = []
for i, result in enumerate(results):
    if isinstance(result, Exception) or result is False:
        disconnected.append(connections_to_send[i])

if disconnected:
    with self.lock:
        for conn_id in disconnected:
            self.remove_connection(conn_id)
```

**Why?**
- If sending fails, the connection is probably dead
- Remove it so we don't keep trying to send to it

---

### `_send_safe(websocket: WebSocket, message: str) -> bool`

**What it does:**
- Safely sends a message to a WebSocket
- Returns `True` if successful, `False` if failed

**Step by step:**
```python
async def _send_safe(self, websocket: WebSocket, message: str) -> bool:
    try:
        await websocket.send_text(message)  # Send the JSON string
        return True
    except Exception as e:
        print(f"✗ Error sending to websocket: {e}")
        return False  # Signal failure
```

**Why wrap in try/except?**
- Network errors happen (client disconnected, network issue, etc.)
- We don't want one failed send to crash the whole broadcast

---

## 🔄 **How It All Works Together**

### The Complete Flow:

1. **Log Ingestion** (`log_ingestor.py`):
   - Reads a new line from `/var/log/auth.log`
   - Calls `raw_log_broadcaster.broadcast("auth", line)` ← **SYNC call**

2. **Broadcaster** (`raw_log_broadcaster.py`):
   - `broadcast()` receives the call (sync thread)
   - Schedules `_broadcast_async()` to run in the event loop
   - `_broadcast_async()` finds all subscribed connections
   - Sends the log to each subscribed WebSocket ← **ASYNC operation**

3. **WebSocket Route** (`websocket.py`):
   - Client connects → `add_connection()` called
   - Client subscribes → `subscribe()` called
   - Client receives logs in real-time!

---

## 🧵 **Thread Safety Explained**

### Why Do We Need Locks?

**The Problem:**
- Multiple threads might modify `self.connections` at the same time
- Example:
  - Thread 1: Adding a connection
  - Thread 2: Removing a connection
  - **Result:** Data corruption!

**The Solution:**
```python
with self.lock:
    # Only ONE thread can be here at a time
    # Other threads wait until this one finishes
    self.connections[connection_id] = websocket
```

**When to use locks:**
- ✅ Reading/writing `self.connections`
- ✅ Reading/writing `self.subscriptions`
- ✅ Modifying `self.connection_counter`
- ❌ Sending WebSocket messages (already async-safe)

---

## 🔀 **Async/Sync Bridging Explained**

### The Challenge:
- **Log ingestion** runs in **sync threads** (regular Python threads)
- **WebSocket sending** must be **async** (FastAPI requirement)

### The Solution:

**Method 1: `asyncio.run_coroutine_threadsafe()`** (Preferred)
```python
# In sync thread:
asyncio.run_coroutine_threadsafe(
    self._broadcast_async(log_source, raw_line),  # Async function
    self.loop  # The event loop running in another thread
)
```
- Schedules the async function to run in the event loop
- Returns immediately (non-blocking)
- The event loop executes it when ready

**Method 2: ThreadPoolExecutor** (Fallback)
```python
# If no event loop available:
self.executor.submit(
    lambda: asyncio.run(self._broadcast_async(log_source, raw_line))
)
```
- Creates a new event loop in a separate thread
- Runs the async function there
- Less efficient, but works as fallback

---

## 📊 **Data Structures Summary**

### `self.connections`
```
{
    "conn_1": <WebSocket object>,
    "conn_2": <WebSocket object>,
    "conn_3": <WebSocket object>
}
```

### `self.subscriptions`
```
{
    "conn_1": {"auth", "ufw"},      # Subscribed to auth and ufw logs
    "conn_2": {"all"},              # Subscribed to all logs
    "conn_3": {"kern"}              # Subscribed to kern logs only
}
```

### Example Flow:
1. New log arrives: `"auth"` log line
2. Check subscriptions:
   - `conn_1` has `{"auth"}` → ✅ Send
   - `conn_2` has `{"all"}` → ✅ Send
   - `conn_3` has `{"kern"}` → ❌ Skip
3. Send to `conn_1` and `conn_2` only

---

## 🎓 **Key FastAPI/Async Concepts**

### 1. **WebSocket in FastAPI**
```python
from fastapi import WebSocket

@router.websocket("/logs/live")
async def websocket_live_logs(websocket: WebSocket):
    await websocket.accept()  # Accept the connection
    await websocket.send_text("Hello!")  # Send message
    data = await websocket.receive_text()  # Receive message
```

### 2. **Async Functions**
- Functions that can `await` other async operations
- Don't block the thread while waiting
- Must be called with `await` or scheduled in an event loop

### 3. **Event Loop**
- Manages all async operations
- FastAPI creates one automatically
- We store it in `self.loop` to use from sync threads

### 4. **Thread Safety**
- Multiple threads accessing shared data = danger!
- Use `threading.Lock()` to ensure only one thread modifies data at a time

---

## 🚨 **Common Questions**

### Q: Why not just make everything async?
**A:** Log file reading (`log_ingestor.py`) uses blocking I/O operations that work better in sync threads. The broadcaster bridges sync → async.

### Q: What happens if a client disconnects?
**A:** The `_send_safe()` method catches the exception, returns `False`, and we remove the connection in `_broadcast_async()`.

### Q: Can multiple clients subscribe to different sources?
**A:** Yes! Each connection has its own subscription set. `conn_1` can subscribe to `"auth"` while `conn_2` subscribes to `"all"`.

### Q: What is the singleton pattern?
**A:** Only ONE instance of `RawLogBroadcaster` exists (created at line 171). All parts of the app use the same instance, so all connections are managed in one place.

---

## 📝 **Summary**

This file implements a **real-time log broadcasting system** that:
1. ✅ Manages WebSocket connections
2. ✅ Tracks subscriptions per connection
3. ✅ Broadcasts logs to subscribed clients
4. ✅ Handles thread safety
5. ✅ Bridges sync (log ingestion) → async (WebSocket sending)
6. ✅ Cleans up disconnected clients automatically

It's the **middleware** between log files and frontend dashboards, enabling real-time log monitoring! 🎉
