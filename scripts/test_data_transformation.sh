#!/bin/bash

# Test script for data transformation functionality
# Tests the fix for handling data transformation requests without tool calls

MCP_PROXY_URL="${MCP_PROXY_URL:-http://localhost:8002}"
SESSION_ID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")

echo "=========================================="
echo "Testing Data Transformation Fix"
echo "=========================================="
echo "Session ID: $SESSION_ID"
echo "MCP Proxy URL: $MCP_PROXY_URL"
echo ""

# Step 1: Get countermeasures for project 686 (this will call a tool)
echo "Step 1: Retrieving countermeasures for project 686..."
echo "Query: 'List countermeasures for project 686'"
echo ""

RESPONSE1=$(curl -s -X POST "$MCP_PROXY_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"List countermeasures for project 686\", \"session_id\": \"$SESSION_ID\"}")

echo "Response 1 (Status):"
echo "$RESPONSE1" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  Success: {data.get('success', False)}\")
    print(f\"  Tool: {data.get('tool_name', 'N/A')}\")
    print(f\"  Session ID: {data.get('session_id', 'N/A')}\")
    print(f\"  Response length: {len(data.get('response', ''))} chars\")
    print(f\"  Response preview: {data.get('response', '')[:200]}...\")
except Exception as e:
    print(f\"  Error parsing response: {e}\")
    print(f\"  Raw: {sys.stdin.read()[:500]}\")
" 2>/dev/null || echo "Failed to parse response"

echo ""
echo "---"
echo ""

# Step 2: Transform the data (this should NOT call a tool, just transform existing data)
echo "Step 2: Transforming the data (should NOT call a tool)..."
echo "Query: 'summarize that data by showing only task ID and Title'"
echo ""

RESPONSE2=$(curl -s -X POST "$MCP_PROXY_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"summarize that data by showing only task ID and Title\", \"session_id\": \"$SESSION_ID\"}")

echo "Response 2 (Status):"
echo "$RESPONSE2" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  Success: {data.get('success', False)}\")
    print(f\"  Tool: {data.get('tool_name', 'N/A')}\")
    print(f\"  Error: {data.get('error', 'None')}\")
    print(f\"  Session ID: {data.get('session_id', 'N/A')}\")
    print(f\"  Response length: {len(data.get('response', ''))} chars\")
    print(f\"\")
    print(f\"  Full Response:\")
    print(f\"  {'='*60}\")
    response_text = data.get('response', '')
    # Print first 1000 chars
    print(response_text[:1000])
    if len(response_text) > 1000:
        print(f\"  ... (truncated, total {len(response_text)} chars)\")
    print(f\"  {'='*60}\")
except Exception as e:
    print(f\"  Error parsing response: {e}\")
    print(f\"  Raw response:\")
    sys.stdin.seek(0)
    raw = sys.stdin.read()
    print(raw[:1000])
" 2>/dev/null || echo "Failed to parse response"

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "Expected behavior:"
echo "  - Step 1: Should call 'list_countermeasures' tool"
echo "  - Step 2: Should NOT call a tool, should transform data from Step 1"
echo "  - Step 2: tool_name should be null or 'None'"
echo "  - Step 2: success should be true"
echo ""

