"""
Integration Test Configuration

Shared fixtures and configuration for integration tests.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_timeout():
    """Default timeout for integration tests (longer than unit tests)"""
    return 30  # seconds


@pytest.fixture(scope="session")
def mcp_server_url():
    """MCP server URL for integration tests"""
    return "http://hx-mcp1-server:8081"


@pytest.fixture(scope="session")
def orchestrator_url():
    """Orchestrator server URL for integration tests"""
    return "http://hx-orchestrator-server:8000"


@pytest.fixture(scope="session")
def qdrant_url():
    """Qdrant server URL for integration tests"""
    return "http://hx-vectordb-server:6333"
