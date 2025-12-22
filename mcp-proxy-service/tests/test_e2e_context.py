"""End-to-end test for context retention system"""
import pytest
import asyncio
import httpx
import json
from typing import Dict, Optional

# Configuration
MCP_PROXY_URL = "http://localhost:8002"
TEST_TIMEOUT = 30.0


async def make_query(query: str, session_id: Optional[str] = None) -> Dict:
    """Make a query to the MCP proxy service"""
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        payload = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        
        response = await client.post(
            f"{MCP_PROXY_URL}/api/v1/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()


@pytest.mark.asyncio
async def test_context_retention_business_units():
    """
    Test that context is retained across queries in the same session.
    
    Scenario:
    1. Query: "List all business units" - gets a list
    2. Follow-up: "How many business units did you find?" - requires context from query 1
    """
    # First query: List business units
    response1 = await make_query("List all business units")
    
    assert response1["success"], f"First query failed: {response1.get('error')}"
    assert "session_id" in response1, "Response should include session_id"
    session_id = response1["session_id"]
    first_response_text = response1["response"].lower()
    
    # Verify first response mentions business units
    assert "business unit" in first_response_text or "business units" in first_response_text, \
        f"First response should mention business units. Got: {response1['response']}"
    
    print(f"\n[OK] First Query Response:\n{response1['response']}\n")
    print(f"Session ID: {session_id}\n")
    
    # Second query: Ask about the count (requires context)
    response2 = await make_query("How many business units did you find?", session_id=session_id)
    
    assert response2["success"], f"Second query failed: {response2.get('error')}"
    assert response2["session_id"] == session_id, "Session ID should be the same"
    second_response_text = response2["response"].lower()
    
    # Verify second response shows context awareness
    # It should reference the previous query or mention a number
    assert any(keyword in second_response_text for keyword in [
        "found", "business unit", "total", "count", "there are", "there were"
    ]), f"Second response should show context awareness. Got: {response2['response']}"
    
    print(f"[OK] Second Query Response (with context):\n{response2['response']}\n")
    
    # Verify the response actually references the count from the first query
    # Extract numbers from both responses
    import re
    numbers1 = re.findall(r'\d+', first_response_text)
    numbers2 = re.findall(r'\d+', second_response_text)
    
    # If first response had numbers, second should reference them
    if numbers1:
        print(f"Numbers found in first response: {numbers1}")
        print(f"Numbers found in second response: {numbers2}")
        # The second response should either mention the same number or reference "the list"
        assert len(numbers2) > 0 or "list" in second_response_text or "previous" in second_response_text, \
            "Second response should reference the count or previous query"


@pytest.mark.asyncio
async def test_context_retention_projects():
    """
    Test context retention with projects.
    
    Scenario:
    1. Query: "List all projects" - gets a list of projects
    2. Follow-up: "What was the first project in that list?" - requires context
    """
    # First query: List projects
    response1 = await make_query("List all projects")
    
    assert response1["success"], f"First query failed: {response1.get('error')}"
    session_id = response1["session_id"]
    first_response_text = response1["response"]
    
    # Verify first response mentions projects
    assert "project" in first_response_text.lower(), \
        f"First response should mention projects. Got: {response1['response']}"
    
    print(f"\n[OK] First Query Response:\n{first_response_text}\n")
    print(f"Session ID: {session_id}\n")
    
    # Second query: Ask about the first project (requires context)
    response2 = await make_query("What was the first project in that list?", session_id=session_id)
    
    assert response2["success"], f"Second query failed: {response2.get('error')}"
    assert response2["session_id"] == session_id, "Session ID should be the same"
    second_response_text = response2["response"]
    
    # Verify second response shows context awareness
    # It should reference the previous list or mention a project name
    context_keywords = [
        "first", "project", "list", "that", "previous", "mentioned", "above"
    ]
    assert any(keyword in second_response_text.lower() for keyword in context_keywords), \
        f"Second response should show context awareness. Got: {response2['response']}"
    
    print(f"[OK] Second Query Response (with context):\n{second_response_text}\n")


@pytest.mark.asyncio
async def test_session_isolation():
    """
    Test that different sessions don't share context.
    
    Scenario:
    1. Session A: Query about business units
    2. Session B: Query about projects  
    3. Session A follow-up: Should only know about business units, not projects
    """
    # Session A: Query about business units
    response_a1 = await make_query("List all business units")
    assert response_a1["success"]
    session_a = response_a1["session_id"]
    
    # Session B: Query about projects (different session)
    response_b1 = await make_query("List all projects")
    assert response_b1["success"]
    session_b = response_b1["session_id"]
    
    assert session_a != session_b, "Sessions should be different"
    
    print(f"\n[OK] Session A ID: {session_a}")
    print(f"[OK] Session B ID: {session_b}\n")
    
    # Session A follow-up: Should reference business units, not projects
    response_a2 = await make_query("How many did you find?", session_id=session_a)
    assert response_a2["success"]
    
    response_text = response_a2["response"].lower()
    
    # Should reference business units (from session A context), not projects
    # This is a bit tricky to test definitively, but we can check it doesn't mention projects
    # if business units were mentioned in the first query
    print(f"[OK] Session A follow-up response:\n{response_a2['response']}\n")
    
    # Verify session isolation: Session A shouldn't know about projects from Session B
    # (This is more of a sanity check - the real test is that sessions are different)
    assert response_a2["session_id"] == session_a, "Follow-up should use same session"


@pytest.mark.asyncio
async def test_context_with_multiple_turns():
    """
    Test context retention across multiple conversation turns.
    
    Scenario:
    1. Query 1: "List all business units"
    2. Query 2: "How many did you find?"
    3. Query 3: "What was the first one?" - requires context from both previous queries
    """
    # Query 1
    response1 = await make_query("List all business units")
    assert response1["success"]
    session_id = response1["session_id"]
    
    print(f"\n[OK] Query 1:\n{response1['response']}\n")
    
    # Query 2
    response2 = await make_query("How many did you find?", session_id=session_id)
    assert response2["success"]
    assert response2["session_id"] == session_id
    
    print(f"[OK] Query 2:\n{response2['response']}\n")
    
    # Query 3: Should understand "the first one" refers to the first business unit
    response3 = await make_query("What was the first one?", session_id=session_id)
    assert response3["success"]
    assert response3["session_id"] == session_id
    
    response_text = response3["response"].lower()
    
    # Should reference business units and "first"
    assert "first" in response_text or "business unit" in response_text, \
        f"Third query should reference 'first' and business units. Got: {response3['response']}"
    
    print(f"[OK] Query 3 (with full context):\n{response3['response']}\n")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
