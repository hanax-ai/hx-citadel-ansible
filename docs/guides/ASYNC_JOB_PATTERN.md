# Async Job Pattern Guide
## HTTP 202 Accepted Pattern for Long-Running Operations

**Version**: 1.0  
**Date**: October 10, 2025  
**Status**: Implementation Guide  
**Related**: CODEBASE-ENHANCEMENT-RECOMMENDATIONS.md

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [The Solution](#the-solution)
4. [Architecture](#architecture)
5. [Implementation Guide](#implementation-guide)
6. [Client Integration](#client-integration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 OVERVIEW

### What is the HTTP 202 Pattern?

The HTTP 202 Accepted pattern is a RESTful approach for handling **long-running operations** that exceed typical HTTP timeout thresholds (30-60 seconds).

**Key Concept**: Instead of blocking the client while processing, the server:
1. **Immediately accepts** the request (< 200ms)
2. **Returns HTTP 202** with a job identifier
3. **Processes asynchronously** in the background
4. **Provides status endpoint** for polling
5. **Streams events** (optional) for real-time updates

### When to Use

✅ **Use HTTP 202 when**:
- Operation takes > 5 seconds
- Processing time is unpredictable
- Client might timeout
- Progress updates are valuable
- Operation can be retried safely

❌ **Don't use HTTP 202 for**:
- Fast operations (< 2 seconds)
- Operations requiring immediate response
- Simple CRUD operations
- Synchronous workflows

### Benefits

| Benefit | Description |
|---------|-------------|
| **No Timeouts** | Client gets immediate response |
| **Better UX** | Non-blocking UI, progress indicators |
| **Scalability** | Frees up connections, enables queuing |
| **Retry-Safe** | Idempotent job IDs prevent duplicates |
| **Observability** | Job tracking, metrics, audit trail |

---

## ❌ THE PROBLEM

### Synchronous Request Flow (Current)

```
┌─────────┐                    ┌─────────────┐                  ┌──────────────┐
│ Client  │                    │  MCP Server │                  │ Orchestrator │
│ (LLM)   │                    │             │                  │              │
└────┬────┘                    └──────┬──────┘                  └──────┬───────┘
     │                                │                                │
     │ POST /crawl_web               │                                │
     │ {"url": "example.com"}        │                                │
     ├──────────────────────────────>│                                │
     │                                │                                │
     │                                │ Start crawling (5s)            │
     │                                ├───────────┐                    │
     │                                │           │                    │
     │                                │<──────────┘                    │
     │                                │                                │
     │                                │ POST /ingest                   │
     │                                ├───────────────────────────────>│
     │                                │                                │
     │                                │                                │ Process content (60s)
     │                                │                                ├──────────────┐
     │                                │                                │              │
     │      ⏳ WAITING (65 seconds) │                                │              │
     │                                │                                │              │
     │                                │                                │<─────────────┘
     │                                │                                │
     │                                │                                │ Store in Qdrant (5s)
     │                                │                                ├──────────────┐
     │                                │                                │              │
     │                                │                                │<─────────────┘
     │                                │                                │
     │                                │<───────────────────────────────┤
     │                                │ {"status": "success"}          │
     │                                │                                │
     │<───────────────────────────────┤                                │
     │ 200 OK (after 70 seconds) ❌   │                                │
     │ TIMEOUT!                       │                                │
     │                                │                                │
```

### Problems

1. **Client Timeout** (30-60s default)
   - Request fails even though processing continues
   - User sees error, but work happens anyway
   - Wasted resources, duplicate retries

2. **Blocking UI**
   - User waits with no feedback
   - Can't do other work
   - Poor experience

3. **Resource Exhaustion**
   - Threads/connections tied up
   - Can't scale to many concurrent users
   - Server becomes unresponsive

4. **No Progress Visibility**
   - Don't know if it's working
   - Can't estimate completion time
   - Can't cancel if needed

---

## ✅ THE SOLUTION

### Asynchronous Request Flow (Target)

```
┌─────────┐                    ┌─────────────┐                  ┌──────────────┐
│ Client  │                    │  MCP Server │                  │ Orchestrator │
│ (LLM)   │                    │             │                  │              │
└────┬────┘                    └──────┬──────┘                  └──────┬───────┘
     │                                │                                │
     │ POST /crawl_web               │                                │
     │ {"url": "example.com"}        │                                │
     ├──────────────────────────────>│                                │
     │                                │                                │
     │                                │ POST /ingest-async             │
     │                                ├───────────────────────────────>│
     │                                │                                │
     │                                │                                │ Queue job
     │                                │                                ├─────────┐
     │                                │<───────────────────────────────┤         │
     │                                │ {"job_id": "abc123"}           │<────────┘
     │<───────────────────────────────┤                                │
     │ 202 Accepted (< 200ms) ✅      │                                │
     │ {"job_id": "abc123",           │                                │
     │  "status": "queued"}           │                                │
     │                                │                                │
     │                                │                                │ Background worker
     │                                │                                ├──────────────┐
     │ GET /jobs/abc123              │                                │ Processing   │
     ├──────────────────────────────>│                                │              │
     │<───────────────────────────────┤                                │              │
     │ {"status": "processing",       │                                │              │
     │  "progress": 25%}              │                                │              │
     │                                │                                │              │
     │ (SSE) /jobs/abc123/events     │                                │              │
     ├──────────────────────────────>│<───────────────────────────────┤              │
     │<───────────────────────────────┤ Event: crawl_complete          │              │
     │ data: {"status": "crawling"}   │                                │              │
     │<───────────────────────────────┤                                │              │
     │ data: {"status": "processing"} │<───────────────────────────────┤              │
     │                                │ Event: ingest_progress         │              │
     │                                │                                │              │
     │ GET /jobs/abc123              │                                │              │
     ├──────────────────────────────>│                                │<─────────────┘
     │<───────────────────────────────┤                                │
     │ {"status": "completed",        │                                │
     │  "result": {...}}              │                                │
     │                                │                                │
```

### Key Improvements

1. **Immediate Response** (< 200ms)
   - No timeouts
   - Client can continue immediately
   - Job queued safely

2. **Progress Tracking**
   - Poll `/jobs/{job_id}` endpoint
   - SSE events for real-time updates
   - Know exactly what's happening

3. **Non-Blocking**
   - UI stays responsive
   - Can do other work
   - Better user experience

4. **Scalable**
   - Connections freed immediately
   - Worker pool processes jobs
   - Can queue thousands of jobs

---

## 🏗️ ARCHITECTURE

### Components

```
┌────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  LiteLLM     │  │  CopilotKit  │  │  Direct API  │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                    MCP SERVER LAYER                                 │
│                            │                                        │
│  ┌─────────────────────────▼──────────────────────────┐            │
│  │              FastMCP Server                         │            │
│  │  ┌──────────────────────────────────────────────┐  │            │
│  │  │  @mcp.tool() async def crawl_web(...)        │  │            │
│  │  │    1. Call orchestrator /ingest-async        │  │            │
│  │  │    2. Return HTTP 202 + job_id               │  │            │
│  │  └──────────────────────────────────────────────┘  │            │
│  └──────────────────────────┬──────────────────────────┘            │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Endpoints                                            │  │
│  │  ┌────────────────────┐  ┌────────────────────┐              │  │
│  │  │ POST /ingest-async │  │ GET /jobs/{job_id} │              │  │
│  │  │ - Generate job_id  │  │ - Query Redis      │              │  │
│  │  │ - Publish to Redis │  │ - Return status    │              │  │
│  │  │ - Return 202       │  │ - Return result    │              │  │
│  │  └─────────┬──────────┘  └────────────────────┘              │  │
│  └────────────┼─────────────────────────────────────────────────┘  │
│               │                                                     │
│  ┌────────────▼──────────────────────────────────────────────────┐ │
│  │  Redis Streams (Event Bus)                                    │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Stream: ingest_jobs                                     │ │ │
│  │  │  {                                                       │ │ │
│  │  │    "job_id": "abc123",                                  │ │ │
│  │  │    "source_type": "web_crawl",                          │ │ │
│  │  │    "source_uri": "https://example.com",                 │ │ │
│  │  │    "status": "queued",                                  │ │ │
│  │  │    "timestamp": 1728567890                              │ │ │
│  │  │  }                                                       │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────┬──────────────────────────────────────────────────┘ │
│               │                                                     │
│  ┌────────────▼──────────────────────────────────────────────────┐ │
│  │  Worker Pool (Async Workers)                                  │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker 4 │     │ │
│  │  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘     │ │
│  │        │             │             │             │           │ │
│  │        └─────────────┴─────────────┴─────────────┘           │ │
│  │                      │                                        │ │
│  │  1. Read from stream (consumer group)                        │ │
│  │  2. Process job (crawl, ingest, store)                       │ │
│  │  3. Update job status in Redis                               │ │
│  │  4. Publish events to SSE                                    │ │
│  │  5. ACK message                                               │ │
│  └────────────┬──────────────────────────────────────────────────┘ │
└─────────────────┼────────────────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │  Redis         │  │  Qdrant        │  │  PostgreSQL    │        │
│  │  (Job State)   │  │  (Vectors)     │  │  (Metadata)    │        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Job Creation**
   ```python
   job_id = str(uuid.uuid4())
   job_data = {
       "job_id": job_id,
       "source_type": "web_crawl",
       "source_uri": url,
       "status": "queued",
       "created_at": datetime.utcnow().isoformat()
   }
   await redis.xadd("ingest_jobs", job_data)
   return {"job_id": job_id, "status": "queued"}
   ```

2. **Job Processing**
   ```python
   # Worker picks up job
   messages = await redis.xreadgroup("workers", "worker-1", {"ingest_jobs": ">"})
   for stream, message_list in messages:
       for message_id, job_data in message_list:
           # Update status
           await redis.hset(f"job:{job_id}", "status", "processing")
           
           # Do work
           result = await process_job(job_data)
           
           # Update result
           await redis.hset(f"job:{job_id}", "status", "completed")
           await redis.hset(f"job:{job_id}", "result", json.dumps(result))
           
           # ACK message
           await redis.xack("ingest_jobs", "workers", message_id)
   ```

3. **Job Status Query**
   ```python
   status = await redis.hget(f"job:{job_id}", "status")
   result = await redis.hget(f"job:{job_id}", "result")
   return {
       "job_id": job_id,
       "status": status,
       "result": json.loads(result) if result else None
   }
   ```

---

## 🛠️ IMPLEMENTATION GUIDE

### Step 1: Update MCP Server Tools

**File**: `roles/fastmcp_server/templates/shield_mcp_server.py.j2`

```python
import httpx
import uuid
from typing import Dict, Any

# Orchestrator URL
ORCHESTRATOR_URL = "http://{{ orchestrator_host }}:{{ orchestrator_port }}"

# HTTP client
http_client = httpx.AsyncClient(timeout=30.0)

@mcp.tool()
async def crawl_web(
    url: str,
    allow_domains: List[str] = None,
    max_pages: int = 10
) -> Dict[str, Any]:
    """
    Crawl a website asynchronously.
    
    Returns immediately with job_id for tracking.
    Use get_job_status() to check progress.
    
    Args:
        url: Starting URL to crawl
        allow_domains: List of allowed domains (optional)
        max_pages: Maximum pages to crawl (default: 10)
    
    Returns:
        {
            "status": "queued",
            "job_id": "abc123-def456-...",
            "message": "Crawling queued for processing",
            "track_url": "/jobs/abc123-def456-..."
        }
    """
    try:
        # Call orchestrator async endpoint
        response = await http_client.post(
            f"{ORCHESTRATOR_URL}/ingest-async",
            json={
                "source_type": "web_crawl",
                "source_uri": url,
                "metadata": {
                    "allow_domains": allow_domains or [],
                    "max_pages": max_pages
                }
            }
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Return HTTP 202 equivalent (job queued)
        return {
            "status": "queued",
            "job_id": result["job_id"],
            "message": f"Crawling {url} queued for processing",
            "track_url": f"/jobs/{result['job_id']}",
            "estimated_time": "2-5 minutes"
        }
        
    except Exception as e:
        logger.error(f"Failed to queue crawl job: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "queue_failed",
            "message": str(e)
        }


@mcp.tool()
async def ingest_doc(
    doc_uri: str,
    doc_type: str = "auto"
) -> Dict[str, Any]:
    """
    Ingest a document asynchronously.
    
    Returns immediately with job_id for tracking.
    Use get_job_status() to check progress.
    
    Args:
        doc_uri: URI of document (file path or URL)
        doc_type: Document type (pdf, docx, txt, auto)
    
    Returns:
        {
            "status": "queued",
            "job_id": "...",
            "message": "Document ingestion queued"
        }
    """
    try:
        response = await http_client.post(
            f"{ORCHESTRATOR_URL}/ingest-async",
            json={
                "source_type": "document",
                "source_uri": doc_uri,
                "metadata": {
                    "doc_type": doc_type
                }
            }
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "status": "queued",
            "job_id": result["job_id"],
            "message": f"Document ingestion queued: {doc_uri}",
            "track_url": f"/jobs/{result['job_id']}",
            "estimated_time": "1-3 minutes"
        }
        
    except Exception as e:
        logger.error(f"Failed to queue ingest job: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "queue_failed",
            "message": str(e)
        }


@mcp.tool()
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of an async job.
    
    Args:
        job_id: Job identifier from crawl_web or ingest_doc
    
    Returns:
        {
            "job_id": "...",
            "status": "queued|processing|completed|failed",
            "progress": 0-100,
            "result": {...} (if completed),
            "error": "..." (if failed)
        }
    """
    try:
        response = await http_client.get(
            f"{ORCHESTRATOR_URL}/jobs/{job_id}"
        )
        response.raise_for_status()
        
        return response.json()
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "status": "error",
                "error": "not_found",
                "message": f"Job {job_id} not found"
            }
        raise
        
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
        return {
            "status": "error",
            "error": "query_failed",
            "message": str(e)
        }
```

### Step 2: Orchestrator Async Endpoint (Already Exists)

The orchestrator already has `/ingest-async` endpoint. Verify it returns the correct format:

**Expected Response**:
```json
{
    "job_id": "abc123-def456-789",
    "status": "queued",
    "message": "Job queued for processing",
    "created_at": "2025-10-10T12:00:00Z"
}
```

### Step 3: Job Status Endpoint (Already Exists)

The orchestrator already has `/jobs/{job_id}` endpoint. Verify it returns:

**Response Format**:
```json
{
    "job_id": "abc123-def456-789",
    "status": "processing",
    "progress": 45,
    "created_at": "2025-10-10T12:00:00Z",
    "started_at": "2025-10-10T12:00:05Z",
    "updated_at": "2025-10-10T12:01:30Z",
    "metadata": {
        "source_type": "web_crawl",
        "source_uri": "https://example.com"
    },
    "events": [
        {"timestamp": "2025-10-10T12:00:05Z", "event": "crawl_started"},
        {"timestamp": "2025-10-10T12:01:00Z", "event": "crawl_completed"},
        {"timestamp": "2025-10-10T12:01:30Z", "event": "processing"}
    ]
}
```

### Step 4: Testing

```bash
# Test async crawl
curl -X POST http://localhost:8000/mcp/crawl_web \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_pages": 5}'

# Response:
# {
#   "status": "queued",
#   "job_id": "abc123-def456-789",
#   "message": "Crawling queued",
#   "track_url": "/jobs/abc123-def456-789"
# }

# Check job status
curl http://localhost:8001/jobs/abc123-def456-789

# Response (while processing):
# {
#   "job_id": "abc123-def456-789",
#   "status": "processing",
#   "progress": 45
# }

# Response (completed):
# {
#   "job_id": "abc123-def456-789",
#   "status": "completed",
#   "progress": 100,
#   "result": {
#     "pages_crawled": 5,
#     "chunks_created": 127,
#     "vectors_stored": 127
#   }
# }
```

---

## 💻 CLIENT INTEGRATION

### Option 1: Polling (Simple)

```python
import asyncio
import httpx

async def crawl_and_wait(url: str) -> dict:
    """Crawl a website and wait for completion."""
    
    client = httpx.AsyncClient()
    
    # 1. Start the crawl
    response = await client.post(
        "http://mcp-server:8000/mcp/crawl_web",
        json={"url": url}
    )
    job_info = response.json()
    job_id = job_info["job_id"]
    
    print(f"Job queued: {job_id}")
    
    # 2. Poll for completion
    while True:
        response = await client.get(
            f"http://orchestrator:8001/jobs/{job_id}"
        )
        status = response.json()
        
        print(f"Status: {status['status']} - Progress: {status.get('progress', 0)}%")
        
        if status["status"] == "completed":
            return status["result"]
        elif status["status"] == "failed":
            raise Exception(f"Job failed: {status.get('error')}")
        
        # Wait before next poll
        await asyncio.sleep(2)

# Usage
result = await crawl_and_wait("https://example.com")
print(f"Crawl complete: {result}")
```

### Option 2: SSE Events (Real-time)

```python
import httpx_sse

async def crawl_with_events(url: str):
    """Crawl with real-time event updates."""
    
    client = httpx.AsyncClient()
    
    # 1. Start the crawl
    response = await client.post(
        "http://mcp-server:8000/mcp/crawl_web",
        json={"url": url}
    )
    job_info = response.json()
    job_id = job_info["job_id"]
    
    print(f"Job queued: {job_id}")
    
    # 2. Subscribe to events
    async with httpx_sse.aconnect_sse(
        client,
        "GET",
        f"http://orchestrator:8001/jobs/{job_id}/events"
    ) as event_source:
        async for event in event_source.aiter_sse():
            data = json.loads(event.data)
            
            print(f"Event: {data['event']} - {data.get('message', '')}")
            
            if data["event"] == "completed":
                return data["result"]
            elif data["event"] == "failed":
                raise Exception(f"Job failed: {data['error']}")

# Usage
result = await crawl_with_events("https://example.com")
print(f"Crawl complete: {result}")
```

### Option 3: LiteLLM Integration

```yaml
# litellm_config.yaml

# MCP tools return job_id
# Client must poll or subscribe
model_list:
  - model_name: shield-mcp
    litellm_params:
      model: anthropic/claude-3-5-sonnet
      tools:
        - name: crawl_web
          description: "Crawl website (returns job_id, use get_job_status to check)"
        - name: get_job_status
          description: "Check status of async job"

# LiteLLM will automatically:
# 1. Call crawl_web (gets job_id)
# 2. Call get_job_status(job_id) in loop
# 3. Return final result to LLM
```

### Option 4: CopilotKit Integration

```typescript
// CopilotKit client with polling
import { useCopilotAction } from "@copilotkit/react-core";

useCopilotAction({
  name: "crawl_web",
  description: "Crawl a website",
  parameters: [
    { name: "url", type: "string", description: "URL to crawl" }
  ],
  handler: async ({ url }) => {
    // 1. Start crawl
    const response = await fetch("/mcp/crawl_web", {
      method: "POST",
      body: JSON.stringify({ url })
    });
    const { job_id } = await response.json();
    
    // 2. Poll for completion
    while (true) {
      const statusResponse = await fetch(`/jobs/${job_id}`);
      const status = await statusResponse.json();
      
      // Update UI with progress
      updateProgress(status.progress);
      
      if (status.status === "completed") {
        return status.result;
      } else if (status.status === "failed") {
        throw new Error(status.error);
      }
      
      await sleep(2000); // Poll every 2 seconds
    }
  }
});
```

---

## ✅ BEST PRACTICES

### 1. Job ID Generation

```python
import uuid
from datetime import datetime

def generate_job_id(source_type: str) -> str:
    """Generate unique, sortable job ID."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{source_type}_{timestamp}_{unique_id}"

# Example: "web_crawl_20251010120000_abc12345"
```

### 2. Job State Management

```python
# Use Redis hashes for job state
job_key = f"job:{job_id}"

# Store complete job state
await redis.hset(job_key, mapping={
    "job_id": job_id,
    "status": "queued",  # queued, processing, completed, failed
    "progress": 0,
    "created_at": datetime.utcnow().isoformat(),
    "source_type": "web_crawl",
    "source_uri": url
})

# Set expiration (clean up old jobs)
await redis.expire(job_key, 86400)  # 24 hours
```

### 3. Progress Tracking

```python
# Update progress during processing
async def process_crawl_job(job_id: str, url: str):
    total_pages = 10
    
    for i, page in enumerate(crawl_pages(url, total_pages)):
        # Process page
        await process_page(page)
        
        # Update progress
        progress = int((i + 1) / total_pages * 100)
        await redis.hset(f"job:{job_id}", "progress", progress)
        
        # Publish event
        await redis.publish(f"job:{job_id}:events", json.dumps({
            "event": "page_processed",
            "progress": progress,
            "page_url": page.url
        }))
```

### 4. Error Handling

```python
try:
    result = await process_job(job_data)
    
    # Success
    await redis.hset(f"job:{job_id}", mapping={
        "status": "completed",
        "progress": 100,
        "result": json.dumps(result),
        "completed_at": datetime.utcnow().isoformat()
    })
    
except Exception as e:
    # Failure
    await redis.hset(f"job:{job_id}", mapping={
        "status": "failed",
        "error": str(e),
        "error_type": type(e).__name__,
        "failed_at": datetime.utcnow().isoformat()
    })
    
    logger.error(f"Job {job_id} failed: {e}", exc_info=True)
```

### 5. Idempotency

```python
# Client provides idempotency key
@app.post("/ingest-async")
async def ingest_async(
    data: dict,
    idempotency_key: str = Header(None)
):
    # Use idempotency key as job_id
    job_id = idempotency_key or str(uuid.uuid4())
    
    # Check if job already exists
    existing = await redis.exists(f"job:{job_id}")
    if existing:
        # Return existing job
        job_data = await redis.hgetall(f"job:{job_id}")
        return {"job_id": job_id, "status": job_data["status"]}
    
    # Create new job
    await create_job(job_id, data)
    return {"job_id": job_id, "status": "queued"}
```

### 6. Timeout Handling

```python
# Set job timeout
JOB_TIMEOUT = 600  # 10 minutes

# In worker
async def process_with_timeout(job_id: str, job_data: dict):
    try:
        result = await asyncio.wait_for(
            process_job(job_data),
            timeout=JOB_TIMEOUT
        )
        return result
        
    except asyncio.TimeoutError:
        await redis.hset(f"job:{job_id}", mapping={
            "status": "failed",
            "error": "timeout",
            "message": f"Job exceeded {JOB_TIMEOUT}s timeout"
        })
        raise
```

---

## 🔧 TROUBLESHOOTING

### Problem: Job stays in "queued" forever

**Causes**:
- No workers running
- Workers crashed
- Redis connection lost

**Solutions**:
```bash
# Check worker status
curl http://orchestrator:8001/health/workers

# Check Redis connection
redis-cli -h redis-server ping

# Restart workers
ansible-playbook -i inventory/prod.ini site.yml --tags orchestrator-workers

# Check worker logs
journalctl -u shield-orchestrator-workers -f
```

### Problem: Job status endpoint returns 404

**Causes**:
- Job expired (TTL elapsed)
- Wrong job_id
- Redis lost data

**Solutions**:
```bash
# Check if job exists in Redis
redis-cli -h redis-server EXISTS job:abc123-def456-789

# Check Redis memory
redis-cli -h redis-server INFO memory

# Increase job TTL
# In orchestrator config:
JOB_RETENTION_SECONDS=172800  # 48 hours
```

### Problem: Progress never updates

**Causes**:
- Worker not updating progress
- Redis connection issues
- Worker processing but not reporting

**Solutions**:
```python
# Add progress logging
logger.info(f"Job {job_id} progress: {progress}%")

# Verify Redis updates
await redis.hset(f"job:{job_id}", "progress", progress)
current = await redis.hget(f"job:{job_id}", "progress")
assert int(current) == progress

# Check worker health
curl http://orchestrator:8001/health/workers
```

### Problem: SSE events not streaming

**Causes**:
- Nginx buffering
- Client timeout
- No events being published

**Solutions**:
```nginx
# Disable buffering for SSE
location /jobs/ {
    proxy_pass http://orchestrator;
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding on;
}
```

```python
# Verify event publishing
await redis.publish(f"job:{job_id}:events", json.dumps(event_data))

# Check subscribers
subscribers = await redis.pubsub_numsub(f"job:{job_id}:events")
logger.info(f"Event channel has {subscribers} subscribers")
```

---

## 📊 MONITORING

### Metrics to Track

```python
from prometheus_client import Counter, Histogram, Gauge

# Job metrics
jobs_created = Counter('jobs_created_total', 'Total jobs created', ['source_type'])
jobs_completed = Counter('jobs_completed_total', 'Total jobs completed', ['source_type', 'status'])
job_duration = Histogram('job_duration_seconds', 'Job processing duration', ['source_type'])
active_jobs = Gauge('active_jobs', 'Currently active jobs', ['status'])

# In job creation
jobs_created.labels(source_type='web_crawl').inc()
active_jobs.labels(status='queued').inc()

# In job completion
duration = time.time() - start_time
job_duration.labels(source_type='web_crawl').observe(duration)
jobs_completed.labels(source_type='web_crawl', status='completed').inc()
active_jobs.labels(status='queued').dec()
active_jobs.labels(status='completed').inc()
```

### Alerts

```yaml
# prometheus_alerts.yml
groups:
  - name: async_jobs
    rules:
      - alert: JobsStuckInQueue
        expr: active_jobs{status="queued"} > 100
        for: 5m
        annotations:
          summary: "Too many jobs stuck in queue"
          
      - alert: JobFailureRateHigh
        expr: rate(jobs_completed_total{status="failed"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Job failure rate > 10%"
          
      - alert: JobProcessingTimeHigh
        expr: job_duration_seconds{quantile="0.95"} > 300
        for: 10m
        annotations:
          summary: "P95 job duration > 5 minutes"
```

---

## 📚 REFERENCES

### HTTP Status Codes

- **202 Accepted**: Request accepted, processing async
- **200 OK**: Synchronous success (not used for async)
- **303 See Other**: Redirect to job status URL (alternative)

### Standards

- [RFC 7231 - HTTP/1.1 Semantics (202)](https://tools.ietf.org/html/rfc7231#section-6.3.3)
- [REST API Best Practices - Async Operations](https://restfulapi.net/http-status-202-accepted/)

### Related Patterns

- **Webhook Pattern**: Server calls client when job completes
- **WebSocket Pattern**: Bidirectional real-time communication
- **Polling Pattern**: Client periodically checks status (simpler)
- **SSE Pattern**: Server pushes events to client (one-way)

---

**Document Status**: ✅ **READY FOR IMPLEMENTATION**  
**Last Updated**: October 10, 2025  
**Next Review**: After Phase 1 completion

