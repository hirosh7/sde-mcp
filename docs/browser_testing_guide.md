# Browser Testing Guide for Session ID Persistence

This guide helps you test session ID persistence using browser DevTools.

## Prerequisites

1. All services running: `docker-compose up -d`
2. Client UI accessible at: `http://localhost:8080`
3. Browser DevTools open (F12)

## Testing Steps

### 1. Open Browser DevTools

1. Navigate to `http://localhost:8080`
2. Press `F12` to open DevTools
3. Go to **Console** tab
4. Go to **Application** tab → **Local Storage** → `http://localhost:8080`

### 2. Clear Existing Session (Optional)

In Console tab, run:
```javascript
localStorage.removeItem('sde-mcp-session-id');
console.log('Session cleared');
```

### 3. Send First Query

1. Type a query in the input box: `"List all projects"`
2. Click Send or press Enter
3. **Watch Console** for `[Session]` messages:
   - Should see: `[Session] Using existing session_id: ...` or `[Session] Generated new session_id: ...`
   - Should see: `[Session] Sending query with session_id: ...`
   - Should see: `[Session] Payload being sent: ...`
   - Should see: `[Session] Session ID confirmed: ...` (if server returns same ID)

4. **Check Network Tab**:
   - Find request to `/api/v1/nlquery`
   - Click on it → **Payload** tab
   - Verify `session_id` is in the JSON payload

5. **Check Local Storage**:
   - Application tab → Local Storage → `http://localhost:8080`
   - Should see key: `sde-mcp-session-id` with a UUID value
   - **Note this value!**

### 4. Send Second Query (Same Tab)

1. Type another query: `"How many projects are there?"`
2. Click Send
3. **Verify Session ID**:
   - Console should show: `[Session] Using existing session_id: <same-id>`
   - Network → Payload should show the **same session_id**
   - Local Storage value should **not change**

### 5. Send Third Query

1. Type: `"What was the first project?"`
2. Click Send
3. **Verify again** that session_id is the same

### 6. Check Server Logs

In terminal, run:
```bash
docker-compose logs -f mcp-proxy | grep -E "\[MCP-Proxy\].*session_id|Using provided|Generated new"
```

You should see:
- `[MCP-Proxy] Using provided session_id: <your-session-id>` for all requests
- **NOT** `Generated new session_id` (unless it's the very first request)

### 7. Verify Redis Storage

```bash
# List all sessions
python3 scripts/inspect_redis.py

# View your specific session
python3 scripts/inspect_redis.py --session-id <your-session-id>
```

You should see multiple conversations stored under the same session ID.

## Expected Behavior

✅ **Correct Behavior:**
- Same session_id used for all queries in the same browser tab
- Console shows "Using existing session_id" after first query
- Network requests all include the same session_id
- Local Storage value doesn't change
- Server logs show "Using provided session_id" (not "Generated new")
- Redis shows multiple conversations under same session_id

❌ **Problem Indicators:**
- Different session_id for each query
- Console shows "Generated new session_id" multiple times
- Server logs show "Generated new session_id" instead of "Using provided"
- Local Storage value changes between requests
- Warning: `[Session] Session ID changed!`

## Debugging

### If Session IDs Are Changing

1. **Check Console Logs:**
   ```javascript
   // In browser console
   console.log('Current session:', localStorage.getItem('sde-mcp-session-id'));
   ```

2. **Check Network Requests:**
   - Open Network tab
   - Find `/api/v1/nlquery` requests
   - Check Payload → verify `session_id` is being sent
   - Check Response → verify `session_id` is returned

3. **Check Server Logs:**
   ```bash
   # All session-related logs
   docker-compose logs mcp-proxy mock-seaglass | grep -i session
   
   # Filter by your session ID
   docker-compose logs mcp-proxy | grep "<your-session-id>"
   ```

4. **Check Redis:**
   ```bash
   python3 scripts/inspect_redis.py
   ```

### Common Issues

**Issue: Session ID changes on every request**
- **Cause:** Client not sending session_id, or server not receiving it
- **Check:** Network tab → Payload → verify `session_id` field exists
- **Check:** Server logs for "Generated new session_id" messages

**Issue: Session ID persists but conversation history is lost**
- **Cause:** Redis TTL expired, or Redis connection issues
- **Check:** Redis TTL: `redis-cli TTL session:<session-id>`
- **Check:** Server logs for Redis errors

**Issue: Different session IDs in different browser tabs**
- **Cause:** Expected behavior - each tab has its own localStorage
- **Solution:** This is normal. Each browser tab maintains its own session.

## Automated Testing

For automated testing without browser, use:
```bash
./scripts/test_session_persistence.sh
```

This simulates browser behavior and verifies session ID persistence.

## Manual Browser Console Testing

You can also test directly in the browser console:

```javascript
// Get current session ID
const sessionId = localStorage.getItem('sde-mcp-session-id');
console.log('Current session:', sessionId);

// Send a test request
fetch('http://localhost:8003/api/v1/nlquery', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'test', session_id: sessionId })
})
  .then(r => r.json())
  .then(d => {
    console.log('Response session_id:', d.session_id);
    console.log('Match:', d.session_id === sessionId ? '✅' : '❌');
  });
```

Run this multiple times - the session_id should always match!

