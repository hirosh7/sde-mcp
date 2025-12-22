"""Tests for Redis session storage client"""
import pytest
import asyncio
from datetime import datetime, timezone
from app.redis_client import RedisSessionStorage

# Use a separate Redis DB for testing (e.g., DB 1)
TEST_REDIS_HOST = "localhost"
TEST_REDIS_PORT = 6379
TEST_REDIS_DB = 1
TEST_SESSION_TTL = 60  # 1 minute for testing

@pytest.fixture
async def redis_storage():
    """Create Redis storage instance for testing"""
    storage = RedisSessionStorage(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        db=TEST_REDIS_DB,
        session_ttl=TEST_SESSION_TTL
    )
    yield storage
    # Cleanup: close connection after tests
    await storage.close()

@pytest.fixture
async def cleanup_test_sessions(redis_storage):
    """Cleanup test sessions before and after each test"""
    # Cleanup before test
    yield
    # Cleanup after test - delete all test sessions
    # Note: In a real scenario, you might want to use a test prefix
    pass

@pytest.mark.asyncio
async def test_get_session_context_nonexistent(redis_storage):
    """Test retrieving non-existent session returns None"""
    result = await redis_storage.get_session_context("nonexistent-session")
    assert result is None

@pytest.mark.asyncio
async def test_save_and_get_session_context(redis_storage):
    """Test saving and retrieving session context"""
    session_id = "test-session-1"
    context = {
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "conversations": []
    }
    
    await redis_storage.save_session_context(session_id, context)
    retrieved = await redis_storage.get_session_context(session_id)
    
    assert retrieved is not None
    assert retrieved["session_id"] == session_id
    assert "created_at" in retrieved
    assert retrieved["conversations"] == []
    
    # Cleanup
    await redis_storage.delete_session(session_id)

@pytest.mark.asyncio
async def test_append_conversation_new_session(redis_storage):
    """Test appending conversation to a new session"""
    session_id = "test-session-2"
    query = "List all projects"
    response = "Found 2 projects"
    metadata = {"tool_name": "list_projects", "success": True}
    
    await redis_storage.append_conversation(session_id, query, response, metadata)
    context = await redis_storage.get_session_context(session_id)
    
    assert context is not None
    assert len(context["conversations"]) == 1
    assert context["conversations"][0]["query"] == query
    assert context["conversations"][0]["response"] == response
    assert context["conversations"][0]["metadata"] == metadata
    assert "timestamp" in context["conversations"][0]
    
    # Cleanup
    await redis_storage.delete_session(session_id)

@pytest.mark.asyncio
async def test_append_conversation_existing_session(redis_storage):
    """Test appending multiple conversations to existing session"""
    session_id = "test-session-3"
    
    # First conversation
    await redis_storage.append_conversation(
        session_id, 
        "Query 1", 
        "Response 1", 
        {"tool": "tool1"}
    )
    
    # Second conversation
    await redis_storage.append_conversation(
        session_id, 
        "Query 2", 
        "Response 2", 
        {"tool": "tool2"}
    )
    
    context = await redis_storage.get_session_context(session_id)
    
    assert context is not None
    assert len(context["conversations"]) == 2
    assert context["conversations"][0]["query"] == "Query 1"
    assert context["conversations"][1]["query"] == "Query 2"
    
    # Cleanup
    await redis_storage.delete_session(session_id)

@pytest.mark.asyncio
async def test_conversation_limit(redis_storage):
    """Test that conversations are limited to max (50)"""
    session_id = "test-session-4"
    
    # Add 55 conversations (should keep only last 50)
    for i in range(55):
        await redis_storage.append_conversation(
            session_id,
            f"Query {i}",
            f"Response {i}",
            {"index": i}
        )
    
    context = await redis_storage.get_session_context(session_id)
    
    assert context is not None
    assert len(context["conversations"]) == 50
    # Should keep the last 50 (indices 5-54)
    assert context["conversations"][0]["query"] == "Query 5"
    assert context["conversations"][-1]["query"] == "Query 54"
    
    # Cleanup
    await redis_storage.delete_session(session_id)

@pytest.mark.asyncio
async def test_session_isolation(redis_storage):
    """Test that different sessions don't interfere with each other"""
    session_id_1 = "test-session-5"
    session_id_2 = "test-session-6"
    
    await redis_storage.append_conversation(
        session_id_1, 
        "Session 1 Query", 
        "Session 1 Response", 
        {}
    )
    
    await redis_storage.append_conversation(
        session_id_2, 
        "Session 2 Query", 
        "Session 2 Response", 
        {}
    )
    
    context_1 = await redis_storage.get_session_context(session_id_1)
    context_2 = await redis_storage.get_session_context(session_id_2)
    
    assert context_1 is not None
    assert context_2 is not None
    assert len(context_1["conversations"]) == 1
    assert len(context_2["conversations"]) == 1
    assert context_1["conversations"][0]["query"] == "Session 1 Query"
    assert context_2["conversations"][0]["query"] == "Session 2 Query"
    
    # Cleanup
    await redis_storage.delete_session(session_id_1)
    await redis_storage.delete_session(session_id_2)

@pytest.mark.asyncio
async def test_delete_session(redis_storage):
    """Test deleting a session"""
    session_id = "test-session-7"
    
    await redis_storage.append_conversation(
        session_id, 
        "Test Query", 
        "Test Response", 
        {}
    )
    
    # Verify session exists
    context = await redis_storage.get_session_context(session_id)
    assert context is not None
    
    # Delete session
    await redis_storage.delete_session(session_id)
    
    # Verify session is deleted
    context_after = await redis_storage.get_session_context(session_id)
    assert context_after is None

@pytest.mark.asyncio
async def test_ttl_expiration(redis_storage):
    """Test that sessions expire after TTL"""
    session_id = "test-session-8"
    short_ttl_storage = RedisSessionStorage(
        host=TEST_REDIS_HOST,
        port=TEST_REDIS_PORT,
        db=TEST_REDIS_DB,
        session_ttl=2  # 2 seconds
    )
    
    await short_ttl_storage.append_conversation(
        session_id, 
        "Test Query", 
        "Test Response", 
        {}
    )
    
    # Verify session exists immediately
    context = await short_ttl_storage.get_session_context(session_id)
    assert context is not None
    
    # Wait for TTL to expire
    await asyncio.sleep(3)
    
    # Verify session has expired
    context_after = await short_ttl_storage.get_session_context(session_id)
    assert context_after is None
    
    await short_ttl_storage.close()
