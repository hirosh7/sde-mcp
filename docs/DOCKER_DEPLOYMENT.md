# Docker Deployment Guide

## Overview

The SDE MCP Server has been migrated from Python to TypeScript and now includes full Docker support with HTTP transport.

## Changes Made

### 1. Elicitation Support (`src/tools/project.ts`)
- Implemented interactive user prompting for project name when not provided
- Implemented profile selection prompting when auto-detection fails
- Uses `server.server.elicitInput()` for user interaction
- Graceful fallback when elicitation is not supported

### 2. HTTP Server Implementation (`src/httpServer.ts`)
- Created new HTTP server using `StreamableHTTPServerTransport`
- Session management with UUID-based session IDs
- Endpoints:
  - `POST /mcp` - Handles MCP requests and initialization
  - `GET /mcp` - Handles SSE streams for real-time updates
  - `DELETE /mcp` - Handles session cleanup
  - `GET /health` - Health check endpoint
- Graceful shutdown with cleanup handlers

### 3. Docker Support

#### Updated `Dockerfile.sde-mcp-server`
```dockerfile
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy TypeScript source and config files
COPY src/ ./src/
COPY tsconfig.json tsconfig.build.json ./

# Build TypeScript code
RUN npm run build

# Copy any additional needed files
COPY README.md LICENSE ./

# Expose port
EXPOSE 8001

# Run the MCP HTTP server
CMD ["node", "dist/httpServer.js"]
```

#### Updated `.dockerignore`
Added Node.js/TypeScript-specific ignores:
- `node_modules/`
- `dist/`
- `*.tsbuildinfo`
- Coverage and test files
- Workspace files

### 4. Package Scripts (`package.json`)
- Added `start:http` script: `npm run build && node dist/httpServer.js`
- Existing `start` script for stdio mode: `npm run build && node dist/index.js`

## Usage

### Docker Compose (Production)

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f sde-mcp-server

# Stop services
docker-compose down
```

### Local Development

#### HTTP Mode (for Docker/production):
```bash
npm install
npm run start:http
```

#### Stdio Mode (for Claude Desktop/local MCP):
```bash
npm install
npm start
```

### Environment Variables

Required environment variables (set in `.env` or docker-compose):
- `SDE_HOST` - SD Elements instance URL
- `SDE_API_KEY` - SD Elements API key
- `ANTHROPIC_API_KEY` - Anthropic API key (for proxy service)

Optional:
- `PORT` - HTTP server port (default: 8001)
- `HOST` - HTTP server host (default: 0.0.0.0)
- `CLAUDE_MODEL` - Claude model to use (default: claude-3-5-haiku-20241022)

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌──────────────────┐
│  Client UI  │────────▶│  MCP Proxy  │────────▶│  SDE MCP Server  │
│  (Port 8080)│         │  (Port 8002)│         │   (Port 8001)    │
└─────────────┘         └─────────────┘         └──────────────────┘
                               │                          │
                               │                          │
                               ▼                          ▼
                        ┌────────────┐          ┌─────────────────┐
                        │  Claude AI │          │  SD Elements    │
                        │    API     │          │      API        │
                        └────────────┘          └─────────────────┘
```

## Testing

1. **Health Check**:
   ```bash
   curl http://localhost:8001/health
   ```
   Expected: `{"status":"ok","timestamp":"..."}`

2. **MCP Connection**:
   Use the client-ui at http://localhost:8080 to interact with the MCP server

3. **Test Elicitation**:
   - Create a project without providing a name
   - The system should prompt you for the project name
   - If profile can't be auto-detected, it will prompt for profile selection

## Troubleshooting

### Build Fails in Docker

Check TypeScript compilation:
```bash
npm run build
```

### Server Won't Start

1. Check environment variables are set
2. Verify port 8001 is not in use:
   ```bash
   docker ps
   netstat -ano | findstr :8001  # Windows
   lsof -i :8001                  # Linux/Mac
   ```

### Elicitation Not Working

Elicitation requires:
- Client must support MCP elicitation protocol
- Connected via compatible MCP client (Claude, custom client)
- If elicitation fails, tool returns error with required parameters

## Migration from Python

The Python version is still available in the `src/sde_mcp_server/` directory but is no longer used in Docker. The TypeScript version provides:

✅ Better type safety
✅ Faster execution
✅ Modern async/await patterns
✅ Built-in session management
✅ Compatible with latest MCP SDK features
✅ Elicitation support

## Next Steps

1. **Build**: `docker-compose up --build -d`
2. **Test**: Visit http://localhost:8080
3. **Monitor**: `docker-compose logs -f`
4. **Develop**: Make changes and rebuild

## Branch

All changes are in the `feature/poc-add-elicitation` branch:
- Elicitation implementation
- HTTP server support
- Docker deployment configuration
- Updated documentation

To merge into main, create a PR from this branch.

