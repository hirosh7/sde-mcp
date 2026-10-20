# Redis Session Inspection Guide

This guide explains how to inspect and debug session data stored in Redis.

## Quick Start

### Using the Inspection Script

The `scripts/inspect_redis.py` script provides a convenient way to inspect Redis session data.

#### List All Sessions

```bash
# Using default Redis URL (redis://localhost:6379)
python scripts/inspect_redis.py

# Using custom Redis URL
python scripts/inspect_redis.py --redis-url redis://redis:6379
```

#### View a Specific Session

```bash
python scripts/inspect_redis.py --session-id <your-session-id>
```

#### Delete a Specific Session

```bash
python scripts/inspect_redis.py --delete <session-id>
```

#### Clear All Sessions (Use with Caution!)

```bash
python scripts/inspect_redis.py --clear-all
```

### Using Redis CLI Directly

If you have Redis CLI installed, you can inspect data directly:

#### Connect to Redis

```bash
# If Redis is running locally
redis-cli

# If Redis is in Docker
docker exec -it <redis-container-name> redis-cli

# Or if using docker-compose
docker-compose exec redis redis-cli
```

#### List All Session Keys

```bash
KEYS session:*
```

#### Get Session Data

```bash
# Get all conversations for a session (returns list)
LRANGE session:<session-id> 0 -1

# Get conversation count
LLEN session:<session-id>

# Get TTL (time to live)
TTL session:<session-id>
```

#### View Formatted Session Data

```bash
# Get all conversations and format with jq (if installed)
redis-cli LRANGE session:<session-id> 0 -1 | jq -r '.[] | "\(.timestamp) - \(.query)"'
```

#### Delete a Session

```bash
DEL session:<session-id>
```

#### Clear All Sessions

```bash
# Get all session keys and delete them
redis-cli --eval - 0 <<EOF
local keys = redis.call('keys', 'session:*')
for i=1,#keys do
    redis.call('del', keys[i])
end
return #keys
EOF
```

Or using a simple loop:

```bash
redis-cli KEYS "session:*" | xargs redis-cli DEL
```

## Understanding Session Data Structure

Each session is stored as a Redis list with the key format: `session:<session-id>`

Each conversation entry is a JSON object with the following structure:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "query": "List all projects",
  "response": "Here are the projects...",
  "metadata": {
    "tool_name": "list_projects",
    "success": true
  }
}
```

## Debugging Session Issues

### Check if Session Exists

```bash
redis-cli EXISTS session:<session-id>
```

### Check Session TTL

```bash
# Returns seconds until expiration (-1 = no expiration, -2 = key doesn't exist)
redis-cli TTL session:<session-id>
```

### Monitor Session Creation/Updates

```bash
# Monitor all Redis commands in real-time
redis-cli MONITOR | grep session:
```

### Check Redis Memory Usage

```bash
redis-cli INFO memory
```

## Common Issues

### Session IDs Changing Unexpectedly

If session IDs are changing even from the same browser tab:

1. **Check browser localStorage**: Open browser DevTools → Application → Local Storage → Check `sde-mcp-session-id`
2. **Check server logs**: Look for "Using provided session_id" vs "Generated new session_id" messages
3. **Verify session_id is being sent**: Check Network tab in DevTools → Request payload → `session_id` field
4. **Check Redis**: Verify the session exists and has data

### Session Data Not Persisting

1. **Check Redis connection**: Verify Redis is running and accessible
2. **Check TTL**: Sessions expire after 24 hours by default
3. **Check Redis memory**: Redis may evict keys if memory limit is reached
4. **Check logs**: Look for Redis connection errors in server logs

### Session Data Corrupted

If you see JSON parsing errors:

1. **Inspect raw data**: `redis-cli LRANGE session:<session-id> 0 -1`
2. **Check for encoding issues**: Ensure Redis is configured with UTF-8 encoding
3. **Delete corrupted session**: Use `--delete` option or `DEL` command

## Environment Variables

The inspection script respects the following environment variables:

- `REDIS_URL`: Redis connection URL (default: `redis://localhost:6379`)

You can also pass it as a command-line argument:

```bash
python scripts/inspect_redis.py --redis-url redis://redis:6379
```

## Docker Compose Usage

If using docker-compose, Redis is accessible at `redis://redis:6379` from within containers:

```bash
# From host machine
python scripts/inspect_redis.py --redis-url redis://localhost:6379

# From within a container
python scripts/inspect_redis.py --redis-url redis://redis:6379
```

