"""
Integration Test Configuration

Shared fixtures and configuration for integration tests.

Environment Variables:
- MCP_SERVER_URL: Override MCP server URL (default: http://hx-mcp1-server:8081)
- ORCHESTRATOR_URL: Override orchestrator URL (default: http://hx-orchestrator-server:8000)
- QDRANT_URL: Override Qdrant URL (default: http://hx-vectordb-server:6333)
- TEST_TIMEOUT: Override default test timeout in seconds (default: 30)

Examples:
  # Run tests against different environment
  MCP_SERVER_URL=http://hx-mcp1-dev.dev-test.hana-x.ai:8081 pytest tests/integration/

  # Run tests in CI/CD with custom URLs
  export MCP_SERVER_URL=http://hx-mcp1-staging.dev-test.hana-x.ai:8081
  export ORCHESTRATOR_URL=http://hx-orchestrator-staging.dev-test.hana-x.ai:8000
  pytest tests/integration/
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_timeout():
    """
    Default timeout for integration tests (longer than unit tests).

    Override via TEST_TIMEOUT environment variable.
    """
    return int(os.getenv("TEST_TIMEOUT", "30"))  # seconds


@pytest.fixture(scope="session")
def mcp_server_url():
    """
    MCP server URL for integration tests.

    Override via MCP_SERVER_URL environment variable.
    Default: http://hx-mcp1-server:8081
    """
    return os.getenv("MCP_SERVER_URL", "http://hx-mcp1-server:8081")


@pytest.fixture(scope="session")
def orchestrator_url():
    """
    Orchestrator server URL for integration tests.

    Override via ORCHESTRATOR_URL environment variable.
    Default: http://hx-orchestrator-server:8000
    """
    return os.getenv("ORCHESTRATOR_URL", "http://hx-orchestrator-server:8000")


@pytest.fixture(scope="session")
def qdrant_url():
    """
    Qdrant server URL for integration tests.

    Override via QDRANT_URL environment variable.
    Default: http://hx-vectordb-server:6333
    """
    return os.getenv("QDRANT_URL", "http://hx-vectordb-server:6333")
