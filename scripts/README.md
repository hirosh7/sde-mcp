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

For more details, see the [Redis Inspection Guide](../docs/redis_inspection.md).

