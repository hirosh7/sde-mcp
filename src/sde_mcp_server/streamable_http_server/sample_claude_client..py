import asyncio
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()  # Load ANTHROPIC_API_KEY from .env
class MCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.anthropic = Anthropic()  # Requires ANTHROPIC_API_KEY env var
        self.session: Optional[ClientSession] = None
        self.tools = []
        self.client_context = None
        self.session_context = None
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
    async def process_query(self, query: str) -> str:
        # Send message to Claude with tool list
        # NOTE: Model name must match your API access. Common models:
        # - claude-sonnet-4-20250514 (latest)
        # - claude-3-5-sonnet-20241022
        # - claude-3-5-sonnet-20240620
        # - claude-3-opus-20240229
        # - claude-3-sonnet-20240229
        # - claude-3-haiku-20240307
        try:
            claude_resp = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",  # Update this to match your API access
                max_tokens=500,
                messages=[{"role": "user", "content": query}],
                tools=self.tools,
            )
        except Exception as e:
            error_msg = str(e)
            if "not_found_error" in error_msg or "404" in error_msg:
                raise ValueError(
                    f"Model not found. Please update the model name in the code. "
                    f"Check available models at https://console.anthropic.com/. "
                    f"Original error: {error_msg}"
                ) from e
            raise
        output = []
        for chunk in claude_resp.content:
            if chunk.type == "text":
                output.append(chunk.text)
            elif chunk.type == "tool_use":
                name, args = chunk.name, chunk.input
                result = await self.session.call_tool(name, args)
                output.append(f"[Tool Call] {name}({args}) -> {result.content!r}")
        return "\n".join(output)
    async def chat_loop(self):
        print("Ask questions (type 'exit' to quit):")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            response = await self.process_query(user_input)
            print("Assistant:", response)
    async def close(self):
        if self.session_context:
            await self.session_context.__aexit__(None, None, None)
        if self.client_context:
            await self.client_context.__aexit__(None, None, None)
async def main():
    client = MCPClient("http://localhost:8000/mcp")
    try:
        await client.connect()
        # Direct test
        print(await client.process_query("What is the addition of 23 and 56.67?"))
        # Optionally enable chat
        await client.chat_loop()
    finally:
        await client.close()
if __name__ == "__main__":
    asyncio.run(main())