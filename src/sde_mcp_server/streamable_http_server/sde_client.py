import asyncio
import json
import os
import time
from typing import Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()  # Load ANTHROPIC_API_KEY from .env

class MCPClient:
    def __init__(self, server_url: str, enable_timing: bool = False):
        self.server_url = server_url
        self.anthropic = Anthropic()  # Requires ANTHROPIC_API_KEY env var
        self.session: Optional[ClientSession] = None
        self.tools = []
        self.client_context = None
        self.session_context = None
        self.conversation_history: list = []  # Track conversation for context
        # Enable timing via parameter or ENABLE_TIMING env var
        self.enable_timing = enable_timing or os.getenv("ENABLE_TIMING", "").lower() in ("true", "1", "yes")

    async def connect(self):
        # Connect to the streamable HTTP server
        self.client_context = streamablehttp_client(self.server_url)
        read_stream, write_stream, _ = await self.client_context.__aenter__()
        # Create a session using the client streams
        self.session_context = ClientSession(read_stream, write_stream)
        self.session = await self.session_context.__aenter__()
        await self.session.initialize()
        resp = await self.session.list_tools()
        self.tools = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
            }
            for t in resp.tools
        ]
        print("Connected: Tools available =", [t["name"] for t in self.tools])

    def _format_tool_result(self, tool_name: str, result_content: Any) -> str:
        """Format tool result content as natural language"""
        # Handle MCP content structure - result.content can be a list of content items
        if hasattr(result_content, '__iter__') and not isinstance(result_content, (str, dict)):
            # Extract text from content items (e.g., TextContent objects)
            text_parts = []
            for item in result_content:
                if hasattr(item, 'text'):
                    text_parts.append(item.text)
                elif isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
            if text_parts:
                result_content = '\n'.join(text_parts)
            else:
                # If we can't extract text, convert to string
                result_content = str(result_content)
        
        # Now handle as string
        if isinstance(result_content, str):
            # Try to parse as JSON
            try:
                data = json.loads(result_content)
            except (json.JSONDecodeError, TypeError):
                # Not JSON, return as-is
                return result_content
        else:
            data = result_content
        
        # Format common response structures
        if isinstance(data, dict):
            # Handle success/error responses
            if "success" in data:
                if data["success"]:
                    parts = [f"[SUCCESS] {tool_name} completed successfully"]
                    if "message" in data:
                        parts.append(f": {data['message']}")
                    # Include key information
                    for key in ["project", "application", "profile", "result"]:
                        if key in data and data[key]:
                            parts.append(f"\n{key.title()}: {json.dumps(data[key], indent=2)}")
                    return "\n".join(parts)
                else:
                    return f"[ERROR] {tool_name} failed: {data.get('error', 'Unknown error')}"
            
            # Format as readable text
            formatted_parts = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    formatted_parts.append(f"{key}: {json.dumps(value, indent=2)}")
                else:
                    formatted_parts.append(f"{key}: {value}")
            return "\n".join(formatted_parts)
        
        # For lists or other types, try to serialize safely
        try:
            return json.dumps(data, indent=2, default=str)
        except (TypeError, ValueError):
            return str(data)

    async def process_query(self, query: str, conversation_history: Optional[list] = None) -> str:
        """Process a query with Claude, handling tool calls and formatting responses"""
        query_start = time.time()
        self._timing_print(f"\n[TIMING] Starting query processing at {query_start:.2f}")
        
        # Send message to Claude with tool list
        # NOTE: Model name must match your API access. Common models:
        # - claude-sonnet-4-20250514 (latest)
        # - claude-3-5-sonnet-20241022
        # - claude-3-5-sonnet-20240620
        # - claude-3-opus-20240229
        # - claude-3-sonnet-20240229
        # - claude-3-haiku-20240307
        
        # Use a copy of conversation history to avoid modifying the original
        messages = (conversation_history or []).copy() if conversation_history else []
        initial_message_count = len(messages)
        messages.append({"role": "user", "content": query})
        
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            iteration_start = time.time()
            self._timing_print(f"[TIMING] Iteration {iteration} started at {iteration_start:.2f}")
            
            try:
                claude_start = time.time()
                self._timing_print(f"[TIMING] Calling Claude API (Haiku)...")
                claude_resp = self.anthropic.messages.create(
                    model="claude-3-5-haiku-20241022",  # Fast and cost-effective model
                    max_tokens=4000,
                    messages=messages,
                    tools=self.tools,
                )
                claude_elapsed = time.time() - claude_start
                self._timing_print(f"[TIMING] Claude API responded in {claude_elapsed:.2f}s")
            except Exception as e:
                error_msg = str(e)
                if "not_found_error" in error_msg or "404" in error_msg:
                    raise ValueError(
                        f"Model not found. Please update the model name in the code. "
                        f"Check available models at https://console.anthropic.com/. "
                        f"Original error: {error_msg}"
                    ) from e
                raise
            
            # Add Claude's response to conversation history
            assistant_message = {"role": "assistant", "content": []}
            tool_results = []
            
            for chunk in claude_resp.content:
                if chunk.type == "text":
                    assistant_message["content"].append({"type": "text", "text": chunk.text})
                elif chunk.type == "tool_use":
                    # Call the tool
                    tool_name = chunk.name
                    tool_args = chunk.input
                    tool_id = chunk.id
                    
                    tool_start = time.time()
                    self._timing_print(f"[TIMING] Calling tool: {tool_name} with args: {json.dumps(tool_args, default=str)[:100]}...")
                    result = await self.session.call_tool(tool_name, tool_args)
                    tool_elapsed = time.time() - tool_start
                    self._timing_print(f"[TIMING] Tool {tool_name} completed in {tool_elapsed:.2f}s")
                    
                    # Format the result
                    format_start = time.time()
                    formatted_result = self._format_tool_result(tool_name, result.content)
                    format_elapsed = time.time() - format_start
                    self._timing_print(f"[TIMING] Result formatting took {format_elapsed:.2f}s")
                    
                    # Add tool use to assistant message
                    assistant_message["content"].append({
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_args,
                    })
                    
                    # Add tool result to be sent back to Claude
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": formatted_result,
                    })
            
            messages.append(assistant_message)
            
            iteration_elapsed = time.time() - iteration_start
            self._timing_print(f"[TIMING] Iteration {iteration} completed in {iteration_elapsed:.2f}s")
            
            # If there are tool results, send them back to Claude for natural language response
            if tool_results:
                self._timing_print(f"[TIMING] {len(tool_results)} tool result(s) to send back to Claude")
                messages.append({"role": "user", "content": tool_results})
                # Continue loop to get Claude's final response after processing tool results
                continue
            else:
                # No more tool calls, return the final text response
                text_parts = [
                    item["text"] for item in assistant_message["content"] 
                    if item.get("type") == "text"
                ]
                final_response = "\n".join(text_parts) if text_parts else "No response generated."
                # Update conversation history with this exchange
                if conversation_history is not None:
                    # Only add NEW messages (not the ones we copied from history)
                    new_messages = messages[initial_message_count:]
                    conversation_history.extend(new_messages)
                
                total_elapsed = time.time() - query_start
                self._timing_print(f"[TIMING] COMPLETE: Total query processing completed in {total_elapsed:.2f}s ({iteration} iterations)")
                return final_response
        
        total_elapsed = time.time() - query_start
        self._timing_print(f"[TIMING] ERROR: Maximum iterations reached after {total_elapsed:.2f}s")
        return "Maximum iterations reached. Please try a simpler query."

    def _safe_print(self, text: str):
        """Print text safely handling Unicode on Windows"""
        try:
            print(text)
        except UnicodeEncodeError:
            # Replace Unicode characters that can't be encoded
            safe_text = text.encode('ascii', 'replace').decode('ascii')
            print(safe_text)
    
    def _timing_print(self, text: str):
        """Print timing information only if timing is enabled"""
        if self.enable_timing:
            print(text, flush=True)

    async def chat_loop(self):
        print("Ask questions (type 'exit' to quit, 'clear' to reset conversation):")
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if user_input.lower() == "clear":
                self.conversation_history = []
                print("Conversation history cleared.")
                continue
            if not user_input:
                continue
            
            try:
                response = await self.process_query(user_input, self.conversation_history)
                print("\nAssistant:", end=" ")
                self._safe_print(response)
            except Exception as e:
                print(f"\nError: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()


    async def close(self):
        if self.session_context:
            await self.session_context.__aexit__(None, None, None)
        if self.client_context:
            await self.client_context.__aexit__(None, None, None)


async def main():
    # Enable timing via ENABLE_TIMING env var (set to "true", "1", or "yes")
    # or pass enable_timing=True to MCPClient constructor
    client = MCPClient("http://localhost:8001/mcp")
    try:
        await client.connect()
        # Direct test - test connection to SD Elements
        print(await client.process_query("Test the connection to SD Elements"))
        # Enable chat loop for interactive testing
        await client.chat_loop()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

