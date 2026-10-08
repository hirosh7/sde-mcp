# Migration Guide: Enabling Context Retention

This guide helps you migrate from the version without context retention to the version with Redis-based session context retention.

## Overview

**What's Changing:**
- **Before**: Each query is processed independently with no memory of previous conversations
- **After**: Conversations are stored in Redis, enabling context-aware responses across multiple queries

**New Components:**
- Redis service for session storage
- Session ID management in client and server
- Conversation history tracking

**Tested Configuration:**
- **Claude Model**: `claude-sonnet-4-5-20250929`
- **Browser**: Chrome (latest)
- **Session Storage**: Redis 7-alpine

## Prerequisites

- Docker and Docker Compose installed
- Existing `.env` file configured
- Current version running successfully

## Migration Steps

### Step 1: Backup Current Configuration

```bash
# Backup your current docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Backup your .env file
cp .env .env.backup
```

### Step 2: Update Environment Variables

Add the following Redis configuration to your `.env` file:

```bash
# Redis Configuration (for session context storage)
# Default: redis://localhost:6379 (for Docker Compose)
# For local Redis: redis://localhost:6379
# For external Redis: redis://your-redis-host:6379
REDIS_URL=redis://redis:6379

# Session expiration time in hours (default: 24)
SESSION_TTL_HOURS=24

# Maximum number of conversations per session (default: 50)
SESSION_MAX_CONVERSATIONS=50

# Optional: Log level for debugging (default: INFO)
LOG_LEVEL=INFO
```

**Note**: If you're running services locally (not in Docker), use `redis://localhost:6379` instead of `redis://redis:6379`.

### Step 3: Update docker-compose.yml

Add the Redis service to your `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  # Redis - In-memory storage for session context
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Update mcp-proxy service to include Redis dependency and environment variables
  mcp-proxy:
    # ... existing configuration ...
    environment:
      - MCP_SERVER_URL=http://sde-mcp-server:8001/mcp
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLAUDE_MODEL=${CLAUDE_MODEL:-claude-3-5-haiku-20241022}
      - CLAUDE_TOOL_SELECTION_MODEL=${CLAUDE_TOOL_SELECTION_MODEL:-claude-3-5-haiku-20241022}
      - ENABLE_TIMING=${ENABLE_TIMING:-false}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - SDE_HOST=${SDE_HOST}
      - REDIS_URL=redis://redis:6379
      - SESSION_TTL_HOURS=${SESSION_TTL_HOURS:-24}
      - SESSION_MAX_CONVERSATIONS=${SESSION_MAX_CONVERSATIONS:-50}
    depends_on:
      - sde-mcp-server
      - redis  # Add Redis dependency

  # Update mock-seaglass service to include logging
  mock-seaglass:
    # ... existing configuration ...
    environment:
      - MCP_PROXY_URL=http://mcp-proxy:8002
      - LOG_LEVEL=${LOG_LEVEL:-INFO}

# Add volumes section if it doesn't exist
volumes:
  redis-data:
```

### Step 4: Update Dependencies

The `mcp-proxy-service/requirements.txt` should include:

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
anthropic>=0.18.0
python-dotenv>=1.0.0
mcp>=1.0.0
pydantic>=2.0.0
redis>=5.0.0
```

If `redis>=5.0.0` is missing, add it.

### Step 5: Stop Current Services

```bash
# Stop all running services
docker-compose down

# Optional: Remove old containers and volumes (if you want a clean start)
# WARNING: This will delete any existing data
# docker-compose down -v
```

### Step 6: Rebuild and Start Services

```bash
# Rebuild services with new configuration
docker-compose build

# Start all services (including Redis)
docker-compose up -d

# Check service status
docker-compose ps

# View logs to verify Redis is running
docker-compose logs redis
```

### Step 7: Verify Redis Connection

Check that Redis is accessible and the mcp-proxy can connect:

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check mcp-proxy logs for Redis connection
docker-compose logs mcp-proxy | grep -i redis
# Should see: "Connected to Redis at redis://redis:6379"
```

### Step 8: Test Context Retention

1. **Open the client UI**: `http://localhost:8080`
   - **Tested with**: Chrome browser (latest version)

2. **Send a query that creates context**:
   ```
   List all projects
   ```

3. **Send a follow-up query that references the previous**:
   ```
   How many projects are there?
   ```

4. **Verify context is working**:
   - The second query should understand "projects" refers to the list from the first query
   - Check browser console (F12) for `[Session]` log messages showing the same session_id
   - Verify session_id persists in browser localStorage (Application tab → Local Storage)

5. **Check Redis storage**:
   ```bash
   # Connect to Redis
   docker-compose exec redis redis-cli
   
   # List all session keys
   KEYS session:*
   
   # View a session's conversation history
   LRANGE session:<session-id> 0 -1
   ```

**Note**: This migration guide was tested with:
- Claude model: `claude-sonnet-4-5-20250929`
- Browser: Chrome (latest version)
- Redis: 7-alpine

## Configuration Options

### Redis URL

**Docker Compose (default)**:
```bash
REDIS_URL=redis://redis:6379
```

**Local Redis**:
```bash
REDIS_URL=redis://localhost:6379
```

**External Redis**:
```bash
REDIS_URL=redis://your-redis-host:6379
# With password:
REDIS_URL=redis://:password@your-redis-host:6379
```

### Session TTL

Control how long sessions are stored:

```bash
# 24 hours (default)
SESSION_TTL_HOURS=24

# 48 hours
SESSION_TTL_HOURS=48

# 1 hour (for testing)
SESSION_TTL_HOURS=1
```

### Maximum Conversations

Limit the number of conversations stored per session:

```bash
# 50 conversations (default)
SESSION_MAX_CONVERSATIONS=50

# 100 conversations
SESSION_MAX_CONVERSATIONS=100

# 10 conversations (for testing)
SESSION_MAX_CONVERSATIONS=10
```

## Troubleshooting

### Redis Connection Errors

**Error**: `Connection refused` or `Cannot connect to Redis`

**Solutions**:
1. Verify Redis service is running:
   ```bash
   docker-compose ps redis
   ```

2. Check Redis logs:
   ```bash
   docker-compose logs redis
   ```

3. Verify network connectivity:
   ```bash
   docker-compose exec mcp-proxy ping redis
   ```

4. Check REDIS_URL matches your setup:
   - Docker Compose: `redis://redis:6379`
   - Local: `redis://localhost:6379`

### Session IDs Not Persisting

**Symptoms**: Each query gets a new session ID

**Solutions**:
1. Check browser console for `[Session]` log messages
2. Verify localStorage is enabled in browser
3. Check server logs for session ID handling:
   ```bash
   docker-compose logs mcp-proxy | grep -i session
   ```

### Redis Memory Issues

**Error**: `OOM command not allowed`

**Solutions**:
1. Increase Redis memory limit in docker-compose.yml:
   ```yaml
   command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
   ```

2. Reduce SESSION_TTL_HOURS to expire sessions faster

3. Reduce SESSION_MAX_CONVERSATIONS to store fewer conversations

### Data Loss After Restart

**Note**: Redis data is stored in a Docker volume. If you run `docker-compose down -v`, the volume will be deleted.

**To preserve data**:
```bash
# Stop without removing volumes
docker-compose down

# Start again (data preserved)
docker-compose up -d
```

## Rollback

If you need to rollback to the version without context retention:

```bash
# Stop services
docker-compose down

# Restore backup
cp docker-compose.yml.backup docker-compose.yml
cp .env.backup .env

# Remove Redis service (if added)
# Edit docker-compose.yml to remove redis service and redis-data volume

# Remove Redis environment variables from .env
# Remove REDIS_URL, SESSION_TTL_HOURS, SESSION_MAX_CONVERSATIONS

# Rebuild and start
docker-compose build
docker-compose up -d
```

## What's New: Key Features

### 1. Session Persistence
- Each browser tab maintains its own session
- Sessions persist across page refreshes
- Sessions expire after configured TTL (default: 24 hours)

### 2. Conversation History
- Previous queries and responses are stored
- Claude uses history for context-aware responses
- History is limited to prevent memory issues

### 3. Follow-up Queries
- Queries like "How many are there?" work correctly
- References to "that project" or "the first one" are understood
- Context from previous operations is maintained

## Testing Checklist

- [ ] Redis service starts successfully
- [ ] MCP Proxy connects to Redis
- [ ] Client UI generates session IDs
- [ ] Session IDs persist across multiple queries
- [ ] Follow-up queries use context correctly
- [ ] Sessions expire after TTL
- [ ] Maximum conversations limit works
- [ ] Redis data persists after service restart

**Tested Environment:**
- **Claude Model**: `claude-sonnet-4-5-20250929`
- **Browser**: Chrome (latest version)
- **Session Storage**: Redis 7-alpine

## Next Steps

After migration:

1. **Monitor Redis usage**:
   ```bash
   docker-compose exec redis redis-cli INFO memory
   ```

2. **Inspect session data** (if inspection tools are available):
   ```bash
   # List all sessions
   docker-compose exec redis redis-cli KEYS "session:*"
   ```

3. **Adjust configuration** based on usage patterns:
   - Increase/decrease SESSION_TTL_HOURS
   - Adjust SESSION_MAX_CONVERSATIONS
   - Monitor Redis memory usage

## Support

If you encounter issues during migration:

1. Check service logs: `docker-compose logs <service-name>`
2. Verify environment variables: `docker-compose config`
3. Test Redis connectivity: `docker-compose exec redis redis-cli ping`
4. Review the [Context Retention System documentation](./context_retention_system.md)

## Summary

The migration adds Redis-based context retention, enabling:
- ✅ Context-aware conversations
- ✅ Follow-up query support
- ✅ Session persistence
- ✅ Automatic session expiration

The changes are backward-compatible - existing functionality continues to work, with the addition of context retention when session IDs are provided.

