# Task T002: Create FastAPI Backend Application

**Feature**: Shield AG-UI Backend  
**Phase**: 3.3 Core Implementation  
**Parallel**: [P] (can run parallel with T003 frontend)  
**Estimated Effort**: 4 hours  
**Prerequisites**: T001 (Ansible role structure)

## Task Description

Create the complete FastAPI backend application with AG-UI Python SDK integration, Redis Streams consumer, SSE endpoint, and tool execution proxy to LiteLLM.

## Execution Flow

```
1. Create backend directory structure
   → roles/ag_ui_deployment/files/backend/
   → src/, tests/, requirements.txt, Dockerfile
2. Implement FastAPI application
   → main.py (application entry)
   → routers/ (API endpoints)
   → services/ (business logic)
   → models/ (data models)
3. Integrate AG-UI Python SDK
   → Event handling
   → SSE streaming
4. Implement Redis Streams consumer
   → Connect to shield:events stream
   → Transform events to AG-UI protocol
5. Create Dockerfile (multi-stage build)
6. Write requirements.txt
7. Verify structure matches architecture
```

## Files to Create

### 1. Directory Structure
```
roles/ag_ui_deployment/files/backend/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── api.py
│   │   ├── admin.py
│   │   └── events.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── rbac_service.py
│   │   ├── event_service.py
│   │   ├── redis_consumer.py
│   │   ├── litellm_client.py
│   │   └── audit_logger.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── job.py
│   │   ├── event.py
│   │   └── permissions.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── database.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_auth_service.py
│   │   ├── test_event_service.py
│   │   └── test_redis_consumer.py
│   └── integration/
│       ├── test_api_endpoints.py
│       └── test_sse_stream.py
├── requirements.txt
├── Dockerfile
└── README.md
```

### 2. src/main.py

```python
#!/usr/bin/env python3
"""
Shield AG-UI Backend - FastAPI Application
AG-UI Protocol adapter for HX-Citadel Shield
"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
import os

from src.routers import auth, api, admin, events
from src.services.redis_consumer import RedisStreamConsumer
from src.config import settings

# Structured logging
logger = structlog.get_logger()

# Global consumer instance
redis_consumer: RedisStreamConsumer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - startup and shutdown"""
    global redis_consumer
    
    logger.info(
        "ag_ui_backend_starting",
        redis_url=settings.REDIS_URL,
        litellm_url=settings.LITELLM_URL,
        orchestrator_url=settings.ORCHESTRATOR_URL
    )
    
    # Startup: Initialize Redis consumer
    redis_consumer = RedisStreamConsumer(
        redis_url=settings.REDIS_URL,
        stream_name=settings.REDIS_STREAM_NAME,
        consumer_group=settings.REDIS_CONSUMER_GROUP,
        consumer_name=settings.REDIS_CONSUMER_NAME
    )
    await redis_consumer.start()
    
    # Store consumer in app state to avoid circular imports
    app.state.redis_consumer = redis_consumer
    
    logger.info("redis_consumer_started", consumer_name=settings.REDIS_CONSUMER_NAME)
    
    yield
    
    # Shutdown: Cleanup
    if redis_consumer:
        await redis_consumer.stop()
        logger.info("redis_consumer_stopped")


# FastAPI application
app = FastAPI(
    title="Shield AG-UI Backend",
    description="AG-UI Protocol adapter for HX-Citadel Shield RAG pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(events.router, prefix="", tags=["events"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "shield-ag-ui-backend",
        "version": "1.0.0",
        "redis_connected": redis_consumer.is_connected() if redis_consumer else False
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Shield AG-UI Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8002")),
        reload=os.getenv("ENV", "production") == "development",
        log_level="info"
    )
```

### 3. src/config.py

```python
"""Configuration management using environment variables"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "shield-ag-ui-backend"
    ENV: str = "production"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3001", "http://localhost:80"]
    
    # External Services
    LITELLM_URL: str = "http://hx-litellm-server:4000"
    ORCHESTRATOR_URL: str = "http://hx-orchestrator-server:8000"
    REDIS_URL: str = "redis://hx-sqldb-server:6379"
    QDRANT_URL: str = "http://hx-vectordb-server:6333"
    
    # Redis Streams
    REDIS_STREAM_NAME: str = "shield:events"
    REDIS_CONSUMER_GROUP: str = "ag-ui-clients"
    REDIS_CONSUMER_NAME: str = "hx-dev-server"
    
    # Authentication
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql://shield:shield@hx-sqldb-server:5432/shield"
    
    # LiteLLM API Key
    LITELLM_API_KEY: str = "sk-shield-lob-default"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### 4. src/routers/events.py

```python
"""SSE event streaming endpoint"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import structlog
import asyncio

from src.services.event_service import EventService

router = APIRouter()
logger = structlog.get_logger()


@router.get("/events")
async def event_stream(request: Request):
    """
    Server-Sent Events (SSE) endpoint for real-time event streaming.
    
    Streams AG-UI protocol events transformed from Redis Streams.
    Client should handle reconnection with Last-Event-ID header.
    """
    logger.info("sse_connection_opened", client=request.client.host)
    
    async def event_generator():
        """Generate SSE events from Redis Streams"""
        # Get consumer from app state to avoid circular imports
        redis_consumer = request.app.state.redis_consumer
        event_service = EventService(redis_consumer)
        last_id = request.headers.get("Last-Event-ID", "0-0")
        
        try:
            async for ag_ui_event in event_service.stream_events(last_id):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("sse_client_disconnected", client=request.client.host)
                    break
                
                # Yield AG-UI protocol event as SSE
                yield {
                    "id": ag_ui_event.get("event_id", "0-0"),
                    "event": ag_ui_event.get("type", "message"),
                    "data": ag_ui_event
                }
                
                # Small delay to prevent overwhelming client
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            logger.info("sse_stream_cancelled", client=request.client.host)
        except Exception as e:
            logger.error("sse_stream_error", error=str(e), exc_info=True)
        finally:
            logger.info("sse_connection_closed", client=request.client.host)
    
    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive"
        }
    )
```

### 5. src/services/redis_consumer.py

```python
"""Redis Streams consumer for Shield events"""
import redis.asyncio as redis
import structlog
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional

logger = structlog.get_logger()


class RedisStreamConsumer:
    """
    Async Redis Streams consumer for shield:events stream.
    Uses consumer groups for reliable, at-least-once delivery.
    """
    
    def __init__(
        self,
        redis_url: str,
        stream_name: str,
        consumer_group: str,
        consumer_name: str
    ):
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.client: Optional[redis.Redis] = None
        self._running = False
        
    async def start(self):
        """Initialize Redis connection and create consumer group"""
        self.client = redis.from_url(
            self.redis_url,
            decode_responses=True,
            encoding="utf-8"
        )
        
        try:
            # Create consumer group (ignore if exists)
            await self.client.xgroup_create(
                name=self.stream_name,
                groupname=self.consumer_group,
                id="0",
                mkstream=True
            )
            logger.info(
                "redis_consumer_group_created",
                stream=self.stream_name,
                group=self.consumer_group
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            logger.info(
                "redis_consumer_group_exists",
                stream=self.stream_name,
                group=self.consumer_group
            )
        
        self._running = True
        
    async def stop(self):
        """Close Redis connection"""
        self._running = False
        if self.client:
            await self.client.close()
            
    def is_connected(self) -> bool:
        """Check if Redis client is connected"""
        return self.client is not None and self._running
        
    async def read_events(
        self,
        count: int = 10,
        block_ms: int = 5000,
        from_id: str = ">"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Read events from Redis Stream using XREADGROUP.
        
        Args:
            count: Max messages to read per call
            block_ms: Milliseconds to block waiting for new messages
            from_id: Starting message ID (> for new, 0-0 for pending)
            
        Yields:
            Dict with message id and data
        """
        if not self.client:
            raise RuntimeError("Redis consumer not started")
            
        while self._running:
            try:
                # XREADGROUP: Read from consumer group
                messages = await self.client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_name: from_id},
                    count=count,
                    block=block_ms
                )
                
                if not messages:
                    continue
                    
                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        yield {
                            "id": message_id,
                            "stream": stream_name,
                            "data": message_data
                        }
                        
                        # Acknowledge message
                        await self.client.xack(
                            self.stream_name,
                            self.consumer_group,
                            message_id
                        )
                        
            except redis.RedisError as e:
                logger.error("redis_read_error", error=str(e))
                await asyncio.sleep(5)  # Wait before retry
            except asyncio.CancelledError:
                logger.info("redis_consumer_cancelled")
                break
```

### 6. requirements.txt

```txt
# Web framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# AG-UI SDK
ag-ui-python-sdk>=0.1.0

# Redis
redis[hiredis]==5.0.1

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# HTTP client
httpx==0.26.0

# SSE
sse-starlette==1.8.2

# Logging
structlog==24.1.0

# Configuration
pydantic-settings==2.1.0

# Utilities
python-dotenv==1.0.0
```

### 7. Dockerfile

```dockerfile
# Multi-stage build for Shield AG-UI Backend
FROM python:3.12-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 1: Dependencies
FROM base as dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM base as runtime

# Copy installed packages from dependencies stage
COPY --from=dependencies /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ /app/src/

# Create non-root user
RUN useradd -m -u 1001 agui && chown -R agui:agui /app
USER agui

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8002/health').raise_for_status()"

# Expose port
EXPOSE 8002

# Run application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

## Acceptance Criteria

- [x] Complete directory structure created
- [x] FastAPI application with lifespan management
- [x] AG-UI Python SDK integrated
- [x] Redis Streams consumer implemented
- [x] SSE endpoint for real-time events
- [x] Configuration management with Pydantic
- [x] Structured logging with structlog
- [x] Multi-stage Dockerfile (optimized)
- [x] Non-root user in container
- [x] Health check endpoint
- [x] requirements.txt with all dependencies
- [x] Tests structure created (to be implemented)

## Testing

```bash
# Build Docker image
cd roles/ag_ui_deployment/files/backend/
docker build -t shield-ag-ui-backend:test .

# Run locally
python -m uvicorn src.main:app --reload --port 8002

# Test health endpoint
curl http://localhost:8002/health

# Test SSE stream
curl -N http://localhost:8002/events

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v
```

## Next Tasks

- T003: Integrate Existing Vite Frontend [P]
- T008: Implement Authentication Service
- T009: Implement RBAC Service
- T010: Implement Event Transformation Service

## Notes

- Uses AG-UI Python SDK for protocol compliance
- Redis Streams with consumer groups for reliability
- SSE for real-time event streaming (browser-native)
- Multi-stage Docker build for optimized image size
- Structured logging for better observability
- Non-root user for container security
- Health check for monitoring

## Related Documents

- [Architecture - Backend Architecture](../SHIELD-AG-UI-ARCHITECTURE.md#32-backend-architecture-ag-ui-backend)
- [Implementation Plan - Backend Phase](../DEV-SERVER-AG-UI-IMPLEMENTATION-PLAN.md#phase-2-backend-development)

