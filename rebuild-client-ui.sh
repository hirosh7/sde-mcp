#!/bin/bash
# Script to rebuild client-ui with cache busting

echo "🔄 Rebuilding client-ui container with latest changes..."
echo ""

# Stop and remove old containers
echo "Stopping containers..."
docker-compose down

# Remove old client-ui image to force rebuild
echo "Removing old client-ui image..."
docker-compose rm -f client-ui
docker rmi sde-mcp-client-ui 2>/dev/null || true

# Rebuild client-ui without cache
echo "Rebuilding client-ui (no cache)..."
docker-compose build --no-cache client-ui

# Start all services
echo "Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 5

# Check status
echo ""
echo "✅ Services status:"
docker-compose ps

echo ""
echo "🌐 Client UI should be available at: http://localhost:8080"
echo "🔗 Test page available at: http://localhost:8080/test-links.html"
echo ""
echo "📝 To verify the fix:"
echo "1. Open http://localhost:8080 in your browser"
echo "2. Press Ctrl+Shift+R (hard refresh) to clear browser cache"
echo "3. Send a query: 'Create a project named Test in application 516'"
echo "4. Check if the URL in the response is clickable"
echo ""
echo "📋 View logs with: docker-compose logs -f client-ui"

