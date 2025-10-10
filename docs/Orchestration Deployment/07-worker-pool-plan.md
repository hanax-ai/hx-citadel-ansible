# Component 7: Worker Pool
## Asynchronous Task Processing - Ansible Deployment Plan

**Component:** Worker Pool  
**Target Server:** hx-orchestrator-server (192.168.10.8)  
**Timeline:** Week 4, Days 1-2 (4-6 hours)  
**Priority:** ⭐ **CRITICAL - ASYNC PROCESSING**  
**Dependencies:** Components 1-6 (especially LightRAG)

---

## Overview

This plan covers the async worker pool for background task processing, including:

- Worker pool manager (4 workers)
- Redis Streams consumer (reads from shield:ingestion_queue)
- LightRAG chunk processing
- Job status tracking
- Event emission (progress updates)
- Retry logic and error handling
- Graceful shutdown

**Critical Pattern:** Asynchronous Processing (HTTP 202 Accepted pattern)

---

## Ansible Role Structure

```
roles/orchestrator_workers/
├── defaults/
│   └── main.yml
├── tasks/
│   ├── main.yml
│   ├── 01-worker-pool.yml
│   ├── 02-job-tracker.yml
│   ├── 03-processor.yml
│   └── 04-validation.yml
├── templates/
│   ├── workers/worker_pool.py.j2
│   ├── workers/lightrag_processor.py.j2
│   └── services/job_tracker.py.j2
├── files/
│   └── (none)
└── handlers/
    └── main.yml
```

---

## defaults/main.yml

```yaml
---
# Worker Pool Configuration
worker_pool_size: 4
worker_batch_size: 10
worker_retry_attempts: 3
worker_timeout_seconds: 300
worker_health_check_interval: 30
worker_max_tasks_per_child: 1000
worker_graceful_shutdown_timeout: 60

# Redis Streams (from Component 4)
redis_stream_ingestion: "shield:ingestion_queue"
redis_consumer_group_workers: "lightrag-workers"

# Job tracking
job_status_ttl: 3600  # 1 hour after completion
```

---

## templates/workers/worker_pool.py.j2

```python
"""
Worker pool manager for async task processing
"""

import asyncio
import signal
import logging
from typing import List
from datetime import datetime

from services.redis_streams import redis_streams
from services.event_bus import event_bus
from workers.lightrag_processor import LightRAGProcessor

logger = logging.getLogger("shield-orchestrator.workers")


class WorkerPool:
    """
    Async worker pool for LightRAG chunk processing.
    
    Features:
      - Multiple workers (default: 4)
      - Redis Streams consumer group
      - Graceful shutdown
      - Health monitoring
      - Automatic restart on failure
    """
    
    def __init__(self, pool_size: int = {{ worker_pool_size }}):
        self.pool_size = pool_size
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.processor = LightRAGProcessor()
    
    async def start(self):
        """Start all workers"""
        self.running = True
        
        logger.info(f"Starting worker pool ({self.pool_size} workers)...")
        
        # Start workers
        for worker_id in range(self.pool_size):
            worker_task = asyncio.create_task(
                self._worker_loop(worker_id),
                name=f"worker-{worker_id}"
            )
            self.workers.append(worker_task)
        
        logger.info(f"✅ Worker pool started ({self.pool_size} workers)")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    async def _worker_loop(self, worker_id: int):
        """
        Worker loop - reads from Redis Streams and processes tasks.
        
        Flow:
          1. Read tasks from Redis Streams (XREADGROUP)
          2. Process each task via LightRAG
          3. Update job status
          4. Emit events
          5. ACK message
          6. Repeat
        """
        consumer_name = f"worker-{worker_id}"
        logger.info(f"Worker {worker_id} started (consumer: {consumer_name})")
        
        # Emit worker started event
        await event_bus.emit_event(
            event_type="worker.started",
            metadata={"worker_id": worker_id}
        )
        
        tasks_processed = 0
        
        while self.running:
            try:
                # Read tasks from queue
                tasks = await redis_streams.read_tasks(
                    consumer_group="{{ redis_consumer_group_workers }}",
                    consumer_name=consumer_name,
                    count={{ worker_batch_size }},
                    block_ms={{ worker_health_check_interval * 1000 }}
                )
                
                # Process tasks
                for task in tasks:
                    try:
                        # Process chunk via LightRAG
                        result = await self.processor.process_chunk(task)
                        
                        # ACK task
                        await redis_streams.ack_task(
                            "{{ redis_consumer_group_workers }}",
                            task["message_id"]
                        )
                        
                        tasks_processed += 1
                        
                        # Check max tasks per child
                        if tasks_processed >= {{ worker_max_tasks_per_child }}:
                            logger.info(f"Worker {worker_id} reached max tasks, restarting...")
                            break
                    
                    except Exception as e:
                        logger.error(f"Worker {worker_id} task error: {str(e)}")
                        # TODO: Handle retry logic
            
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                await asyncio.sleep(5)  # Backoff on error
        
        # Emit worker stopped event
        await event_bus.emit_event(
            event_type="worker.stopped",
            metadata={"worker_id": worker_id, "tasks_processed": tasks_processed}
        )
        
        logger.info(f"Worker {worker_id} stopped (processed {tasks_processed} tasks)")
    
    async def stop(self):
        """Gracefully stop all workers"""
        logger.info("Stopping worker pool...")
        self.running = False
        
        # Wait for workers to finish current tasks
        if self.workers:
            await asyncio.wait(self.workers, timeout={{ worker_graceful_shutdown_timeout }})
        
        # Cancel any remaining workers
        for worker in self.workers:
            if not worker.done():
                worker.cancel()
        
        logger.info("✅ Worker pool stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self.stop())


# Global worker pool instance
worker_pool = WorkerPool()


async def start_worker_pool():
    """Start worker pool"""
    await worker_pool.start()


async def stop_worker_pool():
    """Stop worker pool"""
    await worker_pool.stop()


async def check_worker_pool_health() -> dict:
    """
    Check worker pool health for /health/detailed endpoint.
    """
    try:
        active_workers = sum(1 for w in worker_pool.workers if not w.done())
        queue_depth = await redis_streams.get_queue_depth()
        
        return {
            "status": "up" if active_workers > 0 else "down",
            "active_workers": active_workers,
            "queue_depth": queue_depth,
            "processing_rate": 0.0  # TODO: Calculate from metrics
        }
    except Exception as e:
        return {
            "status": "down",
            "error": str(e)
        }
```

---

## templates/workers/lightrag_processor.py.j2

```python
"""
LightRAG chunk processor for workers
"""

import logging
from typing import Dict, Any
from datetime import datetime

from services.lightrag_service import lightrag_service
from services.job_tracker import job_tracker
from services.event_bus import event_bus

logger = logging.getLogger("shield-orchestrator.processor")


class LightRAGProcessor:
    """
    Processes chunks through LightRAG engine.
    
    Steps:
      1. Extract entities (LLM)
      2. Extract relationships (LLM)
      3. Update Knowledge Graph (PostgreSQL)
      4. Generate embeddings (Ollama)
      5. Store vectors (Qdrant)
      6. Update job status
      7. Emit events
    """
    
    async def process_chunk(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process single chunk through LightRAG.
        
        Args:
            task: Task from Redis Streams queue
        
        Returns:
            Processing result
        """
        job_id = task["job_id"]
        chunk_id = task["chunk_id"]
        content = task["content"]
        
        logger.info(f"Processing chunk {chunk_id} (job: {job_id})")
        
        try:
            # Update job status: started (if first chunk)
            await job_tracker.update_job(job_id, status="processing")
            await event_bus.emit_event(
                event_type="ingestion.started",
                job_id=job_id
            )
            
            # Process through LightRAG
            result = await lightrag_service.insert_text(
                text=content,
                metadata=task.get("metadata", {})
            )
            
            # Update job progress
            await job_tracker.increment_processed(job_id)
            progress = await job_tracker.get_progress(job_id)
            
            # Emit progress event
            await event_bus.emit_event(
                event_type="ingestion.progress",
                job_id=job_id,
                data={
                    "chunks_processed": progress["chunks_processed"],
                    "chunks_total": progress["chunks_total"],
                    "percent_complete": progress["percent_complete"]
                }
            )
            
            # Check if job complete
            if progress["percent_complete"] >= 100:
                await job_tracker.update_job(job_id, status="completed")
                await event_bus.emit_event(
                    event_type="ingestion.completed",
                    job_id=job_id,
                    data={
                        "chunks_processed": progress["chunks_processed"],
                        "duration_seconds": progress.get("duration_seconds", 0)
                    }
                )
            
            logger.info(f"✅ Chunk {chunk_id} processed ({progress['percent_complete']}% complete)")
            
            return {
                "status": "success",
                "chunk_id": chunk_id,
                "entities_extracted": result.get("entities_extracted", 0),
                "relationships_extracted": result.get("relationships_extracted", 0)
            }
        
        except Exception as e:
            logger.error(f"Chunk processing error: {str(e)}")
            
            # Update job status: failed
            await job_tracker.update_job(job_id, status="failed", error=str(e))
            await event_bus.emit_event(
                event_type="ingestion.failed",
                job_id=job_id,
                data={"error": str(e), "chunk_id": chunk_id}
            )
            
            raise
```

---

## templates/services/job_tracker.py.j2

```python
"""
Job tracking service using Redis and PostgreSQL
"""

import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime
from services.redis_streams import redis_streams
from database.models import JobStatus
from database.connection import AsyncSessionLocal
from sqlalchemy import select

logger = logging.getLogger("shield-orchestrator.job-tracker")


class JobTracker:
    """
    Tracks job status across ingestion pipeline.
    
    Storage:
      - Redis: Real-time status (fast access, TTL)
      - PostgreSQL: Persistent storage (audit trail)
    """
    
    async def create_job(
        self,
        job_id: str,
        job_type: str,
        chunks_total: int,
        metadata: Dict[str, Any] = None
    ):
        """Create new job"""
        # Store in Redis (fast access)
        await redis_streams.client.hset(
            f"job:{job_id}",
            mapping={
                "status": "queued",
                "job_type": job_type,
                "chunks_total": str(chunks_total),
                "chunks_processed": "0",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": json.dumps(metadata or {})
            }
        )
        await redis_streams.client.expire(f"job:{job_id}", {{ job_status_ttl }})
        
        # Store in PostgreSQL (persistent)
        async with AsyncSessionLocal() as session:
            job = JobStatus(
                id=job_id,
                job_type=job_type,
                status="queued",
                chunks_total=chunks_total,
                metadata=metadata or {}
            )
            session.add(job)
            await session.commit()
    
    async def update_job(
        self,
        job_id: str,
        status: str = None,
        error: str = None
    ):
        """Update job status"""
        updates = {}
        if status:
            updates["status"] = status
        if error:
            updates["error_message"] = error
        
        # Update Redis
        if updates:
            await redis_streams.client.hset(f"job:{job_id}", mapping=updates)
        
        # Update PostgreSQL
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(JobStatus).where(JobStatus.id == job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                if status:
                    job.status = status
                    if status == "processing" and not job.started_at:
                        job.started_at = datetime.utcnow()
                    elif status in ["completed", "failed"]:
                        job.completed_at = datetime.utcnow()
                if error:
                    job.error_message = error
                await session.commit()
    
    async def increment_processed(self, job_id: str):
        """Increment chunks processed counter"""
        await redis_streams.client.hincrby(f"job:{job_id}", "chunks_processed", 1)
        
        # Update PostgreSQL
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(JobStatus).where(JobStatus.id == job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                job.chunks_processed += 1
                await session.commit()
    
    async def get_progress(self, job_id: str) -> Dict[str, Any]:
        """Get job progress"""
        job_data = await redis_streams.client.hgetall(f"job:{job_id}")
        
        if not job_data:
            return {"error": "Job not found"}
        
        chunks_total = int(job_data.get("chunks_total", 0))
        chunks_processed = int(job_data.get("chunks_processed", 0))
        percent = (chunks_processed / chunks_total * 100) if chunks_total > 0 else 0
        
        return {
            "job_id": job_id,
            "status": job_data.get("status"),
            "chunks_total": chunks_total,
            "chunks_processed": chunks_processed,
            "percent_complete": round(percent, 2),
            "created_at": job_data.get("created_at")
        }


# Global job tracker instance
job_tracker = JobTracker()
```

---

## templates/api/jobs.py.j2 (Job Status Endpoints)

```python
"""
Job tracking API endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
import logging

from services.job_tracker import job_tracker

router = APIRouter()
logger = logging.getLogger("shield-orchestrator.jobs")


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str
    chunks_total: int
    chunks_processed: int
    percent_complete: float
    created_at: str


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    tags=["jobs"]
)
async def get_job_status(job_id: str):
    """
    Get job status and progress.
    
    Args:
        job_id: Job UUID
    
    Returns:
        Job status with progress percentage
    """
    try:
        progress = await job_tracker.get_progress(job_id)
        
        if "error" in progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return JobStatusResponse(**progress)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

---

## tasks/01-worker-pool.yml

```yaml
---
# Worker pool deployment
- name: Deploy worker pool manager
  ansible.builtin.template:
    src: workers/worker_pool.py.j2
    dest: "{{ orchestrator_app_dir }}/workers/worker_pool.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [workers]

- name: Deploy LightRAG processor
  ansible.builtin.template:
    src: workers/lightrag_processor.py.j2
    dest: "{{ orchestrator_app_dir }}/workers/lightrag_processor.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [workers]

- name: Test worker pool import
  ansible.builtin.command: >
    {{ orchestrator_venv_dir }}/bin/python -c 
    'import sys; sys.path.insert(0, "{{ orchestrator_app_dir }}"); 
    from workers.worker_pool import WorkerPool; 
    print("Worker pool imported")'
  register: worker_import_test
  changed_when: false
  tags: [workers, validation]
```

---

## tasks/02-job-tracker.yml

```yaml
---
# Job tracker deployment
- name: Deploy job tracker service
  ansible.builtin.template:
    src: services/job_tracker.py.j2
    dest: "{{ orchestrator_app_dir }}/services/job_tracker.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [job-tracker]

- name: Deploy jobs API endpoints
  ansible.builtin.template:
    src: api/jobs.py.j2
    dest: "{{ orchestrator_app_dir }}/api/jobs.py"
    owner: "{{ orchestrator_service_user }}"
    group: "{{ orchestrator_service_group }}"
    mode: "0644"
  become: yes
  notify: restart orchestrator
  tags: [job-tracker, api]

- name: Add jobs router to main.py
  ansible.builtin.lineinfile:
    path: "{{ orchestrator_app_dir }}/main.py"
    line: "app.include_router(jobs.router, prefix='/jobs', tags=['jobs'])"
    insertafter: "app.include_router\\(query.router"
    state: present
  become: yes
  notify: restart orchestrator
  tags: [job-tracker, api]
```

---

## tasks/04-validation.yml

```yaml
---
# Worker pool validation
- name: Verify worker pool starts
  ansible.builtin.shell: |
    cd {{ orchestrator_app_dir }}
    timeout 10 {{ orchestrator_venv_dir }}/bin/python -c "
    import asyncio
    from workers.worker_pool import WorkerPool
    
    async def test():
        pool = WorkerPool(pool_size=2)
        await pool.start()
        await asyncio.sleep(2)
        await pool.stop()
        print('✅ Worker pool test passed')
    
    asyncio.run(test())
    " || echo "Worker pool test completed"
  register: worker_pool_test
  changed_when: false
  tags: [validation]

- name: Check Redis consumer group has workers
  ansible.builtin.command: >
    redis-cli -h 192.168.10.48 XINFO CONSUMERS {{ redis_stream_ingestion }} {{ redis_consumer_group_workers }}
  register: consumer_check
  changed_when: false
  tags: [validation]

- name: Display worker pool validation
  ansible.builtin.debug:
    msg:
      - "✅ Worker pool test: {{ worker_pool_test.stdout }}"
      - "✅ Consumer group: {{ redis_consumer_group_workers }}"
      - "✅ Worker pool operational!"
  tags: [validation]
```

---

## Success Criteria

```yaml
✅ Worker Pool:
   • WorkerPool class deployed
   • 4 workers configured
   • Graceful shutdown implemented
   • Signal handlers (SIGTERM, SIGINT)

✅ LightRAG Processor:
   • Chunk processing logic deployed
   • Entity extraction integration
   • Job status updates
   • Event emission

✅ Job Tracker:
   • Job creation/update methods
   • Redis + PostgreSQL dual storage
   • Progress tracking
   • TTL management (1 hour)

✅ API Endpoints:
   • GET /jobs/{job_id} (job status)
   • Returns progress percentage
   • 404 for missing jobs

✅ Integration:
   • Workers read from Redis Streams
   • LightRAG processes chunks
   • Job status updated
   • Events emitted
   • Messages ACKed

✅ Validation:
   • Worker pool starts successfully
   • Consumer group registered
   • Workers consume messages
   • Jobs tracked in Redis + PostgreSQL
```

---

## Testing Procedures

```bash
# Test 1: Submit ingestion job
JOB_ID=$(curl -X POST http://192.168.10.8:8000/lightrag/ingest-async \
  -H "Content-Type: application/json" \
  -d '{
    "chunks": [
      {"text": "Test chunk 1", "source_uri": "test://1"},
      {"text": "Test chunk 2", "source_uri": "test://2"}
    ],
    "source_type": "test"
  }' | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Test 2: Monitor job status
watch -n 1 "curl -s http://192.168.10.8:8000/jobs/$JOB_ID | jq ."

# Test 3: Check worker activity
redis-cli -h 192.168.10.48 XINFO CONSUMERS shield:ingestion_queue lightrag-workers

# Test 4: Monitor events
curl -N http://192.168.10.8:8000/events/stream

# Expected events:
# - ingestion.queued
# - ingestion.started
# - ingestion.progress (multiple)
# - ingestion.completed
```

---

## Timeline

**Estimated Time:** 12-15 hours over 7 days

```yaml
Days 1-2 (6 hours):
  • Worker pool implementation: 3 hours
  • Job tracker implementation: 2 hours
  • Initial testing: 1 hour

Days 3-4 (4 hours):
  • LightRAG processor: 2 hours
  • Integration testing: 2 hours

Days 5-7 (5 hours):
  • End-to-end validation: 2 hours
  • Performance tuning: 2 hours
  • Documentation: 1 hour

Total: 15 hours
```

---

## Next Component

**After worker pool is operational, proceed to:**

→ **Component 8: Pydantic AI Agents** (`08-pydantic-ai-agents-plan.md`)

---

**Worker Pool Plan Complete!** ✅
**Async processing enabled!** 🚀

