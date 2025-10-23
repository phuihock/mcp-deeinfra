"""Pytest configuration and fixtures for MCP DeepInfra tests."""

import json
import os
import pytest
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def mcp_server():
    """Fixture that starts the MCP server as a subprocess and provides a client interface."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Start the server
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_deepinfra.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(project_root),
        env={**os.environ, "PYTHONPATH": str(project_root / "src")}
    )

    # Give the server a moment to start
    time.sleep(0.1)

    class MCPServerClient:
        def __init__(self, process):
            self.process = process
            self.request_id = 1

        def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
            """Send a JSON-RPC request to the server."""
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method,
                "params": params or {}
            }
            self.request_id += 1

            # Send request
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            # Read response (skip any log lines)
            while True:
                line = self.process.stdout.readline().strip()
                if line.startswith('{'):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue

        def send_notification(self, method: str, params: Dict[str, Any] = None):
            """Send a JSON-RPC notification to the server."""
            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {}
            }
            self.process.stdin.write(json.dumps(notification) + "\n")
            self.process.stdin.flush()

        def terminate(self):
            """Terminate the server process."""
            self.process.terminate()
            self.process.wait()

    client = MCPServerClient(process)

    # Initialize the server
    init_response = client.send_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    })

    assert "result" in init_response, f"Server initialization failed: {init_response}"

    # Send initialized notification
    client.send_notification("notifications/initialized")

    yield client

    # Cleanup
    client.terminate()