"""Redis-based session storage for conversation context"""
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisSessionStorage:
    """Manages conversation session storage in Redis"""
    
    def __init__(self, redis_url: str, ttl_hours: int = 24, max_conversations: int = 50):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_hours * 3600
        self.max_conversations = max_conversations
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await self.client.ping()
        logger.info(f"Connected to Redis at {self.redis_url}")
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"session:{session_id}"
    
    async def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Retrieve conversation history for a session"""
        key = self._session_key(session_id)
        
        # Get all conversation entries
        conversations = await self.client.lrange(key, 0, -1)
        
        if not conversations:
            return []
        
        # Parse JSON entries
        history = []
        for conv_json in conversations:
            try:
                history.append(json.loads(conv_json))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse conversation entry: {e}")
                continue
        
        return history
    
    async def append_conversation(
        self, 
        session_id: str, 
        query: str, 
        response: str, 
        metadata: Dict
    ) -> None:
        """Append a Q&A pair to session history"""
        key = self._session_key(session_id)
        
        # Create conversation entry
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata
        }
        
        # Add to list
        await self.client.rpush(key, json.dumps(entry))
        
        # Trim to max conversations
        await self.client.ltrim(key, -self.max_conversations, -1)
        
        # Set/refresh TTL
        await self.client.expire(key, self.ttl_seconds)
        
        logger.debug(f"Appended conversation to session {session_id}")
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        key = self._session_key(session_id)
        result = await self.client.delete(key)
        return result > 0
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        key = self._session_key(session_id)
        return await self.client.exists(key) > 0

