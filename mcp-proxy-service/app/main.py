"""Main FastAPI application for MCP Proxy Service"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import Config
from app.models import QueryRequest, QueryResponse, HealthResponse
from app.mcp_client import MCPHTTPClient
from app.claude_adapter import ClaudeToolSelector
from app.claude_formatter import ClaudeResponseFormatter
from app.response_formatter import FallbackResponseFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
mcp_client: MCPHTTPClient | None = None
claude_selector: ClaudeToolSelector | None = None
claude_formatter: ClaudeResponseFormatter | None = None
fallback_formatter: FallbackResponseFormatter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global mcp_client, claude_selector, claude_formatter, fallback_formatter
    
    # Startup
    logger.info("Starting MCP Proxy Service...")
    Config.validate()
    
    try:
        # Initialize MCP client
        mcp_client = MCPHTTPClient(Config.MCP_SERVER_URL)
        await mcp_client.connect()
        logger.info(f"Connected to MCP server at {Config.MCP_SERVER_URL}")
        
        # Initialize Claude selector
        claude_selector = ClaudeToolSelector(
            api_key=Config.ANTHROPIC_API_KEY,
            model=Config.CLAUDE_MODEL
        )
        logger.info(f"Initialized Claude adapter with model {Config.CLAUDE_MODEL}")
        
        # Initialize Claude formatter
        claude_formatter = ClaudeResponseFormatter(
            api_key=Config.ANTHROPIC_API_KEY,
            model=Config.CLAUDE_MODEL
        )
        logger.info("Initialized Claude response formatter")
        
        # Initialize fallback formatter
        fallback_formatter = FallbackResponseFormatter()
        logger.info("Initialized fallback response formatter")
        
        logger.info("MCP Proxy Service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP Proxy Service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Proxy Service...")
    if mcp_client:
        await mcp_client.close()
    logger.info("MCP Proxy Service stopped")


# Create FastAPI app
app = FastAPI(
    title="MCP Proxy Service",
    description="Proxy service for natural language SD Elements queries via MCP",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    mcp_connected = mcp_client is not None and mcp_client.session is not None
    return HealthResponse(
        status="healthy",
        service="mcp-proxy",
        mcp_server_connected=mcp_connected
    )


@app.get("/api/v1/tools")
async def list_tools():
    """List available MCP tools"""
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        tools = await mcp_client.get_tools()
        return {"tools": tools, "count": len(tools)}
    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sde-instance")
async def get_sde_instance():
    """Get SDE instance information"""
    import os
    from .config import Config
    
    # Try to get SDE_HOST from environment (passed through from docker-compose)
    sde_host = os.getenv("SDE_HOST", "")
    
    if sde_host:
        # Remove protocol if present
        instance_url = sde_host.replace("http://", "").replace("https://", "").rstrip("/")
        
        # Extract instance name from URL
        # For example: sde-ent-onyxdrift.sdelab.net -> "Onyxdrift"
        instance_name = "SD Elements"
        if "sdelab.net" in instance_url or "sdelements.com" in instance_url:
            # Extract subdomain or instance identifier
            parts = instance_url.split(".")
            if len(parts) > 0:
                subdomain = parts[0]
                if subdomain.startswith("sde-"):
                    instance_name = subdomain.replace("sde-", "").replace("-", " ").title()
                else:
                    instance_name = subdomain.replace("-", " ").title()
        
        return {
            "instance_name": instance_name,
            "instance_url": instance_url
        }
    else:
        # Fallback: extract from MCP server URL
        mcp_url = Config.MCP_SERVER_URL
        instance_url = mcp_url.replace("/mcp", "").replace("http://", "").replace("https://", "")
        return {
            "instance_name": "SD Elements",
            "instance_url": instance_url if instance_url else "Unknown"
        }


@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query.
    
    This endpoint:
    1. Uses Claude to select the appropriate tool
    2. Calls the tool via MCP
    3. Formats the result into natural language
    """
    if not mcp_client or not claude_selector or not claude_formatter or not fallback_formatter:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    try:
        # Get available tools
        tools = await mcp_client.get_tools()
        
        if not tools:
            return QueryResponse(
                response="No tools available from MCP server",
                success=False,
                error="No tools available"
            )
        
        # Use Claude to select tool
        try:
            tool_name, arguments = await claude_selector.select_tool(request.query, tools)
        except ValueError as e:
            return QueryResponse(
                response=str(e),
                success=False,
                error=str(e),
                tool_name=None
            )
        
        # Call the tool
        try:
            result = await mcp_client.call_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return QueryResponse(
                response=f"Failed to execute tool '{tool_name}': {str(e)}",
                success=False,
                error=str(e),
                tool_name=tool_name
            )
        
        # Format the result using Claude, with fallback to manual formatter
        try:
            formatted_response = await claude_formatter.format_result(
                tool_name=tool_name,
                result=result,
                original_query=request.query
            )
        except Exception as e:
            logger.warning(f"Claude formatting failed, using fallback: {e}")
            # Fallback to manual formatter
            formatted_response = fallback_formatter.format_tool_result(tool_name, result)
        
        return QueryResponse(
            response=formatted_response,
            success=True,
            tool_name=tool_name
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        return QueryResponse(
            response=f"An error occurred: {str(e)}",
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

