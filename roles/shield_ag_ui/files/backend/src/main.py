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

logger = structlog.get_logger()

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
    
    redis_consumer = RedisStreamConsumer(
        redis_url=settings.REDIS_URL,
        stream_name=settings.REDIS_STREAM_NAME,
        consumer_group=settings.REDIS_CONSUMER_GROUP,
        consumer_name=settings.REDIS_CONSUMER_NAME
    )
    await redis_consumer.start()
    
    app.state.redis_consumer = redis_consumer
    
    logger.info("redis_consumer_started", consumer_name=settings.REDIS_CONSUMER_NAME)
    
    yield
    
    if redis_consumer:
        await redis_consumer.stop()
        logger.info("redis_consumer_stopped")


app = FastAPI(
    title="Shield AG-UI Backend",
    description="AG-UI Protocol adapter for HX-Citadel Shield RAG pipeline",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
