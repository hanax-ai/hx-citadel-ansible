"""
Type Guard Tests

Tests for runtime type checking functions.
Single Responsibility: Validate type guard functions.

Functions Tested:
- is_valid_job_status()
- is_valid_health_status()
- is_valid_lightrag_mode()
"""

import pytest
from common_types import (
    is_valid_job_status,
    is_valid_health_status,
    is_valid_lightrag_mode,
)


@pytest.mark.unit
@pytest.mark.fast
class TestTypeGuards:
    """Test runtime type checking functions"""

    def test_is_valid_job_status(self):
        """Test job status validation"""
        # Valid statuses
        assert is_valid_job_status("pending") is True
        assert is_valid_job_status("processing") is True
        assert is_valid_job_status("completed") is True
        assert is_valid_job_status("failed") is True
        assert is_valid_job_status("cancelled") is True

        # Invalid statuses
        assert is_valid_job_status("invalid") is False
        assert is_valid_job_status("PENDING") is False  # Case sensitive
        assert is_valid_job_status("") is False

    def test_is_valid_health_status(self):
        """Test health status validation"""
        # Valid statuses
        assert is_valid_health_status("healthy") is True
        assert is_valid_health_status("degraded") is True
        assert is_valid_health_status("unhealthy") is True
        assert is_valid_health_status("unknown") is True

        # Invalid statuses
        assert is_valid_health_status("invalid") is False
        assert is_valid_health_status("OK") is False

    def test_is_valid_lightrag_mode(self):
        """Test LightRAG mode validation"""
        # Valid modes
        assert is_valid_lightrag_mode("naive") is True
        assert is_valid_lightrag_mode("local") is True
        assert is_valid_lightrag_mode("global") is True
        assert is_valid_lightrag_mode("hybrid") is True

        # Invalid modes
        assert is_valid_lightrag_mode("invalid") is False
        assert is_valid_lightrag_mode("HYBRID") is False  # Case sensitive
