# Seaglass-SDE MCP Workflow Prototype

This prototype demonstrates a complete natural language interface for SD Elements, integrating the MCP Proxy Service with Seaglass (via a mock service) and a web UI.

## Architecture

```
Client UI (Port 8080)
    ↓
Mock Seaglass (Port 8003)
    ↓
MCP Proxy Service (Port 8002)
    ↓
SDE MCP Server (Port 8001)
    ↓
SD Elements API
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- SD Elements API credentials
- Anthropic API key (for Claude)

### Setup

1. **Clone and checkout the feature branch:**

```bash
git checkout feature/add-streamable-http-to-server
git checkout -b feature/poc-sea-sde-mcp-workflow
```

2. **Configure environment variables:**

Create a `.env` file in the root directory:

```bash
# SD Elements API
SDE_HOST=https://your-instance.sdelements.com
SDE_API_KEY=your-sde-api-key-here

# Anthropic API (for Claude)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Optional: Claude model (defaults to claude-3-5-haiku-20241022)
CLAUDE_MODEL=claude-3-5-haiku-20241022

# Optional: Enable timing output
ENABLE_TIMING=false
```

3. **Start all services:**

```bash
docker-compose up --build
```

This will start:
- Client UI on `http://localhost:8080`
- Mock Seaglass on `http://localhost:8003`
- MCP Proxy Service on `http://localhost:8002`
- SDE MCP Server on `http://localhost:8001`

4. **Access the UI:**

Open your browser to `http://localhost:8080` and start sending natural language queries!

## Testing

### Via Web UI

1. Open `http://localhost:8080`
2. Click an example query or type your own
3. View the formatted response and response time

### Via API (Mock Seaglass)

```bash
curl -X POST http://localhost:8003/api/v1/nlquery \
  -H "Content-Type: application/json" \
  -d '{"query": "List all projects"}'
```

### Via API (MCP Proxy Direct)

```bash
curl -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all projects"}'
```

## Example Queries

- "List all projects"
- "Create a new project called Mobile Banking App"
- "Get details for project 29023"
- "Show me projects created this month"
- "What applications are in project 12345?"

## Service Details

### Client UI (`client-ui/`)

Simple web interface for sending queries and viewing responses.

- **Port:** 8080
- **Technology:** HTML/CSS/JavaScript
- **Purpose:** User-facing interface for testing

### Mock Seaglass (`mock-seaglass/`)

Lightweight service that simulates Seaglass for prototype testing.

- **Port:** 8003
- **Technology:** FastAPI
- **Purpose:** Simulate Seaglass integration point

### MCP Proxy Service (`mcp-proxy-service/`)

Core service that orchestrates Claude and MCP tool calls.

- **Port:** 8002
- **Technology:** FastAPI, Anthropic SDK, MCP Client
- **Purpose:** Bridge natural language to MCP tools

**Key Components:**
- `claude_adapter.py`: Uses Claude to select tools
- `mcp_client.py`: Connects to MCP server
- `response_formatter.py`: Formats JSON responses to natural language

### SDE MCP Server (`src/sde_mcp_server/`)

Existing MCP server that provides SD Elements tools.

- **Port:** 8001
- **Technology:** FastMCP
- **Purpose:** Expose SD Elements API as MCP tools

## Performance

Expected response times (Option C - Single Claude Call):

- Tool list fetch: ~100ms (cached)
- Claude tool selection: ~2-3s
- MCP tool execution: ~0.5-2s
- Local formatting: ~10ms
- **Total: ~3-5 seconds**

Compare to Option B (Two Claude Calls): ~10-12 seconds

## Troubleshooting

### Services won't start

1. Check that all required environment variables are set in `.env`
2. Verify Docker is running
3. Check logs: `docker-compose logs [service-name]`

### MCP Proxy can't connect to MCP Server

1. Ensure SDE MCP Server is running and healthy
2. Check `MCP_SERVER_URL` in MCP Proxy environment
3. Verify network connectivity: `docker-compose exec mcp-proxy ping sde-mcp-server`

### Claude API errors

1. Verify `ANTHROPIC_API_KEY` is set correctly
2. Check API key has sufficient credits
3. Verify model name matches your API access level

### No tools available

1. Check SDE MCP Server logs for connection issues
2. Verify `SDE_HOST` and `SDE_API_KEY` are correct
3. Test MCP Server directly: `curl http://localhost:8001/mcp/list_tools`

## Development

### Running Services Individually

**MCP Proxy:**
```bash
cd mcp-proxy-service
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key
export MCP_SERVER_URL=http://localhost:8001/mcp
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

**Mock Seaglass:**
```bash
cd mock-seaglass
pip install -r requirements.txt
export MCP_PROXY_URL=http://localhost:8002
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

**Client UI:**
```bash
cd client-ui/static
python -m http.server 8080
```

### Adding New Formatters

To add formatting for a new tool, edit `mcp-proxy-service/app/response_formatter.py`:

```python
def _format_new_tool(self, result: Dict[str, Any]) -> str:
    # Your formatting logic here
    return formatted_string

# Add to formatters dict:
formatters = {
    ...
    "new_tool": self._format_new_tool,
}
```

## Architecture Documentation

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed information about:
- All three architectural approaches (A, B, C)
- Trade-off analysis
- Performance comparisons
- Cost analysis

## Next Steps

1. **Production Integration:** Integrate MCP Proxy into real Seaglass service
2. **Enhanced Formatters:** Add more tool-specific formatters
3. **Caching:** Implement query result caching
4. **Error Handling:** Improve error messages and recovery
5. **Testing:** Add unit and integration tests

## Support

For issues or questions:
- Check service logs: `docker-compose logs`
- Review [ARCHITECTURE.md](./ARCHITECTURE.md) for design decisions
- See individual service READMEs for service-specific details

