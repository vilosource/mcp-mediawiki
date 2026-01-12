#!/bin/bash
set -e

echo "Starting mcp-mediawiki entrypoint"

# Default to running with arguments passed to container
# If no arguments, run with default stdio transport
if [ $# -eq 0 ]; then
    echo "No arguments provided, starting with stdio transport"
    exec python -u mcp_mediawiki.py
else
    echo "Starting with arguments: $@"
    exec python -u mcp_mediawiki.py "$@"
fi
