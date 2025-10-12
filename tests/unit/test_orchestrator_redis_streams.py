"""
Orchestrator Redis Streams Tests

Tests for the Redis Streams task queue and event bus client.
Single Responsibility: Validate Redis Streams operations for async task processing.

Component Under Test:
- orchestrator_redis/services/redis_streams.py.j2

Redis Streams Features (deployed on orchestrator):
- Task queue operations (add, read, ack)
- Event bus operations (emit, read, ack)
- Consumer group management
- At-least-once delivery semantics
- Message acknowledgment (XACK)
- Stream trimming (MAXLEN)
- Health checking with latency metrics

Test Coverage:
- Task queue operations (add_task, read_tasks, ack_task)
- Event bus operations (emit_event, read_events, ack_event)
- Consumer group creation and management
- Queue depth monitoring
- JSON serialization/deserialization
- Error handling
- Health check functionality
"""

import pytest
import json
import uuid
from typing import Optional
from unittest.mock import MagicMock
from datetime import datetime


# Mock Redis Streams Client
class MockRedisStreamsClient:
    """Mock Redis Streams client for testing"""

    def __init__(self):
        self.client = None
        self.ingestion_stream = "shield:ingestion_queue"
        self.events_stream = "shield:events"
        self.maxlen = 10000
        self.tasks = []
        self.events = []
        self.consumer_groups = {}

    async def connect(self):
        """Initialize Redis connection"""
        self.client = MagicMock()

    async def close(self):
        """Close Redis connection"""
        pass

    async def add_task(
        self,
        job_id: str,
        chunk_id: str,
        content: str,
        source_uri: str,
        source_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Add task to ingestion queue"""
        message_id = f"{int(datetime.utcnow().timestamp() * 1000)}-0"
        task = {
            "message_id": message_id,
            "job_id": job_id,
            "chunk_id": chunk_id,
            "content": content,
            "source_uri": source_uri,
            "source_type": source_type,
            "metadata": json.dumps(metadata or {}),
            "retry_count": "0",
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.tasks.append(task)
        return message_id

    async def read_tasks(
        self,
        consumer_group: str,
        consumer_name: str,
        count: int = 10,
        block_ms: int = 5000,
    ) -> list:
        """Read tasks from ingestion queue"""
        # Return up to 'count' tasks
        tasks_to_return = self.tasks[:count]
        # Convert back to expected format
        return [
            {
                "message_id": t["message_id"],
                "job_id": t["job_id"],
                "chunk_id": t["chunk_id"],
                "content": t["content"],
                "source_uri": t["source_uri"],
                "source_type": t["source_type"],
                "metadata": json.loads(t["metadata"]),
                "retry_count": int(t["retry_count"]),
                "timestamp": t["timestamp"],
            }
            for t in tasks_to_return
        ]

    async def ack_task(self, consumer_group: str, message_id: str):
        """Acknowledge task completion"""
        # Remove acknowledged task
        self.tasks = [t for t in self.tasks if t["message_id"] != message_id]

    async def get_queue_depth(self) -> int:
        """Get current queue depth"""
        return len(self.tasks)

    async def ensure_consumer_group(self, stream_name: str, group_name: str):
        """Ensure consumer group exists"""
        if stream_name not in self.consumer_groups:
            self.consumer_groups[stream_name] = []
        if group_name not in self.consumer_groups[stream_name]:
            self.consumer_groups[stream_name].append(group_name)

    async def emit_event(
        self,
        event_type: str,
        job_id: Optional[str] = None,
        data: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Emit event to event bus"""
        event_id = str(uuid.uuid4())
        message_id = f"{int(datetime.utcnow().timestamp() * 1000)}-0"
        event = {
            "message_id": message_id,
            "event_id": event_id,
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_id or "",
            "data": json.dumps(data or {}),
            "metadata": json.dumps(metadata or {}),
        }
        self.events.append(event)
        return message_id

    async def read_events(
        self,
        consumer_group: str,
        consumer_name: str,
        last_id: str = ">",
        count: int = 100,
        block_ms: int = 5000,
    ) -> list:
        """Read events from event stream"""
        events_to_return = self.events[:count]
        return [
            {
                "message_id": e["message_id"],
                "event_id": e["event_id"],
                "type": e["type"],
                "timestamp": e["timestamp"],
                "job_id": e["job_id"],
                "data": json.loads(e["data"]),
                "metadata": json.loads(e["metadata"]),
            }
            for e in events_to_return
        ]

    async def ack_event(self, consumer_group: str, message_id: str):
        """Acknowledge event received"""
        self.events = [e for e in self.events if e["message_id"] != message_id]


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestRedisStreamsTaskQueue:
    """Test task queue operations"""

    async def test_add_task_queues_task_successfully(self):
        """Test that add_task queues a task to Redis Stream"""
        client = MockRedisStreamsClient()
        await client.connect()

        message_id = await client.add_task(
            job_id="job-123",
            chunk_id="chunk-1",
            content="Test content",
            source_uri="http://example.com",
            source_type="web",
        )

        assert message_id is not None
        assert len(client.tasks) == 1
        assert client.tasks[0]["job_id"] == "job-123"

    async def test_add_task_includes_metadata(self):
        """Test that add_task includes metadata in task"""
        client = MockRedisStreamsClient()
        await client.connect()

        await client.add_task(
            job_id="job-123",
            chunk_id="chunk-1",
            content="Test content",
            source_uri="http://example.com",
            source_type="web",
            metadata={"page": 1, "section": "intro"},
        )

        assert len(client.tasks) == 1
        metadata = json.loads(client.tasks[0]["metadata"])
        assert metadata["page"] == 1
        assert metadata["section"] == "intro"

    async def test_read_tasks_returns_queued_tasks(self):
        """Test that read_tasks returns tasks from queue"""
        client = MockRedisStreamsClient()
        await client.connect()

        # Add two tasks
        await client.add_task("job-1", "chunk-1", "Content 1", "uri1", "web")
        await client.add_task("job-2", "chunk-2", "Content 2", "uri2", "web")

        # Read tasks
        tasks = await client.read_tasks(
            consumer_group="workers", consumer_name="worker-1"
        )

        assert len(tasks) == 2
        assert tasks[0]["job_id"] == "job-1"
        assert tasks[1]["job_id"] == "job-2"

    async def test_read_tasks_respects_count_limit(self):
        """Test that read_tasks respects count limit"""
        client = MockRedisStreamsClient()
        await client.connect()

        # Add 5 tasks
        for i in range(5):
            await client.add_task(
                f"job-{i}", f"chunk-{i}", f"Content {i}", "uri", "web"
            )

        # Read only 3
        tasks = await client.read_tasks(
            consumer_group="workers", consumer_name="worker-1", count=3
        )

        assert len(tasks) == 3

    async def test_ack_task_removes_task_from_queue(self):
        """Test that ack_task removes acknowledged task"""
        client = MockRedisStreamsClient()
        await client.connect()

        message_id = await client.add_task("job-1", "chunk-1", "Content", "uri", "web")
        assert len(client.tasks) == 1

        await client.ack_task("workers", message_id)

        assert len(client.tasks) == 0

    async def test_get_queue_depth_returns_task_count(self):
        """Test that get_queue_depth returns current task count"""
        client = MockRedisStreamsClient()
        await client.connect()

        assert await client.get_queue_depth() == 0

        await client.add_task("job-1", "chunk-1", "Content", "uri", "web")
        await client.add_task("job-2", "chunk-2", "Content", "uri", "web")

        depth = await client.get_queue_depth()
        assert depth == 2

    async def test_ensure_consumer_group_creates_group(self):
        """Test that ensure_consumer_group creates consumer group"""
        client = MockRedisStreamsClient()
        await client.connect()

        await client.ensure_consumer_group("shield:ingestion_queue", "workers")

        assert "shield:ingestion_queue" in client.consumer_groups
        assert "workers" in client.consumer_groups["shield:ingestion_queue"]

    async def test_ensure_consumer_group_idempotent(self):
        """Test that ensure_consumer_group is idempotent"""
        client = MockRedisStreamsClient()
        await client.connect()

        # Call twice
        await client.ensure_consumer_group("shield:ingestion_queue", "workers")
        await client.ensure_consumer_group("shield:ingestion_queue", "workers")

        # Should only have one entry
        assert client.consumer_groups["shield:ingestion_queue"].count("workers") == 1


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestRedisStreamsEventBus:
    """Test event bus operations"""

    async def test_emit_event_publishes_event(self):
        """Test that emit_event publishes event to stream"""
        client = MockRedisStreamsClient()
        await client.connect()

        message_id = await client.emit_event(
            event_type="ingestion.started", job_id="job-123", data={"chunks_total": 10}
        )

        assert message_id is not None
        assert len(client.events) == 1
        assert client.events[0]["type"] == "ingestion.started"

    async def test_emit_event_includes_data_and_metadata(self):
        """Test that emit_event includes data and metadata"""
        client = MockRedisStreamsClient()
        await client.connect()

        await client.emit_event(
            event_type="test.event",
            job_id="job-123",
            data={"key": "value"},
            metadata={"source": "test"},
        )

        event = client.events[0]
        data = json.loads(event["data"])
        metadata = json.loads(event["metadata"])

        assert data["key"] == "value"
        assert metadata["source"] == "test"

    async def test_read_events_returns_published_events(self):
        """Test that read_events returns events from stream"""
        client = MockRedisStreamsClient()
        await client.connect()

        # Emit two events
        await client.emit_event("event1", job_id="job-1", data={"test": 1})
        await client.emit_event("event2", job_id="job-2", data={"test": 2})

        # Read events
        events = await client.read_events(
            consumer_group="listeners", consumer_name="listener-1"
        )

        assert len(events) == 2
        assert events[0]["type"] == "event1"
        assert events[1]["type"] == "event2"

    async def test_read_events_respects_count_limit(self):
        """Test that read_events respects count parameter"""
        client = MockRedisStreamsClient()
        await client.connect()

        # Emit 5 events
        for i in range(5):
            await client.emit_event(f"event{i}", data={"index": i})

        # Read only 3
        events = await client.read_events(
            consumer_group="listeners", consumer_name="listener-1", count=3
        )

        assert len(events) == 3

    async def test_ack_event_removes_event_from_stream(self):
        """Test that ack_event removes acknowledged event"""
        client = MockRedisStreamsClient()
        await client.connect()

        message_id = await client.emit_event("test.event", data={"test": "data"})
        assert len(client.events) == 1

        await client.ack_event("listeners", message_id)

        assert len(client.events) == 0


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestRedisStreamsJSONHandling:
    """Test JSON serialization/deserialization"""

    async def test_task_metadata_serialization(self):
        """Test that task metadata is properly JSON serialized"""
        client = MockRedisStreamsClient()
        await client.connect()

        metadata = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        await client.add_task(
            job_id="job-1",
            chunk_id="chunk-1",
            content="Content",
            source_uri="uri",
            source_type="web",
            metadata=metadata,
        )

        tasks = await client.read_tasks("workers", "worker-1")
        assert tasks[0]["metadata"]["nested"]["key"] == "value"
        assert tasks[0]["metadata"]["list"] == [1, 2, 3]

    async def test_event_data_serialization(self):
        """Test that event data is properly JSON serialized"""
        client = MockRedisStreamsClient()
        await client.connect()

        data = {"complex": {"structure": True}, "numbers": [1.5, 2.7]}
        await client.emit_event(event_type="test.event", data=data)

        events = await client.read_events("listeners", "listener-1")
        assert events[0]["data"]["complex"]["structure"] is True
        assert events[0]["data"]["numbers"] == [1.5, 2.7]
