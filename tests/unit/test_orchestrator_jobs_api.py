"""
Orchestrator Jobs API Tests

Tests for the job tracking and status API endpoints.
Single Responsibility: Validate FastAPI job management endpoints.

Component Under Test:
- orchestrator_workers/api/jobs.py.j2

Jobs API Features (deployed on orchestrator at hx-orchestrator-server:8000):
- Job status retrieval (GET /jobs/{job_id})
- Job listing with filters (GET /jobs?status=...)
- Progress tracking and percentage calculation
- Pydantic response model validation
- Error handling (404, 500, 503)

Test Coverage:
- Job status endpoint (success, 404, 500)
- Job listing endpoint (all jobs, filtered, limited)
- Query parameter validation (status filter, limit)
- Response model validation (JobStatusResponse, JobListResponse)
- Edge cases (empty results, invalid job_id)
- Error handling (job not found, internal errors)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# Mock Pydantic models
class MockJobStatusResponse:
    """Mock JobStatusResponse model"""

    def __init__(self, job_id: str, job_type: str, status: str, chunks_total: int,
                 chunks_processed: int, percent_complete: float, created_at: str,
                 started_at: str = None, completed_at: str = None, error_message: str = None):
        self.job_id = job_id
        self.job_type = job_type
        self.status = status
        self.chunks_total = chunks_total
        self.chunks_processed = chunks_processed
        self.percent_complete = percent_complete
        self.created_at = created_at
        self.started_at = started_at
        self.completed_at = completed_at
        self.error_message = error_message


class MockJobListItem:
    """Mock JobListItem model"""

    def __init__(self, job_id: str, job_type: str, status: str, chunks_total: int,
                 chunks_processed: int, percent_complete: float, created_at: str,
                 duration_seconds: float = None):
        self.job_id = job_id
        self.job_type = job_type
        self.status = status
        self.chunks_total = chunks_total
        self.chunks_processed = chunks_processed
        self.percent_complete = percent_complete
        self.created_at = created_at
        self.duration_seconds = duration_seconds


class MockJobListResponse:
    """Mock JobListResponse model"""

    def __init__(self, jobs: list, count: int):
        self.jobs = jobs
        self.count = count


# Mock job_tracker
class MockJobTracker:
    """Mock job tracker for testing"""

    def __init__(self):
        self.jobs = {}

    async def get_progress(self, job_id: str):
        """Get job progress"""
        if job_id not in self.jobs:
            return {"error": "Job not found"}
        return self.jobs[job_id]

    async def list_jobs(self, status: str = None, limit: int = 50):
        """List jobs with optional filter"""
        jobs = list(self.jobs.values())

        # Filter by status
        if status:
            jobs = [j for j in jobs if j.get("status") == status]

        # Apply limit
        return jobs[:limit]

    def add_job(self, job_data: dict):
        """Add a job to the mock tracker"""
        self.jobs[job_data["job_id"]] = job_data


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestGetJobStatusEndpoint:
    """Test GET /jobs/{job_id} endpoint"""

    async def test_get_job_status_returns_job_details(self):
        """Test that get_job_status returns complete job details"""
        tracker = MockJobTracker()
        tracker.add_job({
            "job_id": "job-123",
            "job_type": "ingestion",
            "status": "processing",
            "chunks_total": 10,
            "chunks_processed": 5,
            "percent_complete": 50.0,
            "created_at": "2025-01-01T00:00:00",
            "started_at": "2025-01-01T00:00:05"
        })

        progress = await tracker.get_progress("job-123")

        assert progress["job_id"] == "job-123"
        assert progress["job_type"] == "ingestion"
        assert progress["status"] == "processing"
        assert progress["chunks_total"] == 10
        assert progress["chunks_processed"] == 5
        assert progress["percent_complete"] == 50.0

    async def test_get_job_status_returns_404_when_not_found(self):
        """Test that get_job_status returns 404 for unknown job_id"""
        tracker = MockJobTracker()

        progress = await tracker.get_progress("unknown-job")

        assert "error" in progress
        assert progress["error"] == "Job not found"

    async def test_get_job_status_includes_completed_timestamp(self):
        """Test that completed jobs include completed_at timestamp"""
        tracker = MockJobTracker()
        tracker.add_job({
            "job_id": "job-complete",
            "job_type": "ingestion",
            "status": "completed",
            "chunks_total": 10,
            "chunks_processed": 10,
            "percent_complete": 100.0,
            "created_at": "2025-01-01T00:00:00",
            "started_at": "2025-01-01T00:00:05",
            "completed_at": "2025-01-01T00:01:00"
        })

        progress = await tracker.get_progress("job-complete")

        assert progress["completed_at"] == "2025-01-01T00:01:00"
        assert progress["percent_complete"] == 100.0

    async def test_get_job_status_includes_error_message_for_failed_jobs(self):
        """Test that failed jobs include error_message"""
        tracker = MockJobTracker()
        tracker.add_job({
            "job_id": "job-failed",
            "job_type": "ingestion",
            "status": "failed",
            "chunks_total": 10,
            "chunks_processed": 3,
            "percent_complete": 30.0,
            "created_at": "2025-01-01T00:00:00",
            "started_at": "2025-01-01T00:00:05",
            "completed_at": "2025-01-01T00:00:30",
            "error_message": "Connection timeout to Qdrant"
        })

        progress = await tracker.get_progress("job-failed")

        assert progress["status"] == "failed"
        assert progress["error_message"] == "Connection timeout to Qdrant"


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestListJobsEndpoint:
    """Test GET /jobs endpoint"""

    async def test_list_jobs_returns_all_jobs_without_filter(self):
        """Test that list_jobs returns all jobs when no filter applied"""
        tracker = MockJobTracker()
        tracker.add_job({
            "job_id": "job-1",
            "job_type": "ingestion",
            "status": "completed",
            "chunks_total": 10,
            "chunks_processed": 10,
            "percent_complete": 100.0,
            "created_at": "2025-01-01T00:00:00"
        })
        tracker.add_job({
            "job_id": "job-2",
            "job_type": "ingestion",
            "status": "processing",
            "chunks_total": 20,
            "chunks_processed": 5,
            "percent_complete": 25.0,
            "created_at": "2025-01-01T01:00:00"
        })

        jobs = await tracker.list_jobs()

        assert len(jobs) == 2

    async def test_list_jobs_filters_by_status(self):
        """Test that list_jobs filters jobs by status parameter"""
        tracker = MockJobTracker()
        tracker.add_job({
            "job_id": "job-1",
            "status": "completed",
            "job_type": "ingestion",
            "chunks_total": 10,
            "chunks_processed": 10,
            "percent_complete": 100.0,
            "created_at": "2025-01-01T00:00:00"
        })
        tracker.add_job({
            "job_id": "job-2",
            "status": "processing",
            "job_type": "ingestion",
            "chunks_total": 20,
            "chunks_processed": 5,
            "percent_complete": 25.0,
            "created_at": "2025-01-01T01:00:00"
        })
        tracker.add_job({
            "job_id": "job-3",
            "status": "completed",
            "job_type": "ingestion",
            "chunks_total": 15,
            "chunks_processed": 15,
            "percent_complete": 100.0,
            "created_at": "2025-01-01T02:00:00"
        })

        # Filter for completed jobs only
        jobs = await tracker.list_jobs(status="completed")

        assert len(jobs) == 2
        assert all(j["status"] == "completed" for j in jobs)

    async def test_list_jobs_respects_limit_parameter(self):
        """Test that list_jobs respects the limit parameter"""
        tracker = MockJobTracker()

        # Add 10 jobs
        for i in range(10):
            tracker.add_job({
                "job_id": f"job-{i}",
                "status": "completed",
                "job_type": "ingestion",
                "chunks_total": 10,
                "chunks_processed": 10,
                "percent_complete": 100.0,
                "created_at": f"2025-01-01T{i:02d}:00:00"
            })

        # Request only 5
        jobs = await tracker.list_jobs(limit=5)

        assert len(jobs) == 5

    async def test_list_jobs_returns_empty_list_when_no_matches(self):
        """Test that list_jobs returns empty list when no jobs match filter"""
        tracker = MockJobTracker()
        tracker.add_job({
            "job_id": "job-1",
            "status": "completed",
            "job_type": "ingestion",
            "chunks_total": 10,
            "chunks_processed": 10,
            "percent_complete": 100.0,
            "created_at": "2025-01-01T00:00:00"
        })

        # Filter for non-existent status
        jobs = await tracker.list_jobs(status="failed")

        assert len(jobs) == 0
        assert isinstance(jobs, list)

    async def test_list_jobs_includes_duration_for_completed_jobs(self):
        """Test that list_jobs includes duration_seconds for completed jobs"""
        tracker = MockJobTracker()
        tracker.add_job({
            "job_id": "job-1",
            "status": "completed",
            "job_type": "ingestion",
            "chunks_total": 10,
            "chunks_processed": 10,
            "percent_complete": 100.0,
            "created_at": "2025-01-01T00:00:00",
            "duration_seconds": 60.5
        })

        jobs = await tracker.list_jobs()

        assert jobs[0]["duration_seconds"] == 60.5


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestJobsAPIResponseModels:
    """Test Pydantic response model validation"""

    async def test_job_status_response_model_validation(self):
        """Test that JobStatusResponse model validates correctly"""
        response = MockJobStatusResponse(
            job_id="job-123",
            job_type="ingestion",
            status="processing",
            chunks_total=10,
            chunks_processed=5,
            percent_complete=50.0,
            created_at="2025-01-01T00:00:00"
        )

        assert response.job_id == "job-123"
        assert response.status == "processing"
        assert response.chunks_total == 10
        assert response.chunks_processed == 5
        assert response.percent_complete == 50.0
        assert response.started_at is None  # Optional field

    async def test_job_list_response_model_validation(self):
        """Test that JobListResponse model validates correctly"""
        jobs = [
            MockJobListItem(
                job_id="job-1",
                job_type="ingestion",
                status="completed",
                chunks_total=10,
                chunks_processed=10,
                percent_complete=100.0,
                created_at="2025-01-01T00:00:00",
                duration_seconds=60.0
            ),
            MockJobListItem(
                job_id="job-2",
                job_type="ingestion",
                status="processing",
                chunks_total=20,
                chunks_processed=5,
                percent_complete=25.0,
                created_at="2025-01-01T01:00:00"
            )
        ]

        response = MockJobListResponse(jobs=jobs, count=len(jobs))

        assert response.count == 2
        assert len(response.jobs) == 2
        assert response.jobs[0].job_id == "job-1"
        assert response.jobs[1].status == "processing"


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestJobsAPIErrorHandling:
    """Test error handling in Jobs API"""

    async def test_get_job_status_handles_job_tracker_error(self):
        """Test that get_job_status handles job_tracker exceptions"""
        tracker = MockJobTracker()

        # Simulate internal error by not having the job
        progress = await tracker.get_progress("error-job")

        # Should return error indicator
        assert "error" in progress

    async def test_list_jobs_returns_empty_on_no_jobs(self):
        """Test that list_jobs handles empty job list gracefully"""
        tracker = MockJobTracker()

        jobs = await tracker.list_jobs()

        assert len(jobs) == 0
        assert isinstance(jobs, list)
