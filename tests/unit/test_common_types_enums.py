"""
Enumeration Type Tests

Tests for all enum types in the common_types module.
Single Responsibility: Validate enum definitions and behavior.

Enums Tested:
- JobStatusEnum
- HealthStatusEnum
- CircuitBreakerStateEnum
- LightRAGModeEnum
- MCPResponseStatusEnum
"""

import pytest
from common_types import (
    JobStatusEnum,
    HealthStatusEnum,
    CircuitBreakerStateEnum,
    LightRAGModeEnum,
    MCPResponseStatusEnum,
)


@pytest.mark.unit
@pytest.mark.fast
class TestJobStatusEnum:
    """Test JobStatusEnum values and behavior"""

    def test_all_values_present(self):
        """Test all expected job status values exist"""
        expected_values = ["pending", "processing", "completed", "failed", "cancelled"]
        actual_values = [status.value for status in JobStatusEnum]
        assert set(actual_values) == set(expected_values)
        assert len(actual_values) == 5

    def test_enum_is_string(self):
        """Test that enum values are strings"""
        for status in JobStatusEnum:
            assert isinstance(status.value, str)

    def test_enum_access(self):
        """Test accessing enum by name"""
        assert JobStatusEnum.PENDING.value == "pending"
        assert JobStatusEnum.PROCESSING.value == "processing"
        assert JobStatusEnum.COMPLETED.value == "completed"
        assert JobStatusEnum.FAILED.value == "failed"
        assert JobStatusEnum.CANCELLED.value == "cancelled"

    def test_enum_comparison(self):
        """Test enum comparison works correctly"""
        assert JobStatusEnum.PENDING == JobStatusEnum.PENDING
        assert JobStatusEnum.COMPLETED != JobStatusEnum.FAILED


@pytest.mark.unit
@pytest.mark.fast
class TestHealthStatusEnum:
    """Test HealthStatusEnum values"""

    def test_all_values_present(self):
        """Test all health status values exist"""
        expected_values = ["healthy", "degraded", "unhealthy", "unknown"]
        actual_values = [status.value for status in HealthStatusEnum]
        assert set(actual_values) == set(expected_values)
        assert len(actual_values) == 4

    def test_healthy_status(self):
        """Test healthy status value"""
        assert HealthStatusEnum.HEALTHY.value == "healthy"

    def test_degraded_status(self):
        """Test degraded status value"""
        assert HealthStatusEnum.DEGRADED.value == "degraded"


@pytest.mark.unit
@pytest.mark.fast
class TestCircuitBreakerStateEnum:
    """Test CircuitBreakerStateEnum values"""

    def test_all_states_present(self):
        """Test all circuit breaker states exist"""
        expected_states = ["closed", "open", "half_open"]
        actual_states = [state.value for state in CircuitBreakerStateEnum]
        assert set(actual_states) == set(expected_states)
        assert len(actual_states) == 3

    def test_closed_state(self):
        """Test closed (normal operation) state"""
        assert CircuitBreakerStateEnum.CLOSED.value == "closed"

    def test_open_state(self):
        """Test open (failing fast) state"""
        assert CircuitBreakerStateEnum.OPEN.value == "open"

    def test_half_open_state(self):
        """Test half_open (testing recovery) state"""
        assert CircuitBreakerStateEnum.HALF_OPEN.value == "half_open"


@pytest.mark.unit
@pytest.mark.fast
class TestLightRAGModeEnum:
    """Test LightRAGModeEnum values"""

    def test_all_modes_present(self):
        """Test all LightRAG modes exist"""
        expected_modes = ["naive", "local", "global", "hybrid"]
        actual_modes = [mode.value for mode in LightRAGModeEnum]
        assert set(actual_modes) == set(expected_modes)
        assert len(actual_modes) == 4

    def test_hybrid_mode_default(self):
        """Test hybrid mode (recommended default)"""
        assert LightRAGModeEnum.HYBRID.value == "hybrid"


@pytest.mark.unit
@pytest.mark.fast
class TestMCPResponseStatusEnum:
    """Test MCPResponseStatusEnum values"""

    def test_all_statuses_present(self):
        """Test all MCP response statuses exist"""
        expected_statuses = ["success", "accepted", "error"]
        actual_statuses = [status.value for status in MCPResponseStatusEnum]
        assert set(actual_statuses) == set(expected_statuses)
        assert len(actual_statuses) == 3

    def test_http_202_accepted_pattern(self):
        """Test that ACCEPTED status exists for HTTP 202 pattern"""
        assert MCPResponseStatusEnum.ACCEPTED.value == "accepted"
