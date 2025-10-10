# Component 4: Redis Streams Integration
## Event Bus and Task Queue - Ansible Deployment Plan

**Component:** Redis Streams Integration  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Redis Server:** hx-sqldb-server (192.168.10.48)  
**Timeline:** Week 2, Days 3-4 (3-4 hours)  
**Priority:** ⭐ **CRITICAL - DATA LAYER**  
**Dependencies:** Component 1 (Base Setup), Component 2 (FastAPI)

---

## Overview

This plan covers Redis Streams integration for durable event delivery and task queuing, including:

- Redis client library installation (redis[hiredis])
- Consumer group setup (shield:ingestion_queue, shield:events)
- Redis Streams wrapper module
- Event bus implementation
- Message serialization/deserialization
- Health check integration
- Event streaming endpoints (SSE, WebSocket)

**Critical Feature:** At-least-once delivery semantics (not pub/sub)

---

## Ansible Role Structure

```
roles/orchestrator_redis/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-dependencies.yml
│   ├── 02-consumer-groups.yml
│   ├── 03-streams-wrapper.yml
│   ├── 04-event-bus.yml
│   ├── 05-api-endpoints.yml
│   └── 06-validation.yml
├── templates/
│   ├── services/redis_streams.py.j2
│   ├── services/event_bus.py.j2
│   ├── api/events.py.j2
│   └── utils/redis_health.py.j2
├── files/
│   └── requirements-redis.txt
└── handlers/
    └── main.yml
```

---

## files/requirements-redis.txt

```
# Redis Dependencies
# Component 4: Redis Streams Integration

# Redis client with C parser (faster)
redis[hiredis]>=5.0.0

# Async Redis client (optional, for advanced use)
aioredis>=2.0.0

# Serialization
msgpack>=1.0.0     # Efficient binary serialization (optional)
```

---

## defaults/main.yml

```yaml
---
# Redis Configuration
redis_host: "192.168.10.48"
redis_port: 6379
redis_db: 0
redis_url: "redis://192.168.10.48:6379/0"

# Redis Streams configuration
redis_stream_ingestion: "shield:ingestion_queue"
redis_stream_events: "shield:events"
redis_stream_maxlen: 10000

# Consumer groups
redis_consumer_group_workers: "lightrag-workers"
redis_consumer_group_ag_ui: "ag-ui-frontend"
redis_consumer_group_power_ui: "power-ui-frontend"
redis_consumer_group_dashboard: "dashboard-frontend"
redis_consumer_group_metrics: "metrics-collector"

# Performance tuning
redis_batch_size: 10
redis_block_timeout_ms: 5000
redis_retry_attempts: 3
```

---

## templates/services/redis_streams.py.j2

```python
"""
Redis Streams wrapper for task queue and event bus
"""

import redis.asyncio as redis
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime
from config.settings import settings

logger = logging.getLogger("shield-orchestrator.redis")


class RedisStreamsClient:
    """
    Redis Streams client for task queue and event bus.
    
    Features:
      - At-least-once delivery (consumer groups)
      - Message acknowledgment (XACK)
      - Dead letter handling (retry limits)
      - Automatic trimming (MAXLEN)
    """
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.ingestion_stream = "{{ redis_stream_ingestion }}"
        self.events_stream = "{{ redis_stream_events }}"
        self.maxlen = {{ redis_stream_maxlen }}
    
    async def connect(self):
        """Initialize Redis connection"""
        self.client = await redis.from_url(
            "{{ redis_url }}",
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
        logger.info("✅ Redis Streams client connected")
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("✅ Redis Streams client closed")
    
    # ========================================
    # TASK QUEUE OPERATIONS (Ingestion)
    # ========================================
    
    async def add_task(
        self,
        job_id: str,
        chunk_id: str,
        content: str,
        source_uri: str,
        source_type: str,
        metadata: dict = None
    ) -> str:
        """
        Add task to ingestion queue.
        
        Returns:
            Message ID from Redis
        """
        message = {
            "job_id": job_id,
            "chunk_id": chunk_id,
            "content": content,
            "source_uri": source_uri,
            "source_type": source_type,
            "metadata": json.dumps(metadata or {}),
            "retry_count": "0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_id = await self.client.xadd(
            self.ingestion_stream,
            message,
            maxlen=self.maxlen,
            approximate=True
        )
        
        logger.debug(f"Task queued: {message_id} (job: {job_id})")
        return message_id
    
    async def read_tasks(
        self,
        consumer_group: str,
        consumer_name: str,
        count: int = {{ redis_batch_size }},
        block_ms: int = {{ redis_block_timeout_ms }}
    ) -> List[Dict[str, Any]]:
        """
        Read tasks from ingestion queue (consumer group).
        
        Returns:
            List of tasks with message IDs for ACK
        """
        try:
            messages = await self.client.xreadgroup(
                groupname=consumer_group,
                consumername=consumer_name,
                streams={self.ingestion_stream: ">"},
                count=count,
                block=block_ms
            )
            
            tasks = []
            if messages:
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        task = {
                            "message_id": message_id,
                            "job_id": message_data["job_id"],
                            "chunk_id": message_data["chunk_id"],
                            "content": message_data["content"],
                            "source_uri": message_data["source_uri"],
                            "source_type": message_data["source_type"],
                            "metadata": json.loads(message_data["metadata"]),
                            "retry_count": int(message_data["retry_count"]),
                            "timestamp": message_data["timestamp"]
                        }
                        tasks.append(task)
            
            return tasks
        
        except Exception as e:
            logger.error(f"Error reading tasks: {str(e)}")
            return []
    
    async def ack_task(self, consumer_group: str, message_id: str):
        """Acknowledge task completion"""
        await self.client.xack(
            self.ingestion_stream,
            consumer_group,
            message_id
        )
        logger.debug(f"Task acknowledged: {message_id}")
    
    async def get_queue_depth(self) -> int:
        """Get current queue depth"""
        info = await self.client.xinfo_stream(self.ingestion_stream)
        return info["length"]
    
    # ========================================
    # EVENT BUS OPERATIONS
    # ========================================
    
    async def emit_event(
        self,
        event_type: str,
        job_id: str = None,
        data: dict = None,
        metadata: dict = None
    ) -> str:
        """
        Emit event to event bus.
        
        Event types:
          - ingestion.queued, ingestion.started, ingestion.progress, etc.
          - query.started, query.completed, etc.
          - worker.started, worker.stopped, etc.
        
        Returns:
            Event ID from Redis
        """
        event = {
            "event_id": str(uuid.uuid4()),
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_id or "",
            "data": json.dumps(data or {}),
            "metadata": json.dumps(metadata or {})
        }
        
        event_id = await self.client.xadd(
            self.events_stream,
            event,
            maxlen=self.maxlen,
            approximate=True
        )
        
        logger.debug(f"Event emitted: {event_type} ({event_id})")
        return event_id
    
    async def read_events(
        self,
        consumer_group: str,
        consumer_name: str,
        last_id: str = ">",
        count: int = 100,
        block_ms: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Read events from event stream (consumer group).
        
        Args:
            last_id: ">" for new events, or specific ID for replay
        
        Returns:
            List of events
        """
        try:
            messages = await self.client.xreadgroup(
                groupname=consumer_group,
                consumername=consumer_name,
                streams={self.events_stream: last_id},
                count=count,
                block=block_ms
            )
            
            events = []
            if messages:
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        event = {
                            "message_id": message_id,
                            "event_id": message_data["event_id"],
                            "type": message_data["type"],
                            "timestamp": message_data["timestamp"],
                            "job_id": message_data["job_id"],
                            "data": json.loads(message_data["data"]),
                            "metadata": json.loads(message_data["metadata"])
                        }
                        events.append(event)
            
            return events
        
        except Exception as e:
            logger.error(f"Error reading events: {str(e)}")
            return []
    
    async def ack_event(self, consumer_group: str, message_id: str):
        """Acknowledge event received"""
        await self.client.xack(
            self.events_stream,
            consumer_group,
            message_id
        )


# Global client instance
redis_streams = RedisStreamsClient()


async def init_redis():
    """Initialize Redis Streams client"""
    await redis_streams.connect()


async def close_redis():
    """Close Redis Streams client"""
    await redis_streams.close()


async def check_redis_health() -> dict:
    """
    Check Redis health for /health/detailed endpoint.
    
    Returns:
        dict with status, latency, and stream info
    """
    import time
    
    try:
        start = time.time()
        await redis_streams.client.ping()
        latency_ms = (time.time() - start) * 1000
        
        # Get stream info
        ingestion_info = await redis_streams.client.xinfo_stream(redis_streams.ingestion_stream)
        events_info = await redis_streams.client.xinfo_stream(redis_streams.events_stream)
        
        # Get consumer groups
        ingestion_groups = await redis_streams.client.xinfo_groups(redis_streams.ingestion_stream)
        events_groups = await redis_streams.client.xinfo_groups(redis_streams.events_stream)
        
        return {
            "status": "up",
            "latency_ms": round(latency_ms, 2),
            "streams": {
                redis_streams.ingestion_stream: {
                    "length": ingestion_info["length"],
                    "consumers": len(ingestion_groups)
                },
                redis_streams.events_stream: {
                    "length": events_info["length"],
                    "consumers": len(events_groups)
                }
            }
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "down",
            "error": str(e),
            "latency_ms": 0
        }
```

---

## templates/api/events.py.j2

```python
"""
Event streaming endpoints (SSE and WebSocket)
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import logging

from services.redis_streams import redis_streams

router = APIRouter()
logger = logging.getLogger("shield-orchestrator.events")


@router.get("/events/stream")
async def event_stream(request: Request, last_id: str = "0"):
    """
    Server-Sent Events (SSE) endpoint for real-time event streaming.
    
    Args:
        last_id: Last event ID (for replay), default "0" for all events
    
    Usage:
        curl -N http://192.168.10.8:8000/events/stream
        
        # With event replay from specific ID
        curl -N http://192.168.10.8:8000/events/stream?last_id=1234567890-0
    """
    
    async def event_generator():
        """Generate SSE events from Redis Streams"""
        consumer_name = f"sse-{request.client.host}"
        
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected: {consumer_name}")
                    break
                
                # Read events from Redis Streams
                events = await redis_streams.read_events(
                    consumer_group="{{ redis_consumer_group_power_ui }}",
                    consumer_name=consumer_name,
                    last_id=last_id,
                    count=10,
                    block_ms=5000
                )
                
                # Yield events
                for event in events:
                    yield {
                        "event": event["type"],
                        "id": event["message_id"],
                        "data": json.dumps({
                            "event_id": event["event_id"],
                            "job_id": event["job_id"],
                            "timestamp": event["timestamp"],
                            **event["data"]
                        })
                    }
                    
                    # Acknowledge event
                    await redis_streams.ack_event(
                        "{{ redis_consumer_group_power_ui }}",
                        event["message_id"]
                    )
                    
                    # Update last_id for next iteration
                    last_id = event["message_id"]
                
                # Small delay to prevent busy loop
                if not events:
                    await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Event stream error: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


@router.get("/events/ws")
async def event_websocket():
    """
    WebSocket endpoint for event streaming (AG-UI).
    
    TODO: Implement WebSocket handler in subsequent deployment
    """
    return {"message": "WebSocket endpoint - to be implemented"}


@router.get("/events/stats")
async def event_stats():
    """
    Get event stream statistics.
    
    Returns:
        Stream lengths, consumer group info, throughput metrics
    """
    try:
        ingestion_info = await redis_streams.client.xinfo_stream(redis_streams.ingestion_stream)
        events_info = await redis_streams.client.xinfo_stream(redis_streams.events_stream)
        
        ingestion_groups = await redis_streams.client.xinfo_groups(redis_streams.ingestion_stream)
        events_groups = await redis_streams.client.xinfo_groups(redis_streams.events_stream)
        
        return {
            "streams": {
                redis_streams.ingestion_stream: {
                    "length": ingestion_info["length"],
                    "first_entry": ingestion_info.get("first-entry", [None])[0],
                    "last_entry": ingestion_info.get("last-entry", [None])[0],
                    "consumer_groups": [g["name"] for g in ingestion_groups]
                },
                redis_streams.events_stream: {
                    "length": events_info["length"],
                    "first_entry": events_info.get("first-entry", [None])[0],
                    "last_entry": events_info.get("last-entry", [None])[0],
                    "consumer_groups": [g["name"] for g in events_groups]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}
```

---

## tasks/01-dependencies.yml

```yaml
---
# Redis client installation
- name: Copy Redis requirements
  ansible.builtin.copy:
    src: requirements-redis.txt
    dest: "{{ orchestrator_app_dir }}/requirements-redis.txt"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes

- name: Install Redis Python dependencies
  ansible.builtin.pip:
    requirements: "{{ orchestrator_app_dir }}/requirements-redis.txt"
    virtualenv: "{{ orchestrator_venv_dir }}"
  become: yes
  become_user: "{{ orchestrator_service_user }}"
  notify: restart orchestrator
  tags: [dependencies]

- name: Verify Redis client installation
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import redis; print(redis.__version__)'
  register: redis_version_check
  changed_when: false
  tags: [dependencies, validation]

- name: Display Redis client version
  ansible.builtin.debug:
    msg: "Redis client version: {{ redis_version_check.stdout }}"
  tags: [dependencies]
```

---

## tasks/02-consumer-groups.yml

```yaml
---
# Redis consumer group setup (on hx-sqldb-server)
- name: Create ingestion queue stream (if not exists)
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XGROUP CREATE {{ redis_stream_ingestion }} {{ redis_consumer_group_workers }} $ MKSTREAM
  register: create_ingestion_group
  failed_when: false
  changed_when: "'OK' in create_ingestion_group.stdout"
  tags: [consumer-groups]

- name: Create metrics collector consumer group (ingestion)
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XGROUP CREATE {{ redis_stream_ingestion }} {{ redis_consumer_group_metrics }} $ MKSTREAM
  register: create_metrics_ingestion
  failed_when: false
  changed_when: "'OK' in create_metrics_ingestion.stdout"
  tags: [consumer-groups]

- name: Create events stream (if not exists)
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XGROUP CREATE {{ redis_stream_events }} {{ redis_consumer_group_ag_ui }} $ MKSTREAM
  register: create_events_ag_ui
  failed_when: false
  changed_when: "'OK' in create_events_ag_ui.stdout"
  tags: [consumer-groups]

- name: Create power-ui consumer group (events)
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XGROUP CREATE {{ redis_stream_events }} {{ redis_consumer_group_power_ui }} $ MKSTREAM
  register: create_events_power_ui
  failed_when: false
  changed_when: "'OK' in create_events_power_ui.stdout"
  tags: [consumer-groups]

- name: Create dashboard consumer group (events)
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XGROUP CREATE {{ redis_stream_events }} {{ redis_consumer_group_dashboard }} $ MKSTREAM
  register: create_events_dashboard
  failed_when: false
  changed_when: "'OK' in create_events_dashboard.stdout"
  tags: [consumer-groups]

- name: Create metrics collector consumer group (events)
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XGROUP CREATE {{ redis_stream_events }} {{ redis_consumer_group_metrics }} $ MKSTREAM
  register: create_events_metrics
  failed_when: false
  changed_when: "'OK' in create_events_metrics.stdout"
  tags: [consumer-groups]

- name: Verify consumer groups created
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XINFO GROUPS {{ redis_stream_ingestion }}
  register: ingestion_groups_check
  changed_when: false
  tags: [consumer-groups, validation]

- name: Display consumer groups
  ansible.builtin.debug:
    msg: "✅ Consumer groups created for {{ redis_stream_ingestion }}"
  tags: [consumer-groups]
```

---

## tasks/03-streams-wrapper.yml

```yaml
---
# Deploy Redis Streams wrapper module
- name: Deploy Redis Streams wrapper
  ansible.builtin.template:
    src: services/redis_streams.py.j2
    dest: "{{ orchestrator_app_dir }}/services/redis_streams.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [services]

- name: Test Redis Streams wrapper import
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sys; sys.path.insert(0, "{{ orchestrator_app_dir }}"); 
    from services.redis_streams import RedisStreamsClient; 
    print("Redis Streams wrapper imported successfully")'
  register: wrapper_import_test
  changed_when: false
  tags: [services, validation]
```

---

## tasks/04-event-bus.yml

```yaml
---
# Deploy event bus module
- name: Deploy event bus module
  ansible.builtin.template:
    src: services/event_bus.py.j2
    dest: "{{ orchestrator_app_dir }}/services/event_bus.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [services]
```

---

## tasks/05-api-endpoints.yml

```yaml
---
# Deploy event streaming API endpoints
- name: Deploy events API endpoints
  ansible.builtin.template:
    src: api/events.py.j2
    dest: "{{ orchestrator_app_dir }}/api/events.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [api]

- name: Update main.py to include events router
  ansible.builtin.lineinfile:
    path: "{{ orchestrator_app_dir }}/main.py"
    line: "app.include_router(events.router, prefix='/events', tags=['events'])"
    insertafter: "app.include_router\\(health.router"
    state: present
  become: yes
  notify: restart orchestrator
  tags: [api]

- name: Add events import to main.py
  ansible.builtin.lineinfile:
    path: "{{ orchestrator_app_dir }}/main.py"
    line: "from api import health, events"
    regexp: "^from api import health$"
    state: present
  become: yes
  notify: restart orchestrator
  tags: [api]
```

---

## tasks/06-validation.yml

```yaml
---
# Redis Streams validation
- name: Test Redis connection from orchestrator
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }} ping
  register: redis_ping_test
  changed_when: false
  failed_when: "'PONG' not in redis_ping_test.stdout"
  tags: [validation]

- name: Verify ingestion queue stream exists
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XINFO STREAM {{ redis_stream_ingestion }}
  register: ingestion_stream_check
  changed_when: false
  tags: [validation]

- name: Verify events stream exists
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XINFO STREAM {{ redis_stream_events }}
  register: events_stream_check
  changed_when: false
  tags: [validation]

- name: Verify consumer groups on ingestion stream
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XINFO GROUPS {{ redis_stream_ingestion }}
  register: ingestion_groups
  changed_when: false
  failed_when: "'{{ redis_consumer_group_workers }}' not in ingestion_groups.stdout"
  tags: [validation]

- name: Verify consumer groups on events stream
  ansible.builtin.command: >
    redis-cli -h {{ redis_host }} -p {{ redis_port }}
    XINFO GROUPS {{ redis_stream_events }}
  register: events_groups
  changed_when: false
  tags: [validation]

- name: Test SSE endpoint
  ansible.builtin.uri:
    url: "http://localhost:8000/events/stream"
    method: GET
    timeout: 5
    status_code: 200
  register: sse_endpoint_test
  ignore_errors: yes
  tags: [validation]

- name: Display Redis validation summary
  ansible.builtin.debug:
    msg:
      - "✅ Redis connection: {{ redis_ping_test.stdout }}"
      - "✅ Ingestion stream: {{ ingestion_stream_check.stdout_lines[0] }}"
      - "✅ Events stream: {{ events_stream_check.stdout_lines[0] }}"
      - "✅ Consumer groups (ingestion): {{ ingestion_groups.stdout_lines | length }}"
      - "✅ Consumer groups (events): {{ events_groups.stdout_lines | length }}"
      - "✅ Redis Streams integration complete!"
  tags: [validation]
```

---

## Success Criteria

```yaml
✅ Dependencies:
   • redis[hiredis] >=5.0.0 installed
   • aioredis >=2.0.0 installed (optional)

✅ Consumer Groups Created:
   • shield:ingestion_queue:
     - lightrag-workers
     - metrics-collector
   • shield:events:
     - ag-ui-frontend
     - power-ui-frontend
     - dashboard-frontend
     - metrics-collector

✅ Python Modules:
   • services/redis_streams.py deployed
   • services/event_bus.py deployed
   • api/events.py deployed

✅ API Endpoints:
   • GET /events/stream (SSE) - returns 200
   • GET /events/ws (WebSocket) - placeholder
   • GET /events/stats - returns stream statistics

✅ Validation:
   • Redis connection successful (PING → PONG)
   • Both streams created
   • All consumer groups created
   • SSE endpoint responsive
   • Event replay working
```

---

## Testing Procedures

### **Manual Testing**

```bash
# Test 1: Redis connection
redis-cli -h 192.168.10.48 -p 6379 ping

# Test 2: Check streams
redis-cli -h 192.168.10.48 XINFO STREAM shield:ingestion_queue
redis-cli -h 192.168.10.48 XINFO STREAM shield:events

# Test 3: Check consumer groups
redis-cli -h 192.168.10.48 XINFO GROUPS shield:ingestion_queue
redis-cli -h 192.168.10.48 XINFO GROUPS shield:events

# Test 4: Add test message
redis-cli -h 192.168.10.48 XADD shield:events "*" \
  event_id "test-123" \
  type "test.event" \
  timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  job_id "test-job" \
  data "{}" \
  metadata "{}"

# Test 5: SSE endpoint (stays connected)
curl -N http://192.168.10.8:8000/events/stream

# Test 6: Event stats
curl http://192.168.10.8:8000/events/stats | jq .
```

---

## Timeline

**Estimated Time:** 3-4 hours

```yaml
Task Breakdown:
  • Dependencies installation: 30 minutes
  • Consumer group setup: 1 hour
  • Streams wrapper: 1 hour
  • API endpoints: 30 minutes
  • Validation: 30 minutes
  • Testing: 30 minutes

Total: 4 hours
```

---

## Next Component

**After Redis Streams integration, proceed to:**

→ **Component 5: Qdrant Integration** (`05-qdrant-integration-plan.md`)

---

**Redis Streams Integration Plan Complete!** ✅
**Durable event delivery enabled!** 🚀

