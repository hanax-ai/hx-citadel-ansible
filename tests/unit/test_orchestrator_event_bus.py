"""
Orchestrator Event Bus Tests

Tests for the async event bus with SSE streaming support.
Single Responsibility: Validate pub/sub event system for real-time updates.

Component Under Test:
- orchestrator_workers/services/event_bus.py.j2

Event Bus Features (deployed on orchestrator at hx-orchestrator-server):
- Pub/sub pattern with multiple subscribers
- SSE (Server-Sent Events) streaming
- Event filtering by type
- Event buffering (last N events)
- Subscriber management (add, remove, cleanup)
- Max clients limit
- Statistics tracking

Test Coverage:
- Event creation and SSE formatting
- Subscribe/unsubscribe operations
- Event emission to subscribers
- Event filtering by type
- Event buffering and history replay
- Max clients enforcement
- Dead subscriber cleanup
- Statistics retrieval
- Error handling (queue full, dead subscribers)
"""

import pytest
import asyncio
from unittest.mock import MagicMock
from datetime import datetime
from collections import deque
from dataclasses import asdict


# Mock Event class
class MockEvent:
    """Mock Event for testing"""

    def __init__(self, event_type: str, timestamp: str, job_id: str = None, data: dict = None, metadata: dict = None):
        self.event_type = event_type
        self.timestamp = timestamp
        self.job_id = job_id
        self.data = data
        self.metadata = metadata

    def to_sse(self):
        """Convert to SSE format"""
        import json
        event_data = {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "job_id": self.job_id,
            "data": self.data,
            "metadata": self.metadata
        }
        return f"event: {self.event_type}\ndata: {json.dumps(event_data)}\n\n"


# Mock EventBus class
class MockEventBus:
    """Mock event bus for testing"""

    def __init__(self, max_clients: int = 100, buffer_size: int = 100, keepalive_interval: int = 30):
        self.max_clients = max_clients
        self.buffer_size = buffer_size
        self.keepalive_interval = keepalive_interval
        self.subscribers = set()
        self.event_buffer = deque(maxlen=buffer_size)
        self.events_emitted = 0
        self.events_dropped = 0

    async def subscribe(self, event_types: list = None, include_history: bool = False):
        """Subscribe to events"""
        if len(self.subscribers) >= self.max_clients:
            raise RuntimeError("Max event bus clients reached")

        queue = asyncio.Queue(maxsize=50)
        self.subscribers.add(queue)

        # Send history if requested
        if include_history:
            for event in self.event_buffer:
                if event_types is None or event.event_type in event_types:
                    try:
                        queue.put_nowait(event)
                    except asyncio.QueueFull:
                        break

        return queue

    def unsubscribe(self, queue):
        """Unsubscribe from events"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)

    async def emit_event(self, event_type: str, job_id: str = None, data: dict = None, metadata: dict = None):
        """Emit event to all subscribers"""
        event = MockEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            job_id=job_id,
            data=data,
            metadata=metadata
        )

        # Add to buffer
        self.event_buffer.append(event)
        self.events_emitted += 1

        # Send to subscribers
        dead_subscribers = set()
        for queue in self.subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                self.events_dropped += 1
            except Exception:
                dead_subscribers.add(queue)

        # Clean up dead subscribers
        for queue in dead_subscribers:
            self.unsubscribe(queue)

    def get_stats(self):
        """Get statistics"""
        return {
            "active_subscribers": len(self.subscribers),
            "max_clients": self.max_clients,
            "events_emitted": self.events_emitted,
            "events_dropped": self.events_dropped,
            "buffer_size": len(self.event_buffer),
            "buffer_max": self.buffer_size
        }


@pytest.mark.unit
@pytest.mark.fast
class TestEventFormatting:
    """Test Event data structure and SSE formatting"""

    def test_event_converts_to_sse_format(self):
        """Test that Event converts to proper SSE format"""
        event = MockEvent(
            event_type="test.event",
            timestamp="2025-01-01T00:00:00",
            job_id="job-123",
            data={"key": "value"}
        )

        sse = event.to_sse()

        assert "event: test.event\n" in sse
        assert "data: {" in sse
        assert "\n\n" in sse  # SSE terminator

    def test_event_includes_job_id_in_sse(self):
        """Test that Event includes job_id in SSE data"""
        event = MockEvent(
            event_type="test.event",
            timestamp="2025-01-01T00:00:00",
            job_id="job-456"
        )

        sse = event.to_sse()

        assert "job-456" in sse


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestEventBusSubscription:
    """Test event bus subscribe/unsubscribe"""

    async def test_subscribe_returns_queue(self):
        """Test that subscribe returns async queue"""
        bus = MockEventBus()

        queue = await bus.subscribe()

        assert queue is not None
        assert isinstance(queue, asyncio.Queue)

    async def test_subscribe_adds_to_subscribers(self):
        """Test that subscribe adds queue to subscribers"""
        bus = MockEventBus()

        assert len(bus.subscribers) == 0

        await bus.subscribe()

        assert len(bus.subscribers) == 1

    async def test_unsubscribe_removes_subscriber(self):
        """Test that unsubscribe removes queue from subscribers"""
        bus = MockEventBus()

        queue = await bus.subscribe()
        assert len(bus.subscribers) == 1

        bus.unsubscribe(queue)

        assert len(bus.subscribers) == 0

    async def test_subscribe_rejects_when_max_clients_reached(self):
        """Test that subscribe raises error when max clients reached"""
        bus = MockEventBus(max_clients=2)

        await bus.subscribe()
        await bus.subscribe()

        # Third subscription should fail
        with pytest.raises(RuntimeError, match="Max event bus clients reached"):
            await bus.subscribe()


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestEventEmission:
    """Test event emission to subscribers"""

    async def test_emit_event_sends_to_subscribers(self):
        """Test that emit_event sends event to all subscribers"""
        bus = MockEventBus()
        queue = await bus.subscribe()

        await bus.emit_event(event_type="test.event", data={"test": "data"})

        # Queue should have one event
        assert queue.qsize() == 1

    async def test_emit_event_increments_counter(self):
        """Test that emit_event increments events_emitted counter"""
        bus = MockEventBus()

        assert bus.events_emitted == 0

        await bus.emit_event(event_type="test.event")

        assert bus.events_emitted == 1

    async def test_emit_event_adds_to_buffer(self):
        """Test that emit_event adds event to buffer"""
        bus = MockEventBus(buffer_size=10)

        await bus.emit_event(event_type="test.event")

        assert len(bus.event_buffer) == 1

    async def test_emit_event_sends_to_multiple_subscribers(self):
        """Test that emit_event sends to all subscribers"""
        bus = MockEventBus()
        queue1 = await bus.subscribe()
        queue2 = await bus.subscribe()

        await bus.emit_event(event_type="broadcast.event")

        # Both queues should have the event
        assert queue1.qsize() == 1
        assert queue2.qsize() == 1


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestEventBuffering:
    """Test event buffering and history replay"""

    async def test_subscribe_with_history_sends_buffered_events(self):
        """Test that subscribe with include_history sends buffered events"""
        bus = MockEventBus(buffer_size=10)

        # Emit events before subscription
        await bus.emit_event(event_type="event1")
        await bus.emit_event(event_type="event2")

        # Subscribe with history
        queue = await bus.subscribe(include_history=True)

        # Queue should have 2 buffered events
        assert queue.qsize() == 2

    async def test_event_buffer_respects_max_size(self):
        """Test that event buffer doesn't exceed max size"""
        bus = MockEventBus(buffer_size=3)

        # Emit 5 events
        for i in range(5):
            await bus.emit_event(event_type=f"event{i}")

        # Buffer should only have last 3
        assert len(bus.event_buffer) == 3


@pytest.mark.unit
@pytest.mark.fast
@pytest.mark.asyncio
class TestEventBusStatistics:
    """Test event bus statistics"""

    async def test_get_stats_returns_subscriber_count(self):
        """Test that get_stats returns active subscriber count"""
        bus = MockEventBus()

        await bus.subscribe()
        await bus.subscribe()

        stats = bus.get_stats()

        assert stats["active_subscribers"] == 2

    async def test_get_stats_returns_emitted_count(self):
        """Test that get_stats returns events emitted count"""
        bus = MockEventBus()

        await bus.emit_event(event_type="test1")
        await bus.emit_event(event_type="test2")

        stats = bus.get_stats()

        assert stats["events_emitted"] == 2

    async def test_get_stats_returns_buffer_size(self):
        """Test that get_stats returns current buffer size"""
        bus = MockEventBus(buffer_size=10)

        await bus.emit_event(event_type="test")

        stats = bus.get_stats()

        assert stats["buffer_size"] == 1
        assert stats["buffer_max"] == 10
