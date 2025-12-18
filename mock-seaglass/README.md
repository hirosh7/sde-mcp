# Mock Seaglass Service

A lightweight mock service that simulates the Seaglass service for prototype testing. It forwards natural language queries to the MCP Proxy Service.

## Purpose

This service is used during prototype development to simulate how Seaglass would integrate with the MCP Proxy Service. In production, this functionality would be integrated directly into the real Seaglass service.

## API Endpoints

### `POST /api/v1/nlquery`

Forward a natural language query to the MCP Proxy.

**Request:**
```json
{
  "query": "List all projects"
}
```

**Response:**
```json
{
  "response": "Found 5 project(s):\n1. Mobile Banking App (ID: 12345)...",
  "success": true,
  "error": null
}
```

### `GET /api/v1/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "mock-seaglass"
}
```

## Configuration

Set environment variables:

- `MCP_PROXY_URL`: URL of the MCP Proxy Service (default: `http://localhost:8002`)

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
export MCP_PROXY_URL=http://localhost:8002

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

## Docker

```bash
# Build
docker build -t mock-seaglass .

# Run
docker run -p 8003:8003 \
  -e MCP_PROXY_URL=http://mcp-proxy:8002 \
  mock-seaglass
```

