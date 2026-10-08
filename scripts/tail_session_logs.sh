#!/usr/bin/env bash
# Tail logs and filter for session-related messages
# Usage:
#   ./scripts/tail_session_logs.sh                    # All session logs
#   ./scripts/tail_session_logs.sh <session-id>      # Filter by specific session ID
#   ./scripts/tail_session_logs.sh --service mcp-proxy  # Filter by service

set -euo pipefail

SERVICE=""
SESSION_ID=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--service SERVICE] [SESSION_ID]"
            echo ""
            echo "Tail logs and filter for session-related messages"
            echo ""
            echo "Options:"
            echo "  --service SERVICE    Filter logs from specific service (mcp-proxy, mock-seaglass, etc.)"
            echo "  SESSION_ID          Filter logs for specific session ID"
            echo ""
            echo "Examples:"
            echo "  $0                                    # All session logs from all services"
            echo "  $0 --service mcp-proxy                # Session logs from mcp-proxy only"
            echo "  $0 abc-123-def-456                    # Logs for specific session"
            echo "  $0 --service mcp-proxy abc-123-def-456  # Specific session from specific service"
            exit 0
            ;;
        *)
            if [[ -z "$SESSION_ID" ]]; then
                SESSION_ID="$1"
            else
                echo "Error: Multiple session IDs provided"
                exit 1
            fi
            shift
            ;;
    esac
done

# Build grep pattern
PATTERN="Session|session_id|session-id"

if [[ -n "$SESSION_ID" ]]; then
    # Escape special regex characters in session ID
    ESCAPED_SESSION_ID=$(echo "$SESSION_ID" | sed 's/[.*+?^${}()|[\]\\]/\\&/g')
    PATTERN="$PATTERN|$ESCAPED_SESSION_ID"
fi

# Build docker-compose command
if [[ -n "$SERVICE" ]]; then
    CMD="docker-compose logs -f $SERVICE"
else
    CMD="docker-compose logs -f"
fi

# Tail and grep
echo "Tailing logs for session-related messages..."
if [[ -n "$SESSION_ID" ]]; then
    echo "Filtering for session ID: $SESSION_ID"
fi
if [[ -n "$SERVICE" ]]; then
    echo "Service: $SERVICE"
fi
echo "---"

$CMD 2>&1 | grep --line-buffered -i -E "$PATTERN" | while IFS= read -r line; do
    # Colorize session IDs (UUID format)
    echo "$line" | sed -E 's/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/\x1b[33m\1\x1b[0m/gi'
done

