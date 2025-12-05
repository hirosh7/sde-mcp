# Cursor MCP Configuration

This directory contains the MCP (Model Context Protocol) configuration for the SD Elements server.

## Setup

**IMPORTANT:** You need to add your SD Elements credentials to `.cursor/mcp.json`

1. Copy the example file: `cp .cursor/mcp.json.example .cursor/mcp.json`
2. Open `.cursor/mcp.json` in this directory
3. Replace the placeholder values:
   - `SDE_HOST`: Your SD Elements instance URL
   - `SDE_API_KEY`: Your API key from SD Elements Settings > API Tokens
4. **Choose the correct command path** based on your setup (see below)

## Command Path Configuration

The `command` field must point to a valid Python executable. Choose the option that matches your setup:

### Option 1: Using System Python (Default)
If you have the package installed globally or in your system Python:
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "python3",
      "args": ["-m", "sde_mcp_server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "SDE_HOST": "https://demo.sdelements.com",
        "SDE_API_KEY": "abc123def456..."
      }
    }
  }
}
```

### Option 2: Using Virtual Environment (`.venv`)
If you're using a standard virtual environment:
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": ["-m", "sde_mcp_server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "SDE_HOST": "https://demo.sdelements.com",
        "SDE_API_KEY": "abc123def456..."
      }
    }
  }
}
```

### Option 3: Using WSL Virtual Environment (`.venv-wsl`)
If you're using WSL and have a `.venv-wsl` directory:
```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "${workspaceFolder}/.venv-wsl/bin/python",
      "args": ["-m", "sde_mcp_server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "SDE_HOST": "https://demo.sdelements.com",
        "SDE_API_KEY": "abc123def456..."
      }
    }
  }
}
```

### Troubleshooting Command Path Issues

**Error: `spawn .venv/bin/python ENOENT`**
- This means the path doesn't exist. Check which virtual environment you're using:
  - If using `.venv-wsl`, use Option 3 above
  - If using `.venv`, use Option 2 above
  - If no virtual environment, use Option 1 above

**To find your Python path:**
1. In WSL, activate your virtual environment
2. Run: `which python` or `which python3`
3. Use that full path in the `command` field

## Security Note

**DO NOT commit `.cursor/mcp.json` with real credentials!**

The file `.cursor/mcp.json` is gitignored to prevent accidentally committing your API keys.
A template is provided at `.cursor/mcp.json.example`.

## After Setup

1. Save your changes to `.cursor/mcp.json`
2. Reload Cursor window (Cmd/Ctrl+Shift+P → "Developer: Reload Window")
3. Test with: `"List all projects in SD Elements"`

