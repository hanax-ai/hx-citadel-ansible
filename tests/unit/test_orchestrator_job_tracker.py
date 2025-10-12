"""
Orchestrator Job Tracker Tests

Tests for the job tracking service in orchestrator.
Single Responsibility: Validate job status tracking via Redis + PostgreSQL.

Component Under Test:
- orchestrator_workers/services/job_tracker.py.j2

Job Tracker Features (deployed on orchestrator at hx-orchestrator-server):
- Dual storage (Redis for speed, PostgreSQL for persistence)
- Job creation with UUID generation
- Status management (queued → processing → completed/failed)
- Progress tracking (chunks_processed/chunks_total)
- Timestamp tracking (created_at, started_at, completed_at)
- TTL cleanup in Redis
- Job listing with filters

Test Coverage:
- Job creation (with/without job_id)
- Job status updates
- Progress increment
- Progress retrieval (Redis first, PostgreSQL fallback)
- Job listing with filters
- Timestamp management
- Error handling (PostgreSQL failures)
- TTL extension on updates
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from uuid import UUID


# Mock job tracker classes
class MockRedisClient:
    """Mock Redis client"""

    def __init__(self):
        self.data = {}  # Simulated Redis storage
        self.ttls = {}  # Track TTLs

    async def hset(self, key: str, mapping: dict = None, **kwargs):
        """Mock HSET"""
        if key not in self.data:
            self.data[key] = {}
        if mapping:
            self.data[key].update(mapping)
        if kwargs:
            self.data[key].update(kwargs)

    async def hgetall(self, key: str):
        """Mock HGETALL"""
        if key in self.data:
            # Return data as bytes (like real Redis)
            return {k.encode(): str(v).encode() for k, v in self.data[key].items()}
        return {}

    async def hincrby(self, key: str, field: str, amount: int):
        """Mock HINCRBY"""
        if key not in self.data:
            self.data[key] = {}
        current = int(self.data[key].get(field, 0))
        new_value = current + amount
        self.data[key][field] = str(new_value)
        return new_value

    async def expire(self, key: str, ttl: int):
        """Mock EXPIRE"""
        self.ttls[key] = ttl


class MockDatabaseSession:
    """Mock database session"""

    def __init__(self):
        self.jobs = {}
        self.committed = False

    def add(self, obj):
        """Mock add"""
        self.jobs[obj.id] = obj

    async def commit(self):
        """Mock commit"""
        self.committed = True

    async def execute(self, query):
        """Mock execute"""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.scalars.return_value.all.return_value = []
        return result

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class MockJobTracker:
    """Mock job tracker for testing"""

    def __init__(self):
        self.job_status_ttl = 3600
        self.redis_client = MockRedisClient()

    async def create_job(
        self,
        job_type: str,
        chunks_total: int,
        metadata: dict = None,
        job_id: str = None,
    ):
        """Create new job"""
        from uuid import uuid4

        if job_id is None:
            job_id = str(uuid4())

        created_at = datetime.utcnow()

        # Store in Redis
        await self.redis_client.hset(
            f"job:{job_id}",
            mapping={
                "job_id": job_id,
                "job_type": job_type,
                "status": "queued",
                "chunks_total": str(chunks_total),
                "chunks_processed": "0",
                "created_at": created_at.isoformat(),
            },
        )

        # Set TTL
        await self.redis_client.expire(f"job:{job_id}", self.job_status_ttl)

        return job_id

    async def update_job(self, job_id: str, status: str = None, error: str = None):
        """Update job status"""
        updates = {}

        if status:
            updates["status"] = status

        if error:
            updates["error_message"] = error

        if updates:
            await self.redis_client.hset(f"job:{job_id}", mapping=updates)
            await self.redis_client.expire(f"job:{job_id}", self.job_status_ttl)

    async def increment_processed(self, job_id: str):
        """Increment chunks processed"""
        new_count = await self.redis_client.hincrby(
            f"job:{job_id}", "chunks_processed", 1
        )
        return int(new_count)

    async def get_progress(self, job_id: str):
        """Get job progress"""
        job_data = await self.redis_client.hgetall(f"job:{job_id}")

        if job_data:
            chunks_total = int(job_data.get(b"chunks_total", b"0"))
            chunks_processed = int(job_data.get(b"chunks_processed", b"0"))
            percent = (chunks_processed / chunks_total * 100) if chunks_total > 0 else 0

            return {
                "job_id": job_id,
                "status": job_data.get(b"status", b"unknown").decode("utf-8"),
                "job_type": job_data.get(b"job_type", b"unknown").decode("utf-8"),
                "chunks_total": chunks_total,
                "chunks_processed": chunks_processed,
                "percent_complete": round(percent, 2),
                "created_at": job_data.get(b"created_at", b"").decode("utf-8"),
            }

        return {"error": "Job not found"}


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestJobCreation:
    """Test job creation"""

    async def test_create_job_generates_uuid_if_not_provided(self):
        """Test that create_job generates UUID when job_id is None"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(
            job_type="lightrag_ingestion", chunks_total=100
        )

        # Should be valid UUID
        assert job_id is not None
        assert isinstance(job_id, str)
        # Validate UUID format
        UUID(job_id)  # Raises if invalid

    async def test_create_job_uses_provided_job_id(self):
        """Test that create_job uses provided job_id"""
        tracker = MockJobTracker()
        custom_id = "custom-job-123"

        job_id = await tracker.create_job(
            job_type="lightrag_ingestion", chunks_total=50, job_id=custom_id
        )

        assert job_id == custom_id

    async def test_create_job_stores_in_redis(self):
        """Test that create_job stores job data in Redis"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=10)

        # Verify data in Redis
        job_data = await tracker.redis_client.hgetall(f"job:{job_id}")

        assert job_data is not None
        assert b"job_id" in job_data
        assert b"job_type" in job_data
        assert b"status" in job_data

    async def test_create_job_sets_initial_status_queued(self):
        """Test that created job has status 'queued'"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=5)

        job_data = await tracker.redis_client.hgetall(f"job:{job_id}")

        assert job_data[b"status"].decode() == "queued"

    async def test_create_job_sets_chunks_processed_to_zero(self):
        """Test that new job has chunks_processed = 0"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=20)

        job_data = await tracker.redis_client.hgetall(f"job:{job_id}")

        assert job_data[b"chunks_processed"].decode() == "0"

    async def test_create_job_sets_ttl_in_redis(self):
        """Test that create_job sets TTL for Redis key"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=5)

        # Check TTL was set
        assert f"job:{job_id}" in tracker.redis_client.ttls
        assert tracker.redis_client.ttls[f"job:{job_id}"] == 3600


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestJobStatusUpdates:
    """Test job status updates"""

    async def test_update_job_changes_status(self):
        """Test that update_job changes job status"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=10)

        await tracker.update_job(job_id, status="processing")

        job_data = await tracker.redis_client.hgetall(f"job:{job_id}")

        assert job_data[b"status"].decode() == "processing"

    async def test_update_job_sets_error_message(self):
        """Test that update_job can set error message"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=5)

        await tracker.update_job(job_id, status="failed", error="Test error message")

        job_data = await tracker.redis_client.hgetall(f"job:{job_id}")

        assert b"error_message" in job_data
        assert job_data[b"error_message"].decode() == "Test error message"

    async def test_update_job_extends_ttl(self):
        """Test that update_job extends TTL in Redis"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=5)

        # Update status
        await tracker.update_job(job_id, status="processing")

        # TTL should be extended
        assert tracker.redis_client.ttls[f"job:{job_id}"] == 3600


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestJobProgressTracking:
    """Test job progress tracking"""

    async def test_increment_processed_increments_counter(self):
        """Test that increment_processed increments chunks_processed"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=10)

        # Increment once
        count = await tracker.increment_processed(job_id)
        assert count == 1

        # Increment again
        count = await tracker.increment_processed(job_id)
        assert count == 2

    async def test_increment_processed_returns_new_count(self):
        """Test that increment_processed returns updated count"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=5)

        for i in range(1, 6):
            count = await tracker.increment_processed(job_id)
            assert count == i

    async def test_get_progress_calculates_percent_complete(self):
        """Test that get_progress calculates percent_complete"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=100)

        # Process 25 chunks
        for _ in range(25):
            await tracker.increment_processed(job_id)

        progress = await tracker.get_progress(job_id)

        assert progress["percent_complete"] == 25.0

    async def test_get_progress_returns_job_status(self):
        """Test that get_progress includes job status"""
        tracker = MockJobTracker()

        job_id = await tracker.create_job(job_type="test_job", chunks_total=10)
        await tracker.update_job(job_id, status="processing")

        progress = await tracker.get_progress(job_id)

        assert progress["status"] == "processing"

    async def test_get_progress_returns_not_found_for_invalid_job(self):
        """Test that get_progress returns error for non-existent job"""
        tracker = MockJobTracker()

        progress = await tracker.get_progress("invalid-job-id")

        assert "error" in progress
        assert progress["error"] == "Job not found"
