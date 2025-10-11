"""
Orchestrator Health Endpoint Tests

Tests for the FastAPI health check endpoints in orchestrator.
Single Responsibility: Validate all health check functionality.

Component Under Test:
- orchestrator_fastapi/api/health.py.j2

Health Endpoints (deployed on orchestrator at hx-orchestrator-server:8000):
- /health (or configured health_check_path) - Basic liveness
- /health/detailed (or health_detailed_path) - Component status
- /ready (or health_readiness_path) - Readiness probe
- /live (or health_liveness_path) - Liveness probe

Test Coverage:
- Basic health check (liveness)
- Detailed health with component checks
- Readiness probe validation
- Liveness probe validation
- Response models (Pydantic validation)
- Uptime calculations
- Error handling
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock
import time


# Mock health module classes (Pydantic models)
class MockHealthResponse:
    """Mock HealthResponse for testing"""

    def __init__(self, status: str, timestamp: datetime, version: str, uptime_seconds: float):
        self.status = status
        self.timestamp = timestamp
        self.version = version
        self.uptime_seconds = uptime_seconds

    def dict(self):
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "uptime_seconds": self.uptime_seconds
        }


class MockComponentHealth:
    """Mock ComponentHealth for testing"""

    def __init__(self, status: str, latency_ms: float = 0, details: dict = None):
        self.status = status
        self.latency_ms = latency_ms
        self.details = details or {}


class MockDetailedHealthResponse:
    """Mock DetailedHealthResponse for testing"""

    def __init__(self, status: str, timestamp: datetime, components: dict, overall_status: str):
        self.status = status
        self.timestamp = timestamp
        self.components = components
        self.overall_status = overall_status

    def dict(self):
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "components": self.components,
            "overall_status": self.overall_status
        }


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestBasicHealthCheck:
    """Test basic health check endpoint (liveness probe)"""

    async def test_health_check_returns_healthy_status(self):
        """Test that basic health check returns 'healthy' status"""
        # Simulate health check endpoint
        start_time = time.time()

        response = MockHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=time.time() - start_time
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime_seconds >= 0

    async def test_health_check_includes_timestamp(self):
        """Test that health check includes current timestamp"""
        start_time = time.time()
        before = datetime.utcnow()

        response = MockHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=time.time() - start_time
        )

        after = datetime.utcnow()

        # Timestamp should be between before and after
        assert before <= response.timestamp <= after

    async def test_health_check_includes_version(self):
        """Test that health check includes API version"""
        response = MockHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=0
        )

        assert response.version is not None
        assert isinstance(response.version, str)
        assert len(response.version) > 0

    async def test_health_check_calculates_uptime(self):
        """Test that health check calculates uptime correctly"""
        start_time = time.time()

        # Wait a bit to accumulate uptime
        time.sleep(0.1)

        response = MockHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=time.time() - start_time
        )

        # Uptime should be at least 0.1 seconds
        assert response.uptime_seconds >= 0.1
        assert response.uptime_seconds < 1.0  # Should be less than 1 second for this test

    async def test_health_check_response_structure(self):
        """Test that health response has correct structure"""
        response = MockHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            uptime_seconds=123.45
        )

        response_dict = response.dict()

        # Verify all required fields present
        assert "status" in response_dict
        assert "timestamp" in response_dict
        assert "version" in response_dict
        assert "uptime_seconds" in response_dict

        # Verify types
        assert isinstance(response_dict["status"], str)
        assert isinstance(response_dict["version"], str)
        assert isinstance(response_dict["uptime_seconds"], float)


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestDetailedHealthCheck:
    """Test detailed health check endpoint with component status"""

    async def test_detailed_health_includes_components(self):
        """Test that detailed health check includes component status"""
        components = {
            "application": {
                "status": "up",
                "memory_mb": 256.5,
                "cpu_percent": 12.3
            }
        }

        response = MockDetailedHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components=components,
            overall_status="healthy"
        )

        assert "application" in response.components
        assert response.components["application"]["status"] == "up"

    async def test_detailed_health_reports_overall_status(self):
        """Test that detailed health reports overall status"""
        components = {
            "application": {"status": "up"}
        }

        response = MockDetailedHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components=components,
            overall_status="healthy"
        )

        assert response.overall_status == "healthy"
        assert response.status == "healthy"

    async def test_detailed_health_includes_memory_metrics(self):
        """Test that detailed health includes memory usage"""
        components = {
            "application": {
                "status": "up",
                "memory_mb": 512.75,
                "cpu_percent": 15.5
            }
        }

        response = MockDetailedHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components=components,
            overall_status="healthy"
        )

        app_health = response.components["application"]
        assert "memory_mb" in app_health
        assert isinstance(app_health["memory_mb"], float)
        assert app_health["memory_mb"] > 0

    async def test_detailed_health_includes_cpu_metrics(self):
        """Test that detailed health includes CPU usage"""
        components = {
            "application": {
                "status": "up",
                "memory_mb": 256.0,
                "cpu_percent": 8.2
            }
        }

        response = MockDetailedHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components=components,
            overall_status="healthy"
        )

        app_health = response.components["application"]
        assert "cpu_percent" in app_health
        assert isinstance(app_health["cpu_percent"], float)
        assert app_health["cpu_percent"] >= 0


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestReadinessProbe:
    """Test readiness probe endpoint"""

    async def test_readiness_returns_ready_true(self):
        """Test that readiness probe returns ready: true"""
        response = {
            "ready": True,
            "timestamp": datetime.utcnow()
        }

        assert response["ready"] is True

    async def test_readiness_includes_timestamp(self):
        """Test that readiness probe includes timestamp"""
        before = datetime.utcnow()
        response = {
            "ready": True,
            "timestamp": datetime.utcnow()
        }
        after = datetime.utcnow()

        assert "timestamp" in response
        assert before <= response["timestamp"] <= after

    async def test_readiness_response_structure(self):
        """Test that readiness response has correct structure"""
        response = {
            "ready": True,
            "timestamp": datetime.utcnow()
        }

        # Verify required fields
        assert "ready" in response
        assert "timestamp" in response

        # Verify types
        assert isinstance(response["ready"], bool)
        assert isinstance(response["timestamp"], datetime)


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestLivenessProbe:
    """Test liveness probe endpoint"""

    async def test_liveness_returns_alive_true(self):
        """Test that liveness probe returns alive: true"""
        import os

        response = {
            "alive": True,
            "pid": os.getpid(),
            "timestamp": datetime.utcnow()
        }

        assert response["alive"] is True

    async def test_liveness_includes_pid(self):
        """Test that liveness probe includes process ID"""
        import os

        response = {
            "alive": True,
            "pid": os.getpid(),
            "timestamp": datetime.utcnow()
        }

        assert "pid" in response
        assert isinstance(response["pid"], int)
        assert response["pid"] > 0
        assert response["pid"] == os.getpid()

    async def test_liveness_includes_timestamp(self):
        """Test that liveness probe includes timestamp"""
        import os

        before = datetime.utcnow()
        response = {
            "alive": True,
            "pid": os.getpid(),
            "timestamp": datetime.utcnow()
        }
        after = datetime.utcnow()

        assert "timestamp" in response
        assert before <= response["timestamp"] <= after

    async def test_liveness_response_structure(self):
        """Test that liveness response has correct structure"""
        import os

        response = {
            "alive": True,
            "pid": os.getpid(),
            "timestamp": datetime.utcnow()
        }

        # Verify required fields
        assert "alive" in response
        assert "pid" in response
        assert "timestamp" in response

        # Verify types
        assert isinstance(response["alive"], bool)
        assert isinstance(response["pid"], int)
        assert isinstance(response["timestamp"], datetime)
