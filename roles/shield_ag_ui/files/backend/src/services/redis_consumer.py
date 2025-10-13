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
                messages = await self.client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_name: from_id},
                    count=count,
                    block=block_ms
                )
                
                if not messages:
                    continue
                    
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        yield {
                            "id": message_id,
                            "stream": stream_name,
                            "data": message_data
                        }
                        
                        await self.client.xack(
                            self.stream_name,
                            self.consumer_group,
                            message_id
                        )
                        
            except redis.RedisError as e:
                logger.error("redis_read_error", error=str(e))
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info("redis_consumer_cancelled")
                break
