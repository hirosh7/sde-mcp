#!/usr/bin/env python3
"""
Test script to measure Claude formatting response times.
This helps determine appropriate timeout values.
"""
import asyncio
import time
import json
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-proxy-service'))

load_dotenv()

from app.claude_formatter import ClaudeResponseFormatter
from app.config import Config

async def test_formatting_timing():
    """Test Claude formatting with various result sizes"""
    
    if not Config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return
    
    formatter = ClaudeResponseFormatter(
        api_key=Config.ANTHROPIC_API_KEY,
        model=Config.CLAUDE_MODEL,
        timeout=120.0  # Use longer timeout for testing
    )
    
    # Test cases with different sizes
    test_cases = [
        {
            "name": "Small result (5 countermeasures)",
            "tool_name": "list_countermeasures",
            "result": {
                "results": [
                    {"id": f"T{i}", "title": f"Task {i}", "phase": "X2", "status": "Complete"}
                    for i in range(1, 6)
                ]
            },
            "query": "Get all tasks and summarize them by phase, task id and task title"
        },
        {
            "name": "Medium result (20 countermeasures)",
            "tool_name": "list_countermeasures",
            "result": {
                "results": [
                    {"id": f"T{i}", "title": f"Task {i}", "phase": f"X{(i % 3) + 2}", "status": "Complete"}
                    for i in range(1, 21)
                ]
            },
            "query": "Get all tasks and summarize them by phase, task id and task title"
        },
        {
            "name": "Large result (50 countermeasures)",
            "tool_name": "list_countermeasures",
            "result": {
                "results": [
                    {"id": f"T{i}", "title": f"Task {i}", "phase": f"X{(i % 5) + 2}", "status": "Complete"}
                    for i in range(1, 51)
                ]
            },
            "query": "Get all tasks and summarize them by phase, task id and task title"
        },
        {
            "name": "Very large result (100 countermeasures)",
            "tool_name": "list_countermeasures",
            "result": {
                "results": [
                    {"id": f"T{i}", "title": f"Task {i}", "phase": f"X{(i % 5) + 2}", "status": "Complete"}
                    for i in range(1, 101)
                ]
            },
            "query": "Get all tasks and summarize them by phase, task id and task title"
        }
    ]
    
    print(f"Testing Claude formatting with model: {Config.CLAUDE_MODEL}")
    print(f"Timeout: 120 seconds\n")
    print("=" * 80)
    
    results = []
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print(f"Result size: {len(test_case['result'].get('results', []))} items")
        
        start_time = time.time()
        try:
            formatted_response = await formatter.format_result(
                tool_name=test_case['tool_name'],
                result=test_case['result'],
                original_query=test_case['query'],
                conversation_history=None
            )
            duration = time.time() - start_time
            
            # Check if response looks formatted (not JSON)
            is_json = formatted_response.strip().startswith(("{", "[", "```json"))
            response_preview = formatted_response[:200].replace("\n", " ")
            
            print(f"✓ Completed in {duration:.2f} seconds")
            print(f"  Response preview: {response_preview}...")
            print(f"  Looks like JSON: {is_json}")
            print(f"  Response length: {len(formatted_response)} characters")
            
            results.append({
                "test": test_case['name'],
                "duration": duration,
                "success": True,
                "is_json": is_json,
                "response_length": len(formatted_response)
            })
            
        except asyncio.TimeoutError as e:
            duration = time.time() - start_time
            print(f"✗ Timed out after {duration:.2f} seconds")
            results.append({
                "test": test_case['name'],
                "duration": duration,
                "success": False,
                "error": "Timeout"
            })
        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ Failed after {duration:.2f} seconds: {e}")
            results.append({
                "test": test_case['name'],
                "duration": duration,
                "success": False,
                "error": str(e)
            })
    
    print("\n" + "=" * 80)
    print("\nSummary:")
    print("-" * 80)
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['test']}: {result['duration']:.2f}s")
        if not result['success']:
            print(f"    Error: {result.get('error', 'Unknown')}")
        elif result.get('is_json'):
            print(f"    WARNING: Response appears to be JSON, not formatted text")
    
    # Calculate statistics
    successful = [r for r in results if r['success']]
    if successful:
        durations = [r['duration'] for r in successful]
        print(f"\nStatistics (successful tests only):")
        print(f"  Average: {sum(durations) / len(durations):.2f}s")
        print(f"  Min: {min(durations):.2f}s")
        print(f"  Max: {max(durations):.2f}s")
        print(f"\nRecommended timeout: {max(durations) * 1.5:.0f}s (1.5x max duration)")

if __name__ == "__main__":
    asyncio.run(test_formatting_timing())

