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
        redis_consumer = request.app.state.redis_consumer
        event_service = EventService(redis_consumer)
        last_id = request.headers.get("Last-Event-ID", "0-0")
        
        try:
            async for ag_ui_event in event_service.stream_events(last_id):
                if await request.is_disconnected():
                    logger.info("sse_client_disconnected", client=request.client.host)
                    break
                
                yield {
                    "id": ag_ui_event.get("event_id", "0-0"),
                    "event": ag_ui_event.get("type", "message"),
                    "data": ag_ui_event
                }
                
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
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )
