#!/usr/bin/env bash
# Test session ID persistence by simulating browser requests
# This script tests the same flow a browser would use

set -euo pipefail

SEAGLASS_URL="http://localhost:8003"
SESSION_ID=""

echo "=== Session ID Persistence Test ==="
echo ""

# Simulate: Browser gets/creates session ID (like localStorage.getItem)
echo "Step 1: Simulating browser - getting session ID from 'localStorage'"
SESSION_ID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")
echo "Generated session ID: $SESSION_ID"
echo ""

# Test 1: First request
echo "Test 1: Sending first query with session_id..."
RESPONSE1=$(curl -s -X POST "$SEAGLASS_URL/api/v1/nlquery" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"List all projects\", \"session_id\": \"$SESSION_ID\"}")

SESSION_ID_RESPONSE1=$(echo "$RESPONSE1" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('session_id', 'MISSING'))" 2>/dev/null || echo "ERROR")

echo "  Request session_id: $SESSION_ID"
echo "  Response session_id: $SESSION_ID_RESPONSE1"
if [ "$SESSION_ID_RESPONSE1" = "$SESSION_ID" ]; then
    echo "  ✅ PASS: Session ID preserved"
else
    echo "  ❌ FAIL: Session ID changed!"
    exit 1
fi
echo ""

sleep 2

# Test 2: Second request (simulating browser sending same session_id from localStorage)
echo "Test 2: Sending second query with same session_id (simulating browser localStorage)..."
RESPONSE2=$(curl -s -X POST "$SEAGLASS_URL/api/v1/nlquery" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"How many projects are there?\", \"session_id\": \"$SESSION_ID\"}")

SESSION_ID_RESPONSE2=$(echo "$RESPONSE2" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('session_id', 'MISSING'))" 2>/dev/null || echo "ERROR")

echo "  Request session_id: $SESSION_ID"
echo "  Response session_id: $SESSION_ID_RESPONSE2"
if [ "$SESSION_ID_RESPONSE2" = "$SESSION_ID" ]; then
    echo "  ✅ PASS: Session ID preserved"
else
    echo "  ❌ FAIL: Session ID changed!"
    exit 1
fi
echo ""

sleep 2

# Test 3: Third request
echo "Test 3: Sending third query with same session_id..."
RESPONSE3=$(curl -s -X POST "$SEAGLASS_URL/api/v1/nlquery" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What was the first project?\", \"session_id\": \"$SESSION_ID\"}")

SESSION_ID_RESPONSE3=$(echo "$RESPONSE3" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('session_id', 'MISSING'))" 2>/dev/null || echo "ERROR")

echo "  Request session_id: $SESSION_ID"
echo "  Response session_id: $SESSION_ID_RESPONSE3"
if [ "$SESSION_ID_RESPONSE3" = "$SESSION_ID" ]; then
    echo "  ✅ PASS: Session ID preserved"
else
    echo "  ❌ FAIL: Session ID changed!"
    exit 1
fi
echo ""

# Check server logs
echo "=== Checking Server Logs ==="
echo "Looking for session ID in mcp-proxy logs..."
docker-compose logs mcp-proxy 2>&1 | grep -E "\[MCP-Proxy\].*$SESSION_ID|Using provided.*$SESSION_ID|Generated new" | tail -10 || echo "No matching logs found"
echo ""

echo "=== Test Summary ==="
echo "Session ID used: $SESSION_ID"
echo "All requests preserved the session ID: ✅"
echo ""
echo "To check Redis data:"
echo "  python3 scripts/inspect_redis.py --session-id $SESSION_ID"

