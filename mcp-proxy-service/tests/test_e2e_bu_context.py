"""End-to-end test for business unit context retention"""
import asyncio
import httpx
import json

# Configuration
MCP_PROXY_URL = "http://localhost:8002"
TEST_TIMEOUT = 30.0


async def make_query(query: str, session_id: str = None) -> dict:
    """Make a query to the MCP proxy service"""
    async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
        payload = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        response = await client.post(
            f"{MCP_PROXY_URL}/api/v1/query",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"\nResponse:")
        print(f"  Success: {data.get('success')}")
        print(f"  Session ID: {data.get('session_id')}")
        print(f"  Tool: {data.get('tool_name')}")
        if data.get('error'):
            print(f"  Error: {data.get('error')}")
        print(f"\nResponse Text:")
        try:
            print(f"{data.get('response', '')}")
        except UnicodeEncodeError:
            # Handle Unicode characters for Windows console
            response_text = data.get('response', '')
            print(response_text.encode('ascii', 'ignore').decode('ascii'))
        
        return data


async def main():
    """Run the end-to-end test scenario"""
    print("="*60)
    print("End-to-End Context Test: Business Units")
    print("="*60)
    
    # Query 1: List all business units
    response1 = await make_query("List all business units")
    
    if not response1.get("success"):
        print(f"\nERROR: First query failed: {response1.get('error')}")
        return
    
    session_id = response1.get("session_id")
    if not session_id:
        print("\nERROR: No session_id in response")
        return
    
    print(f"\n[OK] Session ID: {session_id}")
    
    # Query 2: What is the count of business units
    response2 = await make_query("What is the count of business units", session_id=session_id)
    
    if not response2.get("success"):
        print(f"\nERROR: Second query failed: {response2.get('error')}")
        return
    
    # Query 3: What applications and projects are associated with the second BU you listed
    response3 = await make_query(
        "What applications and projects are associated with the second BU you listed",
        session_id=session_id
    )
    
    if not response3.get("success"):
        print(f"\nERROR: Third query failed: {response3.get('error')}")
        print(f"Error details: {response3.get('error')}")
        return
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
