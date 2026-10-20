# Script to rebuild client-ui with cache busting
Write-Host "🔄 Rebuilding client-ui container with latest changes..." -ForegroundColor Cyan
Write-Host ""

# Stop and remove old containers
Write-Host "Stopping containers..." -ForegroundColor Yellow
docker-compose down

# Remove old client-ui image to force rebuild
Write-Host "Removing old client-ui image..." -ForegroundColor Yellow
docker-compose rm -f client-ui
docker rmi sde-mcp-client-ui 2>$null

# Rebuild client-ui without cache
Write-Host "Rebuilding client-ui (no cache)..." -ForegroundColor Yellow
docker-compose build --no-cache client-ui

# Start all services
Write-Host "Starting all services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check status
Write-Host ""
Write-Host "✅ Services status:" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "🌐 Client UI should be available at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "🔗 Test page available at: http://localhost:8080/test-links.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 To verify the fix:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:8080 in your browser"
Write-Host "2. Press Ctrl+Shift+R (hard refresh) to clear browser cache"
Write-Host "3. Send a query: 'Create a project named Test in application 516'"
Write-Host "4. Check if the URL in the response is clickable"
Write-Host ""
Write-Host "📋 View logs with: docker-compose logs -f client-ui" -ForegroundColor Gray

