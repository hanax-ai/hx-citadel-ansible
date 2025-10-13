"""Event transformation service - Redis to AG-UI protocol"""
import structlog
from typing import AsyncGenerator, Dict, Any

logger = structlog.get_logger()


class EventService:
    """Transform Redis Stream events to AG-UI protocol events"""
    
    def __init__(self, redis_consumer):
        self.redis_consumer = redis_consumer
        
    async def stream_events(self, last_id: str = "0-0") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream events from Redis and transform to AG-UI protocol.
        
        Args:
            last_id: Last event ID received by client
            
        Yields:
            AG-UI protocol formatted events
        """
        from_id = ">" if last_id == "0-0" else last_id
        
        async for redis_event in self.redis_consumer.read_events(from_id=from_id):
            ag_ui_event = self._transform_to_ag_ui(redis_event)
            yield ag_ui_event
            
    def _transform_to_ag_ui(self, redis_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Redis Stream event to AG-UI protocol event.
        
        Maps Shield event types to AG-UI protocol event types:
        - job.started -> TextMessageContentEvent
        - tool.execution -> ToolCallEvent
        - result.ready -> TextMessageContentEvent
        """
        event_data = redis_event.get("data", {})
        event_type = event_data.get("type", "unknown")
        
        ag_ui_event = {
            "event_id": redis_event.get("id", "0-0"),
            "type": self._map_event_type(event_type),
            "timestamp": event_data.get("timestamp"),
            "data": event_data
        }
        
        return ag_ui_event
        
    def _map_event_type(self, shield_event_type: str) -> str:
        """Map Shield event types to AG-UI protocol types"""
        mapping = {
            "job.started": "text_message_content",
            "job.completed": "text_message_content",
            "tool.execution": "tool_call",
            "result.ready": "text_message_content",
            "error": "error"
        }
        return mapping.get(shield_event_type, "message")
