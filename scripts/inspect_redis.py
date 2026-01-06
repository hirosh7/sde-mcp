#!/usr/bin/env python3
"""Script to inspect Redis session data

Install dependencies:
    pip install -r scripts/requirements.txt
    # or
    pip install redis>=5.0.0
"""
import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import redis.asyncio as redis
except ImportError:
    print("Error: redis package not installed.")
    print("Install with: pip install -r scripts/requirements.txt")
    print("Or: pip install redis>=5.0.0")
    sys.exit(1)


async def inspect_redis(redis_url: str = "redis://localhost:6379"):
    """Inspect all session data in Redis"""
    client = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        # Get all session keys
        session_keys = await client.keys("session:*")
        
        if not session_keys:
            print("No sessions found in Redis.")
            return
        
        print(f"\nFound {len(session_keys)} session(s) in Redis:\n")
        print("=" * 80)
        
        for key in sorted(session_keys):
            session_id = key.replace("session:", "")
            
            # Get TTL
            ttl = await client.ttl(key)
            ttl_str = f"{ttl // 3600}h {(ttl % 3600) // 60}m {ttl % 60}s" if ttl > 0 else "expired"
            
            # Get conversation count
            conv_count = await client.llen(key)
            
            print(f"\nSession ID: {session_id}")
            print(f"TTL: {ttl_str}")
            print(f"Conversations: {conv_count}")
            print("-" * 80)
            
            # Get all conversations
            conversations = await client.lrange(key, 0, -1)
            
            for idx, conv_json in enumerate(conversations, 1):
                try:
                    conv = json.loads(conv_json)
                    timestamp = conv.get("timestamp", "unknown")
                    query = conv.get("query", "")
                    response = conv.get("response", "")[:100] + "..." if len(conv.get("response", "")) > 100 else conv.get("response", "")
                    tool_name = conv.get("metadata", {}).get("tool_name", "unknown")
                    
                    print(f"\n  Conversation {idx}:")
                    print(f"    Timestamp: {timestamp}")
                    print(f"    Tool: {tool_name}")
                    print(f"    Query: {query}")
                    print(f"    Response: {response}")
                    
                except json.JSONDecodeError as e:
                    print(f"  Conversation {idx}: [ERROR parsing JSON: {e}]")
                    print(f"    Raw data: {conv_json[:200]}...")
            
            print()
        
        print("=" * 80)
        
        # Summary
        print(f"\nSummary:")
        print(f"  Total sessions: {len(session_keys)}")
        total_convs = sum(await client.llen(key) for key in session_keys)
        print(f"  Total conversations: {total_convs}")
        
    finally:
        await client.close()


async def get_session(redis_url: str, session_id: str):
    """Get details for a specific session"""
    client = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        key = f"session:{session_id}"
        
        if not await client.exists(key):
            print(f"Session {session_id} not found in Redis.")
            return
        
        # Get TTL
        ttl = await client.ttl(key)
        ttl_str = f"{ttl // 3600}h {(ttl % 3600) // 60}m {ttl % 60}s" if ttl > 0 else "expired"
        
        # Get conversation count
        conv_count = await client.llen(key)
        
        print(f"\nSession ID: {session_id}")
        print(f"TTL: {ttl_str}")
        print(f"Conversations: {conv_count}")
        print("=" * 80)
        
        # Get all conversations
        conversations = await client.lrange(key, 0, -1)
        
        for idx, conv_json in enumerate(conversations, 1):
            try:
                conv = json.loads(conv_json)
                timestamp = conv.get("timestamp", "unknown")
                query = conv.get("query", "")
                response = conv.get("response", "")
                tool_name = conv.get("metadata", {}).get("tool_name", "unknown")
                success = conv.get("metadata", {}).get("success", False)
                
                print(f"\nConversation {idx}:")
                print(f"  Timestamp: {timestamp}")
                print(f"  Tool: {tool_name}")
                print(f"  Success: {success}")
                print(f"  Query: {query}")
                print(f"  Response:\n{response}")
                print("-" * 80)
                
            except json.JSONDecodeError as e:
                print(f"Conversation {idx}: [ERROR parsing JSON: {e}]")
                print(f"Raw data: {conv_json}")
        
    finally:
        await client.close()


async def delete_session(redis_url: str, session_id: str):
    """Delete a specific session"""
    client = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        key = f"session:{session_id}"
        
        if not await client.exists(key):
            print(f"Session {session_id} not found in Redis.")
            return
        
        await client.delete(key)
        print(f"Deleted session {session_id}")
        
    finally:
        await client.close()


async def clear_all_sessions(redis_url: str):
    """Clear all sessions (use with caution!)"""
    client = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        session_keys = await client.keys("session:*")
        
        if not session_keys:
            print("No sessions to delete.")
            return
        
        count = len(session_keys)
        for key in session_keys:
            await client.delete(key)
        
        print(f"Deleted {count} session(s)")
        
    finally:
        await client.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inspect Redis session data")
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379"),
        help="Redis connection URL (default: redis://localhost:6379)"
    )
    parser.add_argument(
        "--session-id",
        help="Get details for a specific session ID"
    )
    parser.add_argument(
        "--delete",
        help="Delete a specific session ID"
    )
    parser.add_argument(
        "--clear-all",
        action="store_true",
        help="Clear all sessions (use with caution!)"
    )
    
    args = parser.parse_args()
    
    if args.clear_all:
        confirm = input("Are you sure you want to delete ALL sessions? (yes/no): ")
        if confirm.lower() == "yes":
            asyncio.run(clear_all_sessions(args.redis_url))
        else:
            print("Cancelled.")
    elif args.delete:
        asyncio.run(delete_session(args.redis_url, args.delete))
    elif args.session_id:
        asyncio.run(get_session(args.redis_url, args.session_id))
    else:
        asyncio.run(inspect_redis(args.redis_url))


if __name__ == "__main__":
    main()

