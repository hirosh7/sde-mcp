# SD Elements MCP Server - Deployment Guide

This guide provides deployment options for the SD Elements MCP Server using Node.js/TypeScript.

## Prerequisites

- SD Elements instance URL
- SD Elements API key (generate in SD Elements under Settings > API Tokens)
- Node.js 20+ installed
- npm or Docker (for containerized deployment)

## Configuration

All deployment methods require setting environment variables:

- `SDE_HOST`: Your SD Elements instance URL (e.g., `https://your-sdelements-instance.com`)
- `SDE_API_KEY`: Your SD Elements API key

## Deployment Options

### Option 1: Docker Compose (Recommended for Full Stack)

The easiest way to run the complete stack with HTTP transport:

```bash
# Clone the repository
git clone <repository-url>
cd sde-mcp

# Create .env file
cat > .env << EOF
SDE_HOST=https://your-sdelements-instance.com
SDE_API_KEY=your-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
EOF

# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f sde-mcp-server
```

This starts:
- **SDE MCP Server** on port 8001 (HTTP with StreamableHTTP transport)
- **MCP Proxy** on port 8002 (orchestrates Claude + MCP)
- **Client UI** on port 8080 (web interface)

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker documentation.

### Option 2: Stdio Mode (For Claude Desktop/Local MCP Clients)

Run the server in stdio mode for direct integration with MCP clients:

```bash
# Clone the repository
git clone <repository-url>
cd sde-mcp

# Install dependencies
npm install

# Build TypeScript
npm run build

# Set environment variables
export SDE_HOST="https://your-sdelements-instance.com"
export SDE_API_KEY="your-api-key-here"

# Run in stdio mode
npm start
```

### Option 3: HTTP Server Mode (Standalone)

Run just the MCP server with HTTP transport:

```bash
# Clone the repository
git clone <repository-url>
cd sde-mcp

# Install dependencies
npm install

# Build TypeScript
npm run build

# Set environment variables
export SDE_HOST="https://your-sdelements-instance.com"
export SDE_API_KEY="your-api-key-here"
export PORT=8001
export HOST=0.0.0.0

# Run HTTP server
npm run start:http
```

The server will be available at `http://localhost:8001/mcp`.

### Option 4: Development Installation

For development with auto-rebuild:

```bash
# Clone the repository
git clone <repository-url>
cd sde-mcp

# Install dependencies
npm install

# Set environment variables
export SDE_HOST="https://your-sdelements-instance.com"
export SDE_API_KEY="your-api-key-here"

# Run in development mode (stdio)
npm start

# Or run HTTP server in development
npm run start:http
```

## MCP Client Configuration

### Claude Desktop

Add this to your Claude Desktop configuration file:
- **macOS/Linux**: `~/.config/claude-desktop/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "node",
      "args": ["/absolute/path/to/sde-mcp/dist/index.js"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Note**: Replace `/absolute/path/to/sde-mcp` with the actual path to your cloned repository.

### Cline (VS Code Extension)

Add this to your Cline MCP settings:

```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "node",
      "args": ["/absolute/path/to/sde-mcp/dist/index.js"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Continue (VS Code Extension)

Add this to your Continue configuration:

```json
{
  "mcpServers": {
    "sde-elements": {
      "command": "node",
      "args": ["/absolute/path/to/sde-mcp/dist/index.js"],
      "env": {
        "SDE_HOST": "https://your-sdelements-instance.com",
        "SDE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cursor

To configure the SD Elements MCP server in Cursor:

#### Step 1: Build the Server
```bash
cd /path/to/sde-mcp
npm install
npm run build
```

#### Step 2: Configure Cursor MCP

Edit your Cursor MCP configuration file (`.cursor/mcp.json` in your workspace or global settings):

```json
{
  "sde-elements": {
    "command": "node",
    "args": ["/absolute/path/to/sde-mcp/dist/index.js"],
    "env": {
      "SDE_HOST": "https://your-sdelements-instance.com",
      "SDE_API_KEY": "your-api-key-here"
    }
  }
}
```

**Alternative: Using npm start**
```json
{
  "sde-elements": {
    "command": "npm",
    "args": ["start"],
    "cwd": "/absolute/path/to/sde-mcp",
    "env": {
      "SDE_HOST": "https://your-sdelements-instance.com",
      "SDE_API_KEY": "your-api-key-here"
    }
  }
}
```

#### Step 3: Restart Cursor
After adding the configuration, restart Cursor for the changes to take effect.

#### Step 4: Verify Connection
1. Open a chat or use the AI assistant in Cursor
2. The SD Elements tools should now be available
3. You can ask questions like "List all projects in SD Elements" or "Show me countermeasures for project ID 123"

#### Troubleshooting Cursor Configuration

**Server not starting:**
- Ensure Node.js 20+ is installed: `node --version`
- Verify the build completed: check that `dist/index.js` exists
- Verify your `SDE_HOST` and `SDE_API_KEY` are correct
- Check Cursor's output/logs for error messages

**Command not found errors:**
- Ensure Node.js is in your PATH
- If using npm start, ensure npm is in your PATH
- Verify the absolute path to the repository is correct

**Environment variable issues:**
- Make sure your SD Elements instance URL doesn't have a trailing slash
- Verify your API key has the necessary permissions in SD Elements

## Environment Configuration

### Using .env File

Create a `.env` file in your working directory:

```env
SDE_HOST=https://your-sdelements-instance.com
SDE_API_KEY=your-api-key-here
```

The server will automatically load these variables if the file is present.

### Using System Environment Variables

#### Linux/macOS

```bash
# Add to ~/.bashrc, ~/.zshrc, or similar
export SDE_HOST="https://your-sdelements-instance.com"
export SDE_API_KEY="your-api-key-here"

# Reload your shell
source ~/.bashrc
```

#### Windows (PowerShell)

```powershell
# Set environment variables
$env:SDE_HOST="https://your-sdelements-instance.com"
$env:SDE_API_KEY="your-api-key-here"

# Or set permanently
[System.Environment]::SetEnvironmentVariable("SDE_HOST", "https://your-sdelements-instance.com", "User")
[System.Environment]::SetEnvironmentVariable("SDE_API_KEY", "your-api-key-here", "User")
```

## Testing Your Installation

### Basic Connection Test

```bash
# Test that Node.js can run the server
cd /path/to/sde-mcp
npm run build
node dist/index.js --version
```

### HTTP Server Test

```bash
# Start the HTTP server
npm run start:http

# In another terminal, test the health endpoint
curl http://localhost:8001/health

# Expected response:
# {"status":"ok","timestamp":"..."}
```

### Full Integration Test with Docker

```bash
# Build and start all services
docker-compose up --build

# Visit the client UI
open http://localhost:8080

# Test creating a project through the UI
```

## Troubleshooting

### Common Issues

1. **"Command not found: node" or "Command not found: npm"**
   - Install Node.js 20+: https://nodejs.org/
   - Verify installation: `node --version` and `npm --version`

2. **"Cannot find module" errors**
   - Run `npm install` to install dependencies
   - Run `npm run build` to compile TypeScript

3. **"Authentication failed"**
   - Verify your `SDE_HOST` URL is correct (no trailing slash)
   - Check that your `SDE_API_KEY` is valid
   - Ensure the API key has proper permissions

4. **"Connection timeout"**
   - Check network connectivity
   - Verify firewall settings
   - Ensure SD Elements instance is accessible

5. **Docker build failures**
   - Ensure Docker is running: `docker ps`
   - Clear Docker cache: `docker-compose down && docker-compose build --no-cache`
   - Check logs: `docker-compose logs sde-mcp-server`

6. **TypeScript compilation errors**
   - Ensure you're using Node.js 20+
   - Delete node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check for linting errors: `npm run lint`

### Debug Mode

Run with detailed logging:

```bash
# Stdio mode with debug output
NODE_ENV=development npm start

# HTTP mode with debug output
NODE_ENV=development npm run start:http

# Docker mode with debug output
docker-compose logs -f sde-mcp-server
```

## Production Deployment

### Docker Compose (Recommended)

For production deployment with full monitoring:

```bash
# Clone repository
git clone <repository-url>
cd sde-mcp

# Create production .env file
cat > .env << EOF
SDE_HOST=https://your-sdelements-instance.com
SDE_API_KEY=your-api-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
NODE_ENV=production
EOF

# Start with production settings
docker-compose up -d

# Enable automatic restart
docker-compose restart unless-stopped

# Monitor logs
docker-compose logs -f
```

### Systemd Service (Linux)

Create a systemd service file `/etc/systemd/system/sde-mcp-server.service`:

```ini
[Unit]
Description=SD Elements MCP Server (HTTP)
After=network.target

[Service]
Type=simple
User=sde-mcp
WorkingDirectory=/opt/sde-mcp
Environment=SDE_HOST=https://your-sdelements-instance.com
Environment=SDE_API_KEY=your-api-key-here
Environment=PORT=8001
Environment=HOST=0.0.0.0
Environment=NODE_ENV=production
ExecStart=/usr/bin/node /opt/sde-mcp/dist/httpServer.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable sde-mcp-server
sudo systemctl start sde-mcp-server
sudo systemctl status sde-mcp-server
```

### Process Manager (PM2)

```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'sde-mcp-http',
    script: 'dist/httpServer.js',
    cwd: '/opt/sde-mcp',
    instances: 2,
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      SDE_HOST: 'https://your-sdelements-instance.com',
      SDE_API_KEY: 'your-api-key-here',
      PORT: 8001,
      HOST: '0.0.0.0'
    },
    error_file: '/var/log/sde-mcp/error.log',
    out_file: '/var/log/sde-mcp/output.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
}
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Kubernetes Deployment

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sde-mcp-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sde-mcp-server
  template:
    metadata:
      labels:
        app: sde-mcp-server
    spec:
      containers:
      - name: sde-mcp-server
        image: sde-mcp:latest
        ports:
        - containerPort: 8001
        env:
        - name: SDE_HOST
          valueFrom:
            secretKeyRef:
              name: sde-mcp-secrets
              key: sde-host
        - name: SDE_API_KEY
          valueFrom:
            secretKeyRef:
              name: sde-mcp-secrets
              key: sde-api-key
        - name: PORT
          value: "8001"
        - name: HOST
          value: "0.0.0.0"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: sde-mcp-service
spec:
  selector:
    app: sde-mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: LoadBalancer
```

## Security Considerations

- Store API keys securely (use environment variables, not hardcoded values)
- Use HTTPS endpoints only
- Regularly rotate API keys
- Monitor API usage and access logs
- Run the server with minimal required permissions
- Use virtual environments or containers to isolate dependencies

## Monitoring

### Health Checks

The HTTP server provides a health check endpoint:

```bash
# HTTP health check
curl http://localhost:8001/health

# Expected response:
# {"status":"ok","timestamp":"2025-12-23T..."}

# In Docker
docker-compose exec sde-mcp-server curl http://localhost:8001/health
```

### Logging

The server logs to stderr by default. Configure your deployment to capture and rotate logs:

```bash
# View logs in Docker
docker-compose logs -f sde-mcp-server

# View logs with PM2
pm2 logs sde-mcp-http

# View logs with systemd
journalctl -u sde-mcp-server -f
```

### Metrics

Monitor these key metrics:

- **HTTP response times**: Track `/mcp` endpoint performance
- **Error rates**: Monitor stderr for error logs
- **Memory usage**: Watch Node.js heap usage
- **Connection count**: Track active MCP sessions
- **API call latency**: Monitor SD Elements API response times

### Performance Tuning

#### Node.js Options

```bash
# Increase heap size for large workloads
NODE_OPTIONS="--max-old-space-size=4096" npm run start:http

# Enable V8 performance monitoring
NODE_OPTIONS="--trace-gc --trace-warnings" npm run start:http
```

#### PM2 Cluster Mode

For high availability, run multiple instances:

```javascript
// In ecosystem.config.js
instances: 'max',  // Use all CPU cores
exec_mode: 'cluster'
```

## Architecture Notes

### TypeScript/Node.js Implementation

The server is built with:
- **TypeScript 5.9+** - Type-safe implementation
- **MCP SDK** - Official Model Context Protocol SDK
- **Express** - HTTP server for StreamableHTTP transport
- **Zod** - Runtime type validation

### Transport Modes

1. **Stdio Mode** (`dist/index.js`)
   - For local MCP clients (Claude Desktop, Cline, Continue, Cursor)
   - Communication via stdin/stdout
   - Single client per process

2. **HTTP Mode** (`dist/httpServer.js`)
   - For web-based integrations and microservices
   - StreamableHTTP transport with session management
   - Multiple concurrent clients
   - RESTful health checks

### Migration from Python

This is a complete rewrite from Python to TypeScript. Key changes:

- ✅ **Faster startup**: No Python interpreter overhead
- ✅ **Better type safety**: Compile-time type checking
- ✅ **Native async/await**: Modern JavaScript patterns
- ✅ **Elicitation support**: Interactive user prompts
- ✅ **Session management**: Proper HTTP session handling
- ✅ **Health checks**: Built-in monitoring endpoint

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for migration details.

---

For additional support, see the main [README.md](README.md), [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md), or open an issue in the repository. 