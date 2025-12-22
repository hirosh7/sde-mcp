"""Redis client for session context storage"""
import redis.asyncio as redis
import json
from typing import Optional, Dict, List
from datetime import datetime, timezone

class RedisSessionStorage:
    """Store and retrieve session context from Redis"""
    
    def __init__(self, host: str, port: int, db: int = 0, session_ttl: int = 86400):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.session_ttl = session_ttl  # Default 24 hours
    
    async def get_session_context(self, session_id: str) -> Optional[Dict]:
        """Retrieve session context from Redis"""
        key = f"session:{session_id}"
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def save_session_context(self, session_id: str, context: Dict) -> None:
        """Save session context to Redis with TTL"""
        key = f"session:{session_id}"
        data = json.dumps(context, default=str)
        await self.client.setex(key, self.session_ttl, data)
    
    async def append_conversation(
        self, 
        session_id: str, 
        query: str, 
        response: str, 
        metadata: Dict
    ) -> None:
        """Append Q&A pair to session conversation history"""
        context = await self.get_session_context(session_id) or {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "conversations": []
        }
        
        context["conversations"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata
        })
        
        # Keep last 50 conversations per session
        if len(context["conversations"]) > 50:
            context["conversations"] = context["conversations"][-50:]
        
        context["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.save_session_context(session_id, context)
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session from Redis"""
        key = f"session:{session_id}"
        await self.client.delete(key)
    
    async def close(self) -> None:
        """Close Redis connection"""
        await self.client.aclose()
