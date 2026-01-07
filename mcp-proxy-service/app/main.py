"""Main FastAPI application for MCP Proxy Service"""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import Config
from app.models import QueryRequest, QueryResponse, HealthResponse
from app.mcp_client import MCPHTTPClient
from app.claude_adapter import ClaudeToolSelector
from app.claude_formatter import ClaudeResponseFormatter
from app.response_formatter import FallbackResponseFormatter
from app.redis_session import RedisSessionStorage

# Configure logging
log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
mcp_client: MCPHTTPClient | None = None
claude_selector: ClaudeToolSelector | None = None
claude_formatter: ClaudeResponseFormatter | None = None
fallback_formatter: FallbackResponseFormatter | None = None
redis_storage: RedisSessionStorage | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global mcp_client, claude_selector, claude_formatter, fallback_formatter, redis_storage
    
    # Startup
    logger.info("Starting MCP Proxy Service...")
    Config.validate()
    
    try:
        # Initialize Redis storage
        redis_storage = RedisSessionStorage(
            redis_url=Config.REDIS_URL,
            ttl_hours=Config.SESSION_TTL_HOURS,
            max_conversations=Config.SESSION_MAX_CONVERSATIONS
        )
        await redis_storage.connect()
        logger.info(f"Connected to Redis at {Config.REDIS_URL}")
        
        # Initialize MCP client
        mcp_client = MCPHTTPClient(Config.MCP_SERVER_URL)
        await mcp_client.connect()
        logger.info(f"Connected to MCP server at {Config.MCP_SERVER_URL}")
        
        # Initialize Claude selector
        claude_selector = ClaudeToolSelector(
            api_key=Config.ANTHROPIC_API_KEY,
            model=Config.CLAUDE_MODEL,
            tool_selection_model=Config.CLAUDE_TOOL_SELECTION_MODEL
        )
        logger.info(f"Initialized Claude adapter with model {Config.CLAUDE_MODEL} (tool selection: {Config.CLAUDE_TOOL_SELECTION_MODEL})")
        
        # Initialize Claude formatter with configurable timeout
        claude_formatter = ClaudeResponseFormatter(
            api_key=Config.ANTHROPIC_API_KEY,
            model=Config.CLAUDE_MODEL,
            timeout=Config.CLAUDE_FORMATTER_TIMEOUT
        )
        logger.info(f"Initialized Claude response formatter (timeout: {Config.CLAUDE_FORMATTER_TIMEOUT}s)")
        
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
    if redis_storage:
        await redis_storage.close()
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
    Process a natural language query with session context.
    
    This endpoint:
    1. Retrieves conversation history from Redis (if session_id provided)
    2. Uses Claude to select the appropriate tool with context
    3. Calls the tool via MCP
    4. Formats the result into natural language with context
    5. Stores the conversation in Redis
    """
    if not all([mcp_client, claude_selector, claude_formatter, fallback_formatter, redis_storage]):
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    # Generate or use provided session_id
    # Handle empty strings as None (Pydantic might send empty string instead of None)
    logger.debug(f"[MCP-Proxy] Received request with session_id: {request.session_id!r} (type: {type(request.session_id).__name__})")
    
    provided_session_id = None
    if request.session_id:
        stripped = request.session_id.strip()
        if stripped:  # Only use non-empty strings
            provided_session_id = stripped
            logger.debug(f"[MCP-Proxy] Stripped session_id: {provided_session_id!r}")
        else:
            logger.warning(f"[MCP-Proxy] session_id was empty string after stripping")
    else:
        logger.debug(f"[MCP-Proxy] request.session_id is None or falsy")
    
    if provided_session_id:
        session_id = provided_session_id
        logger.info(f"[MCP-Proxy] Using provided session_id: {session_id}")
    else:
        session_id = str(uuid.uuid4())
        logger.warning(f"[MCP-Proxy] Generated new session_id: {session_id} (request.session_id was: {request.session_id!r})")
    
    try:
        # Retrieve conversation history from Redis
        conversation_history = await redis_storage.get_conversation_history(session_id)
        if conversation_history:
            logger.info(f"Session {session_id}: Retrieved {len(conversation_history)} previous conversation(s) from history")
        else:
            logger.debug(f"Session {session_id}: No previous conversations found (new session)")
        
        # Get available tools
        tools = await mcp_client.get_tools()
        
        if not tools:
            return QueryResponse(
                response="No tools available from MCP server",
                success=False,
                error="No tools available",
                session_id=session_id
            )
        
        # Use Claude to select tool with conversation history
        try:
            tool_name, arguments = await claude_selector.select_tool(
                request.query, 
                tools,
                conversation_history=conversation_history
            )
        except ValueError as e:
            return QueryResponse(
                response=str(e),
                success=False,
                error=str(e),
                tool_name=None,
                session_id=session_id
            )
        
        # Check if this is a data transformation request (no tool needed)
        if tool_name is None and arguments.get("is_data_transformation"):
            logger.info(f"Session {session_id}: Handling data transformation request (no tool call needed)")
            # Use Claude to transform data from conversation history
            try:
                formatted_response = await claude_formatter.transform_data(
                    query=request.query,
                    conversation_history=conversation_history
                )
            except Exception as e:
                logger.error(f"Data transformation failed: {e}")
                return QueryResponse(
                    response=f"Failed to transform data: {str(e)}",
                    success=False,
                    error=str(e),
                    tool_name=None,
                    session_id=session_id
                )
        else:
            # Normal flow: call tool and format result
            # Call the tool
            try:
                result = await mcp_client.call_tool(tool_name, arguments)
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return QueryResponse(
                    response=f"Failed to execute tool '{tool_name}': {str(e)}",
                    success=False,
                    error=str(e),
                    tool_name=tool_name,
                    session_id=session_id
                )
            
            # Format the result using Claude with conversation history, with fallback to manual formatter
            format_start_time = time.time()
            try:
                formatted_response = await claude_formatter.format_result(
                    tool_name=tool_name,
                    result=result,
                    original_query=request.query,
                    conversation_history=conversation_history
                )
                format_duration = time.time() - format_start_time
                logger.info(f"Claude formatting completed in {format_duration:.2f}s for tool '{tool_name}'")
            except Exception as e:
                format_duration = time.time() - format_start_time
                logger.warning(f"Claude formatting failed after {format_duration:.2f}s, using fallback: {e}")
                logger.debug(f"Claude formatting error details: {type(e).__name__}: {str(e)}")
                # Fallback to manual formatter with original query for context-aware formatting
                formatted_response = fallback_formatter.format_tool_result(tool_name, result, original_query=request.query)
                logger.info(f"Fallback formatter completed for tool '{tool_name}'")
        
        # Store conversation in Redis
        await redis_storage.append_conversation(
            session_id=session_id,
            query=request.query,
            response=formatted_response,
            metadata={
                "tool_name": tool_name,
                "success": True
            }
        )
        logger.debug(f"Session {session_id}: Stored conversation in Redis (total conversations: {len(conversation_history) + 1})")
        
        return QueryResponse(
            response=formatted_response,
            success=True,
            session_id=session_id,
            tool_name=tool_name
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        return QueryResponse(
            response=f"An error occurred: {str(e)}",
            success=False,
            error=str(e),
            session_id=session_id
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

