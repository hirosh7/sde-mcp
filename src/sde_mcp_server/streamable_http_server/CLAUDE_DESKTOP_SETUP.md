# Using SD Elements MCP Server with Claude Desktop

This guide explains how to configure Claude Desktop to use the SD Elements MCP server via streamable HTTP transport.

## Prerequisites

1. **Claude Desktop** installed (download from https://claude.ai/download)
2. **SD Elements MCP Server** running on `http://localhost:8001/mcp`
3. **Environment variables** configured in `.env`:
   - `SDE_HOST` - Your SD Elements host URL
   - `SDE_API_KEY` - Your SD Elements API key

## Option 1: Using the Updated Client (Recommended)

The updated `sde_client.py` now formats JSON responses as natural language automatically. This is the easiest way to test:

### Steps:

1. **Start the SD Elements MCP Server:**
   ```bash
   python -m sde_mcp_server
   ```
   Server will run on `http://0.0.0.0:8001/mcp`

2. **Run the client in a separate terminal:**
   ```bash
   python src/sde_mcp_server/streamable_http_server/sde_client.py
   ```

3. **Interact with the client:**
   - The client will automatically format JSON tool responses as natural language
   - Claude will generate conversational responses based on tool results
   - Type `clear` to reset conversation history
   - Type `exit` or `quit` to exit

### Features:

- ✅ **Automatic JSON formatting** - Tool results are converted to readable text
- ✅ **Natural language responses** - Claude generates conversational answers
- ✅ **Conversation history** - Maintains context across multiple queries
- ✅ **Tool call visibility** - Shows which tools are being called

## Option 2: Configure Claude Desktop (Advanced)

Claude Desktop can be configured to connect directly to MCP servers. However, **Claude Desktop currently only supports stdio transport**, not streamable HTTP transport.

### Workaround: Use a Bridge/Proxy

Since Claude Desktop doesn't natively support streamable HTTP, you have two options:

#### Option 2a: Use the Python Client (Recommended)

Use the updated `sde_client.py` which provides a better experience than raw Claude Desktop integration:
- Better formatting of JSON responses
- More control over the conversation flow
- Easier debugging

#### Option 2b: Create a Bridge Server

You could create a bridge server that:
1. Accepts stdio connections (for Claude Desktop)
2. Forwards requests to the streamable HTTP server
3. Returns responses back to Claude Desktop

This is more complex and not recommended unless you specifically need Claude Desktop integration.

## Testing the Client

### Example Queries:

```python
# Test connection
"Test the connection to SD Elements"

# List projects
"List all projects in SD Elements"

# Get project details
"Show me details about project ID 123"

# Create a project
"Create a new project called 'My Test Project'"
```

## Troubleshooting

### Server not starting:
- Check that port 8001 is not in use: `netstat -ano | findstr :8001`
- Verify `.env` file has `SDE_HOST` and `SDE_API_KEY` set

### Client connection errors:
- Ensure the server is running before starting the client
- Check the server URL matches: `http://localhost:8001/mcp`
- Verify `ANTHROPIC_API_KEY` is set in `.env`

### JSON formatting issues:
- The client automatically handles JSON parsing
- If you see raw JSON, check that the tool response structure matches expected format
- Some complex nested structures may still show as formatted JSON

## Differences from Claude Desktop

The updated client provides several advantages over direct Claude Desktop integration:

1. **Better formatting** - JSON responses are automatically converted to natural language
2. **Conversation flow** - Tool results are sent back to Claude for natural language generation
3. **Debugging** - You can see tool calls and responses in real-time
4. **Flexibility** - Easy to customize the conversation flow and formatting

## Future: Native Claude Desktop Support

When Claude Desktop adds support for streamable HTTP transport, you'll be able to configure it directly in the Claude Desktop config file (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows).

Expected configuration format (when supported):
```json
{
  "mcpServers": {
    "sde-elements": {
      "url": "http://localhost:8001/mcp",
      "transport": "streamable-http"
    }
  }
}
```

