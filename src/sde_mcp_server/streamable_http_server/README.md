# SD Elements Streamable HTTP Server & Client

This directory contains the streamable HTTP transport implementation for the SD Elements MCP server, along with a client for testing and interacting with the server.

## Overview

The streamable HTTP transport allows the MCP server to be accessed over HTTP, making it easier to integrate with web-based clients and test the server functionality. The client (`sde_client.py`) provides an interactive interface for testing the server and converting JSON tool responses to natural language.

## Prerequisites

- Python 3.10 or higher
- Virtual environment with dependencies installed (see main README)
- SD Elements API credentials
- Anthropic API key (for the client)

## Configuration

### Environment Variables

Create a `.env` file in the project root directory with the following variables:

```env
# SD Elements MCP Server Configuration

# Your SD Elements instance URL (e.g., https://your-instance.sdelements.com)
SDE_HOST=https://your-instance.sdelements.com

# Your SD Elements API key
# Get this from: Settings > API Tokens in your SD Elements instance
SDE_API_KEY=your-api-key-here

# Optional: Anthropic API key (required for the streamable HTTP client)
# Get this from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**Getting Your API Keys:**

1. **SD Elements API Key:**
   - Log into your SD Elements instance
   - Go to **Settings** > **API Tokens**
   - Generate a new API token
   - Copy the token value for `SDE_API_KEY`

2. **Anthropic API Key (for client):**
   - Sign up at https://console.anthropic.com/
   - Go to **API Keys**
   - Create a new API key
   - Copy the key for `ANTHROPIC_API_KEY`

## Running the Server

The server runs on `http://0.0.0.0:8001/mcp` by default.

### Command Line

**Using uv (recommended):**
```bash
# From project root
uv run python -m sde_mcp_server
```

**Using Python directly:**
```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Run the server
python -m sde_mcp_server
```

**Expected output:**
```
FastMCP 2.13.1
Server name: sdelements-mcp
Transport: HTTP
Server URL: http://0.0.0.0:8001/mcp
```

The server will continue running until you stop it (Ctrl+C).

## Running the Client

The client connects to the server and provides an interactive chat interface. Make sure the server is running before starting the client.

### Command Line

**Using Python directly:**
```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Run the client
python src/sde_mcp_server/streamable_http_server/sde_client.py
```

**Expected output:**
```
Connected: Tools available = ['list_projects', 'get_project', ...]
[Calling tool: test_connection]
Great! The connection to SD Elements is successful...
Ask questions (type 'exit' to quit, 'clear' to reset conversation):

You: 
```

## VS Code Configuration

The project includes VS Code launch and task configurations for easy debugging and development.

### Launch Configurations (`.vscode/launch.json`)

The following configurations are available:

#### 1. Python: SD Elements Streamable HTTP Server
Runs the main SD Elements MCP server:
```json
{
    "name": "Python: SD Elements Streamable HTTP Server",
    "type": "debugpy",
    "request": "launch",
    "module": "sde_mcp_server",
    "console": "integratedTerminal",
    "justMyCode": true,
    "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
    },
    "cwd": "${workspaceFolder}"
}
```

#### 2. Python: SD Elements Client
Runs the interactive client (automatically starts the server first):
```json
{
    "name": "Python: SD Elements Client",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/src/sde_mcp_server/streamable_http_server/sde_client.py",
    "console": "integratedTerminal",
    "justMyCode": true,
    "preLaunchTask": "Start SD Elements MCP Server",
    "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
    },
    "cwd": "${workspaceFolder}"
}
```

**To use:**
1. Open VS Code in the project directory
2. Go to Run and Debug (F5)
3. Select "Python: SD Elements Streamable HTTP Server" or "Python: SD Elements Client"
4. Press F5 to start debugging

### Task Configurations (`.vscode/tasks.json`)

#### Start SD Elements MCP Server
Runs the server in the background:
```json
{
    "label": "Start SD Elements MCP Server",
    "type": "shell",
    "command": "${workspaceFolder}/.venv/Scripts/python.exe",
    "args": [
        "-m",
        "sde_mcp_server"
    ],
    "isBackground": true,
    "problemMatcher": {
        "pattern": {
            "regexp": "^.*$",
            "file": 1,
            "location": 2,
            "message": 3
        },
        "background": {
            "activeOnStart": true,
            "beginsPattern": ".*",
            "endsPattern": ".*Application startup complete.*|.*Uvicorn running.*|.*Started server process.*|.*Waiting for application startup.*"
        }
    },
    "options": {
        "env": {
            "PYTHONPATH": "${workspaceFolder}/src"
        }
    },
    "presentation": {
        "reveal": "always",
        "panel": "dedicated"
    }
}
```

**To use:**
1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Type "Tasks: Run Task"
3. Select "Start SD Elements MCP Server"

## Sample Interactions

The client provides an interactive interface for testing the server. Here are some sample interactions to verify functionality:

### 1. Test Connection

```
You: test connection
```

**Expected response:**
```
[Calling tool: test_connection]
Great! The connection to SD Elements is successful. I'm connected to the SD Elements instance at https://your-instance.sdelements.com and the API credentials are working properly.
```

### 2. List All Projects

```
You: list projects
```

**Expected response:**
```
[Calling tool: list_projects]
Here are all the projects in SD Elements:

## Projects Summary

I found **20 projects** across different business units and applications:

1. **A Mishara Training** (ID: 30775)
   - Profile: Blank
   - Survey Complete: ✓
   ...

Would you like me to get more details about any specific project?
```

### 3. Get Project Details

```
You: get project 29023
```

**Expected response:**
```
[Calling tool: get_project]
Here are the details for project 29023:

## Project: SEA-APPLICATION

**Basic Information:**
- **ID:** 29023
- **Name:** SEA-APPLICATION
- **Status:** Active (not archived)
- **Created:** July 15, 2024
- **Last Updated:** July 15, 2024

**Configuration:**
- **Application ID:** 8703
- **Business Unit:** 2140
- **Profile:** Blank (P1)
- **Risk Policy:** 1203
- **Survey Status:** Complete

**Components:**
- Apache
- Amazon VPC
- AWS Service
- Amazon EC2
- Software
- Amazon Route53
- Mobile App
- Android App

...
```

### 4. Sequential Queries

The client maintains conversation history, so you can reference previous results:

```
You: list projects
[Shows list of projects]

You: get project 24730
[Shows details for project 24730 (RMPClient)]

You: what's the profile for that project?
[Uses conversation history to reference project 24730]
```

### 5. Other Useful Commands

```
You: list applications
You: list profiles
You: list countermeasures for project 29023
You: get current user
You: list business units
```

## Features

### Server Features

- **Streamable HTTP Transport**: Server runs on HTTP endpoint `/mcp`
- **All SD Elements Tools**: Full access to all MCP tools for SD Elements
- **Environment-based Configuration**: Uses `.env` file for credentials
- **Error Handling**: Comprehensive error handling and validation

### Client Features

- **Natural Language Responses**: Automatically converts JSON tool responses to readable text
- **Conversation History**: Maintains context across multiple queries
- **Tool Call Visibility**: Shows which tools are being called in real-time
- **Unicode Handling**: Safely handles Unicode characters on Windows console
- **Error Handling**: Graceful error handling with detailed error messages

## Troubleshooting

### Server Issues

**Port already in use:**
```bash
# Windows: Find and kill process on port 8001
netstat -ano | findstr :8001
taskkill /PID <process_id> /F

# Linux/Mac: Find and kill process on port 8001
lsof -ti:8001 | xargs kill -9
```

**Configuration errors:**
- Verify `.env` file exists in project root
- Check that `SDE_HOST` and `SDE_API_KEY` are set correctly
- Ensure API key has proper permissions in SD Elements

**Server won't start:**
- Check Python version: `python --version` (should be 3.10+)
- Verify dependencies are installed: `pip list | grep fastmcp`
- Check for import errors in the console output

### Client Issues

**Connection errors:**
- Ensure the server is running before starting the client
- Verify server URL matches: `http://localhost:8001/mcp`
- Check that `ANTHROPIC_API_KEY` is set in `.env`

**Model not found errors:**
- Update the model name in `sde_client.py` (line 124)
- Check available models at https://console.anthropic.com/
- Common models: `claude-sonnet-4-20250514`, `claude-3-5-sonnet-20241022`

**Unicode encoding errors:**
- The client includes `_safe_print()` to handle Unicode on Windows
- If issues persist, ensure your terminal supports UTF-8 encoding

**Tool call failures:**
- Check server logs for detailed error messages
- Verify API credentials are correct
- Ensure the tool parameters are valid (e.g., project ID exists)

## Architecture

### Server (`server.py`)

- Uses FastMCP framework with streamable HTTP transport
- Initializes SD Elements API client on startup
- Loads library answers cache for survey management
- Runs on `http://0.0.0.0:8001/mcp`

### Client (`sde_client.py`)

- Connects to server via streamable HTTP client
- Uses Anthropic Claude API for natural language processing
- Formats tool results as natural language
- Maintains conversation history for context
- Handles multiple tool calls in sequence

## File Structure

```
streamable_http_server/
├── README.md                    # This file
├── sde_client.py                # Interactive client for testing
├── sample_server.py             # Sample/test server
├── sample_claude_client..py     # Sample client
└── CHANGES.md                   # Changes made to sample code
```

## Next Steps

- See the main [README.md](../../../README.md) for full MCP server documentation
- Check [CLAUDE_DESKTOP_SETUP.md](./CLAUDE_DESKTOP_SETUP.md) for Claude Desktop integration
- Review tool documentation in the main README for available operations

