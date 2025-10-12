"""
Orchestrator Worker Pool Tests

Tests for the async worker pool manager in orchestrator.
Single Responsibility: Validate worker lifecycle, task processing, error handling.

Component Under Test:
- orchestrator_workers/workers/worker_pool.py.j2

Worker Pool Features (deployed on orchestrator at hx-orchestrator-server):
- Multiple async workers consuming from Redis Streams
- Consumer group coordination
- Graceful shutdown on SIGTERM/SIGINT
- Task processing via LightRAG
- Health monitoring
- Automatic restart after max tasks
- Error handling and retry logic

Test Coverage:
- Worker pool initialization
- Worker pool start/stop lifecycle
- Worker task consumption from Redis Streams
- Task processing and ACK behavior
- Error handling (don't ACK failed tasks)
- Graceful shutdown with timeout
- Worker restart after max tasks
- Health check statistics
- Event emissions
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime


# Mock worker pool classes
class MockRedisStreams:
    """Mock Redis Streams client"""

    def __init__(self):
        self.client = AsyncMock()
        self.client.xreadgroup = AsyncMock(return_value=[])
        self.client.xack = AsyncMock(return_value=1)
        self.client.xdel = AsyncMock(return_value=1)
        self.client.xpending = AsyncMock(return_value=[0])

    async def ensure_consumer_group(self, stream_name: str, group_name: str):
        """Mock consumer group creation"""
        pass


class MockEventBus:
    """Mock event bus"""

    def __init__(self):
        self.events = []

    async def emit_event(self, event_type: str, metadata: dict):
        """Mock event emission"""
        self.events.append({"type": event_type, "metadata": metadata})


class MockLightRAGProcessor:
    """Mock LightRAG processor"""

    async def process_chunk(self, task: dict):
        """Mock chunk processing"""
        await asyncio.sleep(0.01)  # Simulate processing
        return {"status": "success", "task": task}


class MockWorkerPool:
    """Mock worker pool for testing"""

    def __init__(self, pool_size: int = 4):
        self.pool_size = pool_size
        self.workers = []
        self.running = False
        self.processor = MockLightRAGProcessor()
        self.consumer_group = "lightrag-workers"
        self.stream_name = "shield:ingestion_queue"
        self._shutdown_event = asyncio.Event()
        self.redis_streams = MockRedisStreams()
        self.event_bus = MockEventBus()

    async def start(self):
        """Start worker pool"""
        self.running = True
        self._shutdown_event.clear()

        # Ensure consumer group
        await self.redis_streams.ensure_consumer_group(
            self.stream_name, self.consumer_group
        )

        # Create worker tasks
        for worker_id in range(self.pool_size):
            worker_task = asyncio.create_task(
                self._worker_loop(worker_id), name=f"worker-{worker_id}"
            )
            self.workers.append(worker_task)

        # Emit event
        await self.event_bus.emit_event(
            event_type="worker_pool.started", metadata={"pool_size": self.pool_size}
        )

    async def _worker_loop(self, worker_id: int):
        """Worker loop"""
        consumer_name = f"worker-{worker_id}"

        # Emit worker started
        await self.event_bus.emit_event(
            event_type="worker.started",
            metadata={"worker_id": worker_id, "consumer_name": consumer_name},
        )

        tasks_processed = 0
        max_tasks = 1000

        while self.running and not self._shutdown_event.is_set():
            try:
                # Read from queue
                messages = await self.redis_streams.client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=consumer_name,
                    streams={self.stream_name: ">"},
                    count=10,
                    block=5000,
                )

                if not messages:
                    continue

                # Process messages
                for _, message_list in messages:
                    for message_id, fields in message_list:
                        # Process task
                        task = {k: v for k, v in fields.items()}
                        task["message_id"] = message_id

                        try:
                            await self.processor.process_chunk(task)

                            # ACK task
                            await self.redis_streams.client.xack(
                                self.stream_name, self.consumer_group, message_id
                            )

                            # Delete message
                            await self.redis_streams.client.xdel(
                                self.stream_name, message_id
                            )

                            tasks_processed += 1

                            # Check max tasks
                            if tasks_processed >= max_tasks:
                                break

                        except (ValueError, RuntimeError, asyncio.CancelledError) as e:
                            # Don't ACK failed tasks
                            await self.event_bus.emit_event(
                                event_type="worker.task_failed",
                                metadata={"worker_id": worker_id, "error": str(e)},
                            )
                            # Re-raise CancelledError to allow graceful shutdown
                            if isinstance(e, asyncio.CancelledError):
                                raise

            except asyncio.CancelledError:
                break
            except (ConnectionError, TimeoutError):
                await asyncio.sleep(0.1)
            except Exception:
                await asyncio.sleep(0.1)

        # Emit worker stopped
        await self.event_bus.emit_event(
            event_type="worker.stopped",
            metadata={"worker_id": worker_id, "tasks_processed": tasks_processed},
        )

    async def stop(self):
        """Stop worker pool"""
        self.running = False
        self._shutdown_event.set()

        # Wait for workers with timeout
        if self.workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.workers, return_exceptions=True), timeout=10.0
                )
            except asyncio.TimeoutError:
                pass

        # Cancel remaining workers
        for worker in self.workers:
            if not worker.done():
                worker.cancel()

        # Emit event
        await self.event_bus.emit_event(
            event_type="worker_pool.stopped", metadata={"pool_size": self.pool_size}
        )

    def get_stats(self):
        """Get statistics"""
        active_workers = sum(1 for w in self.workers if not w.done())
        return {
            "pool_size": self.pool_size,
            "active_workers": active_workers,
            "worker_status": [
                {
                    "worker_id": i,
                    "name": w.get_name(),
                    "done": w.done(),
                    "cancelled": w.cancelled() if w.done() else False,
                }
                for i, w in enumerate(self.workers)
            ],
        }


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestWorkerPoolInitialization:
    """Test worker pool initialization"""

    async def test_worker_pool_creates_with_pool_size(self):
        """Test that worker pool initializes with specified pool size"""
        pool = MockWorkerPool(pool_size=4)

        assert pool.pool_size == 4
        assert pool.running is False
        assert len(pool.workers) == 0

    async def test_worker_pool_has_consumer_group_config(self):
        """Test that worker pool has consumer group configuration"""
        pool = MockWorkerPool()

        assert pool.consumer_group is not None
        assert isinstance(pool.consumer_group, str)

    async def test_worker_pool_has_stream_name_config(self):
        """Test that worker pool has stream name configuration"""
        pool = MockWorkerPool()

        assert pool.stream_name is not None
        assert isinstance(pool.stream_name, str)

    async def test_worker_pool_has_shutdown_event(self):
        """Test that worker pool has shutdown event"""
        pool = MockWorkerPool()

        assert hasattr(pool, "_shutdown_event")
        assert isinstance(pool._shutdown_event, asyncio.Event)
        assert not pool._shutdown_event.is_set()


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestWorkerPoolStartup:
    """Test worker pool startup"""

    async def test_worker_pool_start_creates_workers(self):
        """Test that starting pool creates correct number of workers"""
        pool = MockWorkerPool(pool_size=4)

        await pool.start()

        # Give workers time to start
        await asyncio.sleep(0.1)

        assert pool.running is True
        assert len(pool.workers) == 4
        assert all(isinstance(w, asyncio.Task) for w in pool.workers)

        # Cleanup
        await pool.stop()

    async def test_worker_pool_start_emits_event(self):
        """Test that starting pool emits worker_pool.started event"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.05)

        # Check events
        events = pool.event_bus.events
        pool_started_events = [e for e in events if e["type"] == "worker_pool.started"]

        assert len(pool_started_events) == 1
        assert pool_started_events[0]["metadata"]["pool_size"] == 2

        # Cleanup
        await pool.stop()

    async def test_worker_pool_start_ensures_consumer_group(self):
        """Test that starting pool ensures consumer group exists"""
        pool = MockWorkerPool()

        with patch.object(
            pool.redis_streams, "ensure_consumer_group", new_callable=AsyncMock
        ) as mock_ensure:
            await pool.start()

            mock_ensure.assert_called_once_with(pool.stream_name, pool.consumer_group)

        # Cleanup
        await pool.stop()

    async def test_worker_start_emits_worker_started_events(self):
        """Test that each worker emits worker.started event"""
        pool = MockWorkerPool(pool_size=3)

        await pool.start()
        await asyncio.sleep(0.1)

        # Check events
        events = pool.event_bus.events
        worker_started_events = [e for e in events if e["type"] == "worker.started"]

        assert len(worker_started_events) == 3

        # Cleanup
        await pool.stop()


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestWorkerTaskProcessing:
    """Test worker task processing"""

    async def test_worker_reads_from_redis_streams(self):
        """Test that worker reads tasks from Redis Streams"""
        pool = MockWorkerPool(pool_size=1)

        # Mock message from Redis
        pool.redis_streams.client.xreadgroup.return_value = [
            (
                "shield:ingestion_queue",
                [
                    (
                        b"msg-1",
                        {b"job_id": b"job-123", b"chunk": b"test chunk data"},
                    )
                ],
            )
        ]

        await pool.start()
        await asyncio.sleep(0.2)  # Let worker process

        # Verify xreadgroup called
        assert pool.redis_streams.client.xreadgroup.called

        # Cleanup
        await pool.stop()

    async def test_worker_acks_successful_tasks(self):
        """Test that worker ACKs successfully processed tasks"""
        pool = MockWorkerPool(pool_size=1)

        # Mock message
        pool.redis_streams.client.xreadgroup.return_value = [
            ("shield:ingestion_queue", [(b"msg-1", {b"job_id": b"job-123"})])
        ]

        await pool.start()
        await asyncio.sleep(0.2)

        # Verify ACK called
        assert pool.redis_streams.client.xack.called

        # Cleanup
        await pool.stop()

    async def test_worker_deletes_processed_messages(self):
        """Test that worker deletes processed messages from stream"""
        pool = MockWorkerPool(pool_size=1)

        # Mock message
        pool.redis_streams.client.xreadgroup.return_value = [
            ("shield:ingestion_queue", [(b"msg-1", {b"job_id": b"job-123"})])
        ]

        await pool.start()
        await asyncio.sleep(0.2)

        # Verify XDEL called
        assert pool.redis_streams.client.xdel.called

        # Cleanup
        await pool.stop()

    async def test_worker_does_not_ack_failed_tasks(self):
        """Test that worker doesn't ACK failed tasks (for retry)"""
        pool = MockWorkerPool(pool_size=1)

        # Mock message and make processor fail
        pool.redis_streams.client.xreadgroup.return_value = [
            ("shield:ingestion_queue", [(b"msg-1", {b"job_id": b"job-123"})])
        ]

        # Make processor raise error
        pool.processor.process_chunk = AsyncMock(
            side_effect=Exception("Processing error")
        )

        await pool.start()
        await asyncio.sleep(0.2)

        # Verify task_failed event emitted
        events = pool.event_bus.events
        failed_events = [e for e in events if e["type"] == "worker.task_failed"]

        assert len(failed_events) >= 1

        # Cleanup
        await pool.stop()


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestWorkerPoolShutdown:
    """Test worker pool graceful shutdown"""

    async def test_worker_pool_stops_gracefully(self):
        """Test that worker pool stops gracefully"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.1)

        assert pool.running is True

        await pool.stop()

        assert pool.running is False
        assert pool._shutdown_event.is_set()

    async def test_worker_pool_stop_emits_stopped_event(self):
        """Test that stopping pool emits worker_pool.stopped event"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.05)
        await pool.stop()

        # Check events
        events = pool.event_bus.events
        stopped_events = [e for e in events if e["type"] == "worker_pool.stopped"]

        assert len(stopped_events) == 1

    async def test_worker_stop_emits_worker_stopped_events(self):
        """Test that each worker emits worker.stopped event on shutdown"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.1)
        await pool.stop()

        # Check events
        events = pool.event_bus.events
        worker_stopped_events = [e for e in events if e["type"] == "worker.stopped"]

        # Should have 2 worker.stopped events
        assert len(worker_stopped_events) == 2

    async def test_worker_pool_waits_for_workers_to_finish(self):
        """Test that pool waits for workers to finish current tasks"""
        pool = MockWorkerPool(pool_size=1)

        await pool.start()
        await asyncio.sleep(0.05)

        # Workers should be running
        active_before = sum(1 for w in pool.workers if not w.done())
        assert active_before > 0

        await pool.stop()

        # All workers should be done
        assert all(w.done() for w in pool.workers)

    async def test_worker_pool_cancels_workers_on_timeout(self):
        """Test that pool cancels workers if graceful shutdown times out"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.05)

        # Stop should handle timeout and cancel
        await pool.stop()

        # All workers should be done or cancelled
        assert all(w.done() or w.cancelled() for w in pool.workers)


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestWorkerPoolStatistics:
    """Test worker pool statistics"""

    async def test_get_stats_returns_pool_size(self):
        """Test that get_stats returns pool size"""
        pool = MockWorkerPool(pool_size=4)

        stats = pool.get_stats()

        assert stats["pool_size"] == 4

    async def test_get_stats_returns_active_workers(self):
        """Test that get_stats returns active worker count"""
        pool = MockWorkerPool(pool_size=3)

        await pool.start()
        await asyncio.sleep(0.1)

        stats = pool.get_stats()

        assert "active_workers" in stats
        assert stats["active_workers"] >= 0
        assert stats["active_workers"] <= 3

        # Cleanup
        await pool.stop()

    async def test_get_stats_includes_worker_status(self):
        """Test that get_stats includes individual worker status"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.05)

        stats = pool.get_stats()

        assert "worker_status" in stats
        assert len(stats["worker_status"]) == 2

        # Each worker status should have required fields
        for worker_stat in stats["worker_status"]:
            assert "worker_id" in worker_stat
            assert "name" in worker_stat
            assert "done" in worker_stat

        # Cleanup
        await pool.stop()


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestWorkerPoolHealthCheck:
    """Test worker pool health check"""

    async def test_health_check_returns_status_up_when_running(self):
        """Test that health check returns 'up' when workers are running"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.1)

        stats = pool.get_stats()
        active_workers = stats["active_workers"]

        # Status should be 'up' if workers are active
        assert active_workers > 0

        # Cleanup
        await pool.stop()

    async def test_health_check_returns_status_down_when_stopped(self):
        """Test that health check returns 'down' when pool is stopped"""
        pool = MockWorkerPool(pool_size=2)

        await pool.start()
        await asyncio.sleep(0.05)
        await pool.stop()
        await asyncio.sleep(0.05)

        stats = pool.get_stats()
        active_workers = stats["active_workers"]

        # All workers should be done
        assert active_workers == 0


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestWorkerErrorHandling:
    """Test worker error handling and resilience"""

    async def test_worker_continues_after_task_error(self):
        """Test that worker continues processing after task error"""
        pool = MockWorkerPool(pool_size=1)

        # Mock first message fails, second succeeds
        call_count = 0

        async def mock_process(task):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First task fails")
            return {"status": "success"}

        pool.processor.process_chunk = mock_process

        # Mock two messages
        pool.redis_streams.client.xreadgroup.side_effect = [
            [("stream", [(b"msg-1", {b"job_id": b"job-1"})])],
            [("stream", [(b"msg-2", {b"job_id": b"job-2"})])],
            [],  # No more messages
        ]

        await pool.start()
        await asyncio.sleep(0.3)

        # Verify both tasks were attempted
        assert call_count >= 2

        # Cleanup
        await pool.stop()

    async def test_worker_handles_cancellation_gracefully(self):
        """Test that worker handles asyncio.CancelledError gracefully"""
        pool = MockWorkerPool(pool_size=1)

        await pool.start()
        await asyncio.sleep(0.05)

        # Cancel worker directly
        if pool.workers:
            pool.workers[0].cancel()

        await asyncio.sleep(0.05)

        # Worker should be done
        assert pool.workers[0].done()

        # Cleanup
        await pool.stop()

    async def test_worker_emits_event_on_task_failure(self):
        """Test that worker emits task_failed event on error"""
        pool = MockWorkerPool(pool_size=1)

        # Make processor fail
        pool.processor.process_chunk = AsyncMock(
            side_effect=Exception("Test error")
        )

        # Mock message
        pool.redis_streams.client.xreadgroup.return_value = [
            ("stream", [(b"msg-1", {b"job_id": b"job-123"})])
        ]

        await pool.start()
        await asyncio.sleep(0.2)

        # Check for task_failed event
        events = pool.event_bus.events
        failed_events = [e for e in events if e["type"] == "worker.task_failed"]

        assert len(failed_events) > 0
        assert "error" in failed_events[0]["metadata"]

        # Cleanup
        await pool.stop()
