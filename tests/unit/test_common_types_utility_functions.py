"""
Utility Function Tests

Tests for utility functions in common_types module.
Single Responsibility: Validate utility function behavior.

Functions Tested:
- create_error_response()
- create_job_status_response()
"""

import pytest
from common_types import (
    create_error_response,
    create_job_status_response,
    JobStatusEnum,
    MCPResponseStatusEnum,
)


@pytest.mark.unit
@pytest.mark.fast
class TestCreateErrorResponse:
    """Test create_error_response() utility"""

    def test_minimal_error(self):
        """Test creating minimal error response"""
        resp = create_error_response(
            error="Something went wrong", error_type="generic_error"
        )
        assert resp["status"] == "error"
        assert resp["error"] == "Something went wrong"
        assert resp["error_type"] == "generic_error"
        assert "status_code" not in resp
        assert "retry_after" not in resp

    def test_error_with_status_code(self):
        """Test error response with HTTP status code"""
        resp = create_error_response(
            error="Not found", error_type="http_error", status_code=404
        )
        assert resp["status_code"] == 404

    def test_error_with_retry_after(self):
        """Test error response with retry delay"""
        resp = create_error_response(
            error="Rate limited", error_type="rate_limit_error", retry_after=120
        )
        assert resp["retry_after"] == 120

    def test_error_with_all_fields(self):
        """Test error response with all optional fields"""
        resp = create_error_response(
            error="Service unavailable",
            error_type="service_error",
            status_code=503,
            retry_after=60,
        )
        assert resp["status"] == "error"
        assert resp["error"] == "Service unavailable"
        assert resp["error_type"] == "service_error"
        assert resp["status_code"] == 503
        assert resp["retry_after"] == 60


@pytest.mark.unit
@pytest.mark.fast
class TestCreateJobStatusResponse:
    """Test create_job_status_response() utility"""

    def test_pending_job(self):
        """Test creating response for pending job"""
        resp = create_job_status_response(
            job_id="job-123",
            job_status=JobStatusEnum.PENDING,
            progress=0,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z",
        )
        assert resp["job_id"] == "job-123"
        assert resp["job_status"] == JobStatusEnum.PENDING
        assert resp["progress"] == 0
        assert resp["status"] == MCPResponseStatusEnum.SUCCESS

    def test_processing_job_with_progress(self):
        """Test response for job in progress"""
        resp = create_job_status_response(
            job_id="job-456",
            job_status=JobStatusEnum.PROCESSING,
            progress=50,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:05:00Z",
            metadata={"pages_processed": 25},
        )
        assert resp["progress"] == 50
        assert resp["job_status"] == JobStatusEnum.PROCESSING
        assert resp["metadata"]["pages_processed"] == 25

    def test_completed_job_with_result(self):
        """Test response for completed job"""
        resp = create_job_status_response(
            job_id="job-789",
            job_status=JobStatusEnum.COMPLETED,
            progress=100,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:10:00Z",
            result={"documents_indexed": 100, "vectors_created": 100},
        )
        assert resp["progress"] == 100
        assert resp["job_status"] == JobStatusEnum.COMPLETED
        assert resp["result"]["documents_indexed"] == 100

    def test_failed_job_with_error(self):
        """Test response for failed job"""
        resp = create_job_status_response(
            job_id="job-fail",
            job_status=JobStatusEnum.FAILED,
            progress=30,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:03:00Z",
            error="Connection timeout to Qdrant",
        )
        assert resp["job_status"] == JobStatusEnum.FAILED
        assert resp["error"] == "Connection timeout to Qdrant"

    def test_progress_clamping(self):
        """Test that progress is clamped to 0-100 range"""
        # Below 0
        resp = create_job_status_response(
            job_id="job-1",
            job_status=JobStatusEnum.PENDING,
            progress=-10,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z",
        )
        assert resp["progress"] == 0

        # Above 100
        resp = create_job_status_response(
            job_id="job-2",
            job_status=JobStatusEnum.COMPLETED,
            progress=150,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z",
        )
        assert resp["progress"] == 100
