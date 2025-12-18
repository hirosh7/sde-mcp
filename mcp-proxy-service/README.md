# MCP Proxy Service

A microservice that bridges natural language queries to SD Elements MCP tools, using Claude for tool selection and local formatting for optimal performance.

## Overview

The MCP Proxy Service:
1. Receives natural language queries
2. Uses Claude (Haiku) to select the appropriate MCP tool
3. Executes the tool via the MCP server
4. Formats the JSON response into natural language locally

This approach reduces response time from ~10-12s (two Claude calls) to ~3-5s (single Claude call).

## API Endpoints

### `POST /api/v1/query`

Process a natural language query.

**Request:**
```json
{
  "query": "List all projects"
}
```

**Response:**
```json
{
  "response": "Found 5 project(s):\n1. Mobile Banking App (ID: 12345) - Active\n...",
  "success": true,
  "tool_name": "list_projects",
  "error": null
}
```

### `GET /api/v1/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "mcp-proxy",
  "mcp_server_connected": true
}
```

### `GET /api/v1/tools`

List available MCP tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "list_projects",
      "description": "List all SD Elements projects",
      "input_schema": {...}
    },
    ...
  ],
  "count": 10
}
```

## Configuration

Set environment variables:

- `MCP_SERVER_URL`: URL of the MCP server (default: `http://localhost:8001/mcp`)
- `ANTHROPIC_API_KEY`: Anthropic API key (required)
- `CLAUDE_MODEL`: Claude model to use (default: `claude-3-5-haiku-20241022`)
- `ENABLE_TIMING`: Enable timing output (default: `false`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8002`)

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your-key-here
export MCP_SERVER_URL=http://localhost:8001/mcp

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## Docker

```bash
# Build
docker build -t mcp-proxy .

# Run
docker run -p 8002:8002 \
  -e ANTHROPIC_API_KEY=your-key-here \
  -e MCP_SERVER_URL=http://mcp-server:8001/mcp \
  mcp-proxy
```

## Example Queries

- "List all projects"
- "Create a new project called Mobile Banking App"
- "Get details for project 29023"
- "Show me projects created this month"
- "Update project 12345 with description 'Updated project'"

