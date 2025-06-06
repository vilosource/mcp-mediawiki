#!/bin/bash
set -e

echo "Starting entrypoint.sh"

if [ $# -eq 0 ]; then
    # No command-line arguments, run FastMCP server directly
    echo "Starting FastMCP server..."
    # Run with the -u flag for unbuffered output
    exec python -u mcp_mediawiki.py
else
    # Run with arguments passed to docker run/compose
    echo "Running with custom arguments: $@"
    exec "$@"
fi
