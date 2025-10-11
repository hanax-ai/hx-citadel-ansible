"""
Integration Tests

Tests for cross-type validation and integration scenarios.
Single Responsibility: Validate that types work together correctly.

Scenarios Tested:
- Error responses in API responses
- Complete job status lifecycle
- Request/response compatibility
"""

import pytest
from common_types import (
    create_error_response,
    create_job_status_response,
    CrawlWebResponse,
    JobStatusEnum,
    MCPResponseStatusEnum,
)


@pytest.mark.unit
@pytest.mark.fast
class TestTypeIntegration:
    """Test that types work together correctly"""

    def test_error_response_in_crawl_response(self):
        """Test that error responses work in crawl response"""
        error = create_error_response(
            error="Connection failed",
            error_type="http_error",
            status_code=500
        )

        resp = CrawlWebResponse(
            status=MCPResponseStatusEnum.ERROR,
            pages_crawled=0,
            error=error["error"],
            error_type=error["error_type"]
        )
        assert resp.status == MCPResponseStatusEnum.ERROR
        assert resp.error == "Connection failed"

    def test_job_status_lifecycle(self):
        """Test complete job status lifecycle"""
        # Pending
        pending = create_job_status_response(
            job_id="lifecycle-job",
            job_status=JobStatusEnum.PENDING,
            progress=0,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:00:00Z"
        )
        assert pending["job_status"] == JobStatusEnum.PENDING

        # Processing
        processing = create_job_status_response(
            job_id="lifecycle-job",
            job_status=JobStatusEnum.PROCESSING,
            progress=50,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:05:00Z"
        )
        assert processing["progress"] == 50

        # Completed
        completed = create_job_status_response(
            job_id="lifecycle-job",
            job_status=JobStatusEnum.COMPLETED,
            progress=100,
            created_at="2025-10-11T10:00:00Z",
            updated_at="2025-10-11T10:10:00Z",
            result={"success": True}
        )
        assert completed["result"]["success"] is True
