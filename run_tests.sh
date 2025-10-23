#!/usr/bin/env bash
# Simple test runner script

set -e

echo "Running MCP DeepInfra tests..."

# Install test dependencies if needed
if ! uv sync --extra test --quiet; then
    echo "Failed to install test dependencies"
    exit 1
fi

# Run tests
pytest "$@"

echo "Tests completed successfully!"