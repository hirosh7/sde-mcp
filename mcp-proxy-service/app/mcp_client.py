"""MCP HTTP client for connecting to the SDE MCP Server"""
import json
from datetime import datetime, timedelta
from typing import Any, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class MCPHTTPClient:
    """Client for connecting to MCP server via streamable HTTP"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self.tools = []
        self.client_context = None
        self.session_context = None
        
        # Tool list caching
        self._tool_cache = None
        self._cache_time = None
        self._cache_ttl = timedelta(minutes=5)
    
    async def connect(self):
        """Connect to the MCP server and fetch available tools"""
        # Connect to the streamable HTTP server
        self.client_context = streamablehttp_client(self.server_url)
        read_stream, write_stream, _ = await self.client_context.__aenter__()
        
        # Create a session using the client streams
        self.session_context = ClientSession(read_stream, write_stream)
        self.session = await self.session_context.__aenter__()
        await self.session.initialize()
        
        # Fetch tools
        await self.get_tools()
    
    async def get_tools(self) -> list:
        """Get available tools, using cache if available"""
        now = datetime.now()
        if self._tool_cache and self._cache_time:
            if now - self._cache_time < self._cache_ttl:
                return self._tool_cache
        
        # Fetch from server
        if not self.session:
            await self.connect()
        
        resp = await self.session.list_tools()
        self.tools = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema,
            }
            for t in resp.tools
        ]
        
        self._tool_cache = self.tools
        self._cache_time = now
        return self.tools
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool and return the result as a dictionary"""
        if not self.session:
            await self.connect()
        
        result = await self.session.call_tool(tool_name, arguments)
        
        # Extract content from MCP result structure
        content = result.content
        if hasattr(content, '__iter__') and not isinstance(content, (str, dict)):
            # Handle list of content items
            text_parts = []
            for item in content:
                if hasattr(item, 'text'):
                    text_parts.append(item.text)
                elif isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
            if text_parts:
                content = '\n'.join(text_parts)
            else:
                content = str(content)
        
        # Parse JSON if possible
        if isinstance(content, str):
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                return {"raw": content}
        
        return content if isinstance(content, dict) else {"raw": str(content)}
    
    async def close(self):
        """Close the MCP connection"""
        if self.session_context:
            await self.session_context.__aexit__(None, None, None)
        if self.client_context:
            await self.client_context.__aexit__(None, None, None)

