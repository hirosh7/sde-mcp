# Quick Migration Checklist

Quick reference for migrating to context retention version.

## Pre-Migration

- [ ] Backup `docker-compose.yml` and `.env` files
- [ ] Stop current services: `docker-compose down`

## Configuration Updates

### 1. Update `.env` file

Add these lines:

```bash
REDIS_URL=redis://redis:6379
SESSION_TTL_HOURS=24
SESSION_MAX_CONVERSATIONS=50
LOG_LEVEL=INFO
```

### 2. Update `docker-compose.yml`

Add Redis service and update mcp-proxy dependencies (see [full guide](./MIGRATION_CONTEXT_RETENTION.md#step-3-update-docker-composeyml))

### 3. Update `mcp-proxy-service/requirements.txt`

Ensure it includes:
```
redis>=5.0.0
```

## Migration

```bash
# Rebuild services
docker-compose build

# Start all services
docker-compose up -d

# Verify Redis is running
docker-compose logs redis | grep "Ready to accept"
```

## Verification

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check mcp-proxy connected to Redis
docker-compose logs mcp-proxy | grep -i "Connected to Redis"
```

## Test Context Retention

1. Open `http://localhost:8080` (tested with Chrome)
2. Send query: "List all projects"
3. Send follow-up: "How many are there?"
4. Verify the second query understands context from the first

**Tested Configuration:**
- Claude Model: `claude-sonnet-4-5-20250929`
- Browser: Chrome (latest)

## Rollback

```bash
docker-compose down
cp docker-compose.yml.backup docker-compose.yml
cp .env.backup .env
docker-compose build
docker-compose up -d
```

For detailed instructions, see [MIGRATION_CONTEXT_RETENTION.md](./MIGRATION_CONTEXT_RETENTION.md)

