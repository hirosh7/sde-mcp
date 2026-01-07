#!/bin/bash

# Test script for the Mill Grinder prompt
# Tests: "Get all the tasks from the Mill Grinder project and summarize them by phase, task id and task title"

MCP_PROXY_URL="${MCP_PROXY_URL:-http://localhost:8002}"
SESSION_ID=$(uuidgen 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")

echo "=========================================="
echo "Testing Mill Grinder Prompt"
echo "=========================================="
echo "Session ID: $SESSION_ID"
echo "MCP Proxy URL: $MCP_PROXY_URL"
echo ""
echo "Query: 'Get all the tasks from the Mill Grinder project and summarize them by phase, task id and task title'"
echo ""

START_TIME=$(date +%s)

RESPONSE=$(curl -s -X POST "$MCP_PROXY_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Get all the tasks from the Mill Grinder project and summarize them by phase, task id and task title\", \"session_id\": \"$SESSION_ID\"}")

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "Response received in ${DURATION} seconds"
echo ""
echo "=========================================="
echo "Full Response:"
echo "=========================================="

python3 << 'PYTHON_SCRIPT'
import sys
import json

try:
    data = json.load(sys.stdin)
    print(f"Success: {data.get('success', False)}")
    print(f"Tool: {data.get('tool_name', 'N/A')}")
    print(f"Session ID: {data.get('session_id', 'N/A')}")
    print(f"Error: {data.get('error', 'None')}")
    print()
    print('=' * 80)
    print('FORMATTED RESPONSE:')
    print('=' * 80)
    response_text = data.get('response', '')
    print(response_text)
    print()
    print('=' * 80)
    print('Response Analysis:')
    print('=' * 80)
    print(f"Response length: {len(response_text)} characters")
    
    starts_with_json = response_text.strip().startswith(('{', '[', '```json'))
    print(f"Starts with JSON: {starts_with_json}")
    print(f"Contains 'Phase': {'Phase' in response_text or 'phase' in response_text}")
    print(f"Contains 'Task ID': {'Task ID' in response_text or 'task id' in response_text.lower()}")
    print(f"Contains 'Title': {'Title' in response_text or 'title' in response_text.lower()}")
    print(f"Contains 'summarize' or 'summary': {'summarize' in response_text.lower() or 'summary' in response_text.lower()}")
    
    if starts_with_json:
        print()
        print("WARNING: Response appears to be JSON, not formatted text!")
except Exception as e:
    print(f"Error parsing response: {e}")
    raw = sys.stdin.read()
    print(f"Raw response (first 1000 chars): {raw[:1000]}")
PYTHON_SCRIPT

echo "$RESPONSE" | python3 - << 'PYTHON_SCRIPT'
import sys
import json

try:
    data = json.load(sys.stdin)
    print(f"Success: {data.get('success', False)}")
    print(f"Tool: {data.get('tool_name', 'N/A')}")
    print(f"Session ID: {data.get('session_id', 'N/A')}")
    print(f"Error: {data.get('error', 'None')}")
    print()
    print('=' * 80)
    print('FORMATTED RESPONSE:')
    print('=' * 80)
    response_text = data.get('response', '')
    print(response_text)
    print()
    print('=' * 80)
    print('Response Analysis:')
    print('=' * 80)
    print(f"Response length: {len(response_text)} characters")
    
    starts_with_json = response_text.strip().startswith(('{', '[', '```json'))
    print(f"Starts with JSON: {starts_with_json}")
    print(f"Contains 'Phase': {'Phase' in response_text or 'phase' in response_text}")
    print(f"Contains 'Task ID': {'Task ID' in response_text or 'task id' in response_text.lower()}")
    print(f"Contains 'Title': {'Title' in response_text or 'title' in response_text.lower()}")
    print(f"Contains 'summarize' or 'summary': {'summarize' in response_text.lower() or 'summary' in response_text.lower()}")
    
    if starts_with_json:
        print()
        print("WARNING: Response appears to be JSON, not formatted text!")
except Exception as e:
    print(f"Error parsing response: {e}")
    raw = sys.stdin.read()
    print(f"Raw response (first 1000 chars): {raw[:1000]}")
PYTHON_SCRIPT

echo ""
echo "=========================================="
