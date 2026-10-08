# Scripts

Utility scripts for managing and debugging the SD Elements MCP project.

## Installation

Install script dependencies:

```bash
pip install -r scripts/requirements.txt
```

## Available Scripts

### `inspect_redis.py`

Inspect and manage Redis session data for the MCP Proxy service.

**Installation:**
```bash
pip install -r scripts/requirements.txt
```

**Usage:**
```bash
# List all sessions
python scripts/inspect_redis.py

# View a specific session
python scripts/inspect_redis.py --session-id <session-id>

# Delete a specific session
python scripts/inspect_redis.py --delete <session-id>

# Clear all sessions (use with caution!)
python scripts/inspect_redis.py --clear-all

# Use custom Redis URL
python scripts/inspect_redis.py --redis-url redis://redis:6379
```

**Environment Variables:**
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379`)

**Environment Variables:**
- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379`)

For more details, see the [Redis Inspection Guide](../docs/redis_inspection.md).

### `tail_session_logs.sh`

Tail Docker logs and filter for session-related messages. Useful for debugging session ID issues.

**Usage:**
```bash
# Tail all session-related logs from all services
./scripts/tail_session_logs.sh

# Filter logs from specific service
./scripts/tail_session_logs.sh --service mcp-proxy

# Filter logs for specific session ID
./scripts/tail_session_logs.sh abc-123-def-456

# Combine filters: specific session from specific service
./scripts/tail_session_logs.sh --service mcp-proxy abc-123-def-456
```

**Quick Command Alternatives:**

If you prefer direct commands:

```bash
# All session logs
docker-compose logs -f | grep -i -E "Session|session_id|session-id"

# Specific session ID
docker-compose logs -f | grep -i "abc-123-def-456"

# From specific service
docker-compose logs -f mcp-proxy | grep -i -E "Session|session_id"

# Colorize session IDs (UUID format)
docker-compose logs -f | grep -i -E "Session|session_id" | grep --color=always -E "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
```

### `test_session_persistence.sh`

Automated test script that simulates browser behavior to verify session ID persistence.

**Usage:**
```bash
./scripts/test_session_persistence.sh
```

This script:
- Generates a session ID (simulating browser localStorage)
- Sends 3 consecutive requests with the same session_id
- Verifies that the server preserves the session_id in all responses
- Checks server logs to confirm session_id was used (not regenerated)
- Provides instructions for checking Redis data

**Expected Output:**
```
✅ PASS: Session ID preserved (for all 3 requests)
```

If any test fails, the script exits with error code 1.

For manual browser testing, see the [Browser Testing Guide](../docs/browser_testing_guide.md).

