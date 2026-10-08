# Session ID Debugging Guide

## Issue Fixed

Session IDs were changing even when prompting from the same browser tab. This has been fixed with improved session ID handling and logging.

## Changes Made

### 1. Server-Side Fix (`mcp-proxy-service/app/main.py`)

**Problem**: The original code used `request.session_id or str(uuid.uuid4())` which could generate a new UUID if `session_id` was an empty string or falsy.

**Fix**: Added proper handling for empty strings and None values:
- Strips whitespace from provided session_id
- Only treats non-empty strings as valid session IDs
- Adds detailed logging to track when session IDs are provided vs generated

**Code Changes**:
```python
# Before
session_id = request.session_id or str(uuid.uuid4())

# After
provided_session_id = None
if request.session_id:
    stripped = request.session_id.strip()
    if stripped:  # Only use non-empty strings
        provided_session_id = stripped

if provided_session_id:
    session_id = provided_session_id
    logger.info(f"Using provided session_id: {session_id}")
else:
    session_id = str(uuid.uuid4())
    logger.info(f"Generated new session_id: {session_id} (request.session_id was: {request.session_id!r})")
```

### 2. Client-Side Debugging (`client-ui/static/app.js`)

Added console logging to track session ID behavior:
- Logs when session ID is retrieved from localStorage
- Logs when a new session ID is generated
- Logs when session ID is sent to server
- Warns when server returns a different session ID
- Warns when server doesn't return a session ID

## How to Debug Session Issues

### Step 1: Check Browser Console

Open browser DevTools (F12) → Console tab and look for `[Session]` log messages:

```
[Session] Using existing session_id: abc-123-def-456
[Session] Sending query with session_id: abc-123-def-456
[Session] Session ID confirmed: abc-123-def-456
```

If you see warnings like:
```
[Session] Session ID changed! Old: abc-123, New: xyz-789
```

This indicates the server generated a new session ID instead of using the provided one.

### Step 2: Check Browser localStorage

Open DevTools → Application → Local Storage → `http://localhost:8080`:
- Look for key: `sde-mcp-session-id`
- Verify the value is a valid UUID
- Check if it changes between requests

### Step 3: Check Network Requests

Open DevTools → Network tab:
1. Find the request to `/api/v1/nlquery`
2. Click on it → Payload tab
3. Verify `session_id` is being sent: `{"query": "...", "session_id": "abc-123-def-456"}`
4. Check Response tab → verify `session_id` is returned

### Step 4: Check Server Logs

Look for session-related log messages in the MCP Proxy service logs:

```bash
# If using docker-compose
docker-compose logs -f mcp-proxy | grep -i session

# Look for messages like:
# "Using provided session_id: abc-123-def-456"
# "Generated new session_id: xyz-789 (request.session_id was: None)"
```

### Step 5: Inspect Redis Data

Use the Redis inspection script to verify sessions are being stored:

```bash
# List all sessions
python scripts/inspect_redis.py

# View specific session
python scripts/inspect_redis.py --session-id <your-session-id>
```

See [Redis Inspection Guide](./redis_inspection.md) for more details.

## Common Issues and Solutions

### Issue: Session ID changes on every request

**Symptoms**: Each request gets a new session ID

**Possible Causes**:
1. `session_id` not being sent in request payload
2. `session_id` is empty string or None
3. localStorage is being cleared
4. Different browser tabs/windows (each has its own localStorage)

**Debugging**:
1. Check Network tab → Request payload → verify `session_id` field exists
2. Check browser console for `[Session]` logs
3. Check server logs for "Generated new session_id" messages
4. Verify localStorage value hasn't changed

### Issue: Session ID persists but conversation history is lost

**Symptoms**: Same session ID but no previous conversations

**Possible Causes**:
1. Redis TTL expired (default: 24 hours)
2. Redis memory limit reached (keys evicted)
3. Redis connection issues
4. Session data not being saved

**Debugging**:
1. Check Redis: `python scripts/inspect_redis.py --session-id <session-id>`
2. Check Redis TTL: `redis-cli TTL session:<session-id>`
3. Check server logs for Redis errors
4. Verify session is being saved: Look for "Stored conversation in Redis" log messages

### Issue: Multiple sessions for same user

**Symptoms**: Multiple session IDs in Redis for same user

**Possible Causes**:
1. Multiple browser tabs/windows (each has its own localStorage)
2. localStorage cleared and regenerated
3. Different browsers/devices

**Solution**: This is expected behavior - each browser tab/window maintains its own session. If you want to share sessions across tabs, consider using sessionStorage or a shared storage mechanism.

## Testing Session Persistence

### Test 1: Same Tab, Multiple Queries

1. Open browser → Single tab
2. Send query: "List all projects"
3. Check console: Note session_id
4. Send query: "How many are there?"
5. Verify: Same session_id, conversation history should include both queries

### Test 2: Page Refresh

1. Send query: "List all projects"
2. Note session_id from console
3. Refresh page (F5)
4. Send query: "What was the first project?"
5. Verify: Same session_id, conversation history preserved

### Test 3: New Tab

1. Open new tab → Same URL
2. Send query: "List all projects"
3. Verify: Different session_id (expected - new localStorage)

## Redis Inspection Commands

Quick reference for inspecting Redis:

```bash
# List all sessions
python scripts/inspect_redis.py

# View specific session
python scripts/inspect_redis.py --session-id <session-id>

# Delete a session
python scripts/inspect_redis.py --delete <session-id>

# Using redis-cli directly
redis-cli KEYS "session:*"                    # List all session keys
redis-cli LRANGE session:<id> 0 -1            # Get session data
redis-cli TTL session:<id>                     # Check expiration time
redis-cli EXISTS session:<id>                  # Check if session exists
```

## Next Steps

If session IDs are still changing after these fixes:

1. **Check the logs**: Both client console and server logs
2. **Verify the flow**: Client → Mock Seaglass → MCP Proxy → Redis
3. **Test with curl**: Bypass browser to isolate the issue:
   ```bash
   curl -X POST http://localhost:8003/api/v1/nlquery \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "session_id": "test-session-123"}'
   ```
4. **Check Redis directly**: Verify data is being stored correctly

