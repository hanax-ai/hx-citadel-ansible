"""
Pytest configuration and shared fixtures

Phase 2 Sprint 2.2: Automated Testing (TASK-031)
"""

import pytest
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
import httpx
import respx

# Add project root to Python path
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for end-to-end flows"
    )
    config.addinivalue_line(
        "markers", "mcp: Tests for MCP server functionality"
    )


# ============================================================================
# TEST ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration with server URLs and settings"""
    return {
        "mcp_server": {
            "host": "hx-mcp1-server",
            "port": 8081,
            "url": "http://hx-mcp1-server:8081",
        },
        "orchestrator": {
            "host": "hx-orchestrator-server",
            "port": 8000,
            "url": "http://hx-orchestrator-server:8000",
        },
        "qdrant": {
            "host": "hx-vectordb-server",
            "port": 6333,
            "url": "http://hx-vectordb-server:6333",
        },
        "ollama": {
            "host": "hx-ollama1",
            "port": 11434,
            "url": "http://hx-ollama1:11434",
        },
        "postgresql": {
            "host": "hx-sqldb-server",
            "port": 5432,
        },
        "redis": {
            "host": "hx-sqldb-server",
            "port": 6379,
        },
    }


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory"""
    return PROJECT_ROOT


@pytest.fixture
def roles_dir(project_root: Path) -> Path:
    """Get the roles directory"""
    return project_root / "roles"


@pytest.fixture
def templates_dir(roles_dir: Path) -> Path:
    """Get templates directory for a specific role"""
    def _get_templates(role_name: str) -> Path:
        return roles_dir / role_name / "templates"
    return _get_templates


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================

@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for testing"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def mock_http() -> Generator[respx.MockRouter, None, None]:
    """Mock HTTP requests for testing"""
    with respx.mock() as mock:
        yield mock


# ============================================================================
# MCP SERVER FIXTURES
# ============================================================================

@pytest.fixture
async def mcp_client(test_config: Dict[str, Any]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client configured for MCP server"""
    base_url = test_config["mcp_server"]["url"]
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def mcp_server_url(test_config: Dict[str, Any]) -> str:
    """MCP server base URL"""
    return test_config["mcp_server"]["url"]


# ============================================================================
# ORCHESTRATOR FIXTURES
# ============================================================================

@pytest.fixture
async def orchestrator_client(test_config: Dict[str, Any]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client configured for orchestrator"""
    base_url = test_config["orchestrator"]["url"]
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def orchestrator_url(test_config: Dict[str, Any]) -> str:
    """Orchestrator base URL"""
    return test_config["orchestrator"]["url"]


# ============================================================================
# QDRANT FIXTURES
# ============================================================================

@pytest.fixture
async def qdrant_client(test_config: Dict[str, Any]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client configured for Qdrant"""
    base_url = test_config["qdrant"]["url"]
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def qdrant_url(test_config: Dict[str, Any]) -> str:
    """Qdrant base URL"""
    return test_config["qdrant"]["url"]


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_text() -> str:
    """Sample text for testing embeddings and queries"""
    return (
        "The HX-Citadel Shield is a production-ready RAG pipeline "
        "that integrates LightRAG, FastMCP, and Qdrant for semantic search."
    )


@pytest.fixture
def sample_query() -> str:
    """Sample query for testing retrieval"""
    return "What is HX-Citadel Shield?"


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Sample metadata for vector storage"""
    return {
        "source": "test_document",
        "type": "documentation",
        "created_at": "2025-10-11",
    }


@pytest.fixture
def sample_job_id() -> str:
    """Sample job ID for async operations"""
    return "test-job-12345"


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_orchestrator_response(mock_http: respx.MockRouter, orchestrator_url: str) -> respx.MockRouter:
    """Mock successful orchestrator responses"""
    # Health check
    mock_http.get(f"{orchestrator_url}/healthz").respond(
        json={"status": "healthy"}
    )

    # Job status
    mock_http.get(f"{orchestrator_url}/jobs/test-job-12345").respond(
        json={
            "status": "completed",
            "job_id": "test-job-12345",
            "result": {"success": True}
        }
    )

    return mock_http


@pytest.fixture
def mock_qdrant_response(mock_http: respx.MockRouter, qdrant_url: str) -> respx.MockRouter:
    """Mock successful Qdrant responses"""
    # Health check
    mock_http.get(f"{qdrant_url}/health").respond(
        json={"status": "ok"}
    )

    # Collections list
    mock_http.get(f"{qdrant_url}/collections").respond(
        json={
            "result": {
                "collections": [
                    {"name": "shield_knowledge_base"}
                ]
            }
        }
    )

    return mock_http


@pytest.fixture
def mock_circuit_breaker_open(mock_http: respx.MockRouter, orchestrator_url: str) -> respx.MockRouter:
    """Mock circuit breaker open state (service down)"""
    mock_http.route(url__startswith=orchestrator_url).respond(
        status_code=503,
        json={"error": "Service temporarily unavailable"}
    )
    return mock_http


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_test_state():
    """Reset test state between tests"""
    yield
    # Cleanup code here if needed


@pytest.fixture(scope="session", autouse=True)
def setup_test_reports():
    """Ensure test reports directory exists"""
    reports_dir = PROJECT_ROOT / "tests" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    yield
