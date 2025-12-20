# Context Retention System Implementation

## Problem

The MCP proxy service currently processes each query independently with no memory of previous operations. When a tool execution mentions information (like "answers were deselected"), that context is lost for follow-up queries.

## Solution Overview

Implement per-session context retention that:
1. Stores session context in Docker MinIO (S3-compatible object storage)
2. Retrieves and provides conversation history to Claude on each query
3. Enables Claude to respond with awareness of previous questions and answers

## Architecture

```mermaid
sequenceDiagram
    participant User
    participant Proxy as MCP Proxy
    participant MinIO as MinIO Storage
    participant Claude as Claude API
    participant MCP as MCP Server

    User->>Proxy: Query 1 (session_id: abc123)
    Proxy->>MinIO: Retrieve session context (if exists)
    MinIO-->>Proxy: Previous Q&A history
    Proxy->>Claude: Query + Conversation History
    Claude-->>Proxy: Tool selection
    Proxy->>MCP: Execute tool
    MCP-->>Proxy: Result
    Proxy->>Claude: Format result + History
    Claude-->>Proxy: Formatted response
    Proxy->>MinIO: Store Q&A pair
    Proxy-->>User: Response + session_id

    User->>Proxy: Query 2 (session_id: abc123)
    Proxy->>MinIO: Retrieve session context
    MinIO-->>Proxy: Previous Q&A history
    Note over Proxy: Claude now knows previous context
    Proxy->>Claude: Query + Full Conversation History
    Claude-->>Proxy: Context-aware response
```

## Implementation Steps

### 1. Add MinIO to Docker Compose

**File: `docker-compose.yml`**

Add MinIO service:
```yaml
  # MinIO - Object storage for session context
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio-data:/data
    networks:
      - app-network
    restart: unless-stopped

volumes:
  minio-data:
```

Update `mcp-proxy` service to include MinIO environment variables:
```yaml
    environment:
      - MINIO_ENDPOINT=http://minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
      - MINIO_BUCKET_NAME=sessions
    depends_on:
      - sde-mcp-server
      - minio
```

### 2. Create MinIO Storage Client

**File: `mcp-proxy-service/app/minio_client.py`** (new)

Create MinIO client wrapper for session storage:
```python
from minio import Minio
from minio.error import S3Error
import json
import io
from typing import Optional, Dict
from datetime import datetime

class MinIOSessionStorage:
    """Store and retrieve session context from MinIO"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str):
        self.client = Minio(
            endpoint.replace("http://", "").replace("https://", ""),
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
    
    def save_session_context(self, session_id: str, context: Dict) -> None:
        """Save session context to MinIO"""
        object_name = f"{session_id}/context.json"
        data = json.dumps(context, default=str).encode('utf-8')
        self.client.put_object(
            self.bucket_name,
            object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type='application/json'
        )
    
    def get_session_context(self, session_id: str) -> Optional[Dict]:
        """Retrieve session context from MinIO"""
        object_name = f"{session_id}/context.json"
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = json.loads(response.read())
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            raise
    
    def append_conversation(self, session_id: str, query: str, response: str, metadata: Dict) -> None:
        """Append Q&A pair to session conversation history"""
        context = self.get_session_context(session_id) or {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "conversations": []
        }
        
        context["conversations"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata
        })
        
        # Keep last 50 conversations per session
        if len(context["conversations"]) > 50:
            context["conversations"] = context["conversations"][-50:]
        
        context["updated_at"] = datetime.utcnow().isoformat()
        self.save_session_context(session_id, context)
```

### 3. Update Configuration

**File: `mcp-proxy-service/app/config.py`**

Add MinIO configuration:
```python
    # MinIO Configuration
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "sessions")
    
    # Session Configuration
    SESSION_MAX_CONVERSATIONS = int(os.getenv("SESSION_MAX_CONVERSATIONS", "50"))
```

### 4. Update Models

**File: `mcp-proxy-service/app/models.py`**

Add session_id to request/response:
```python
from typing import Optional

class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for context retention")

class QueryResponse(BaseModel):
    response: str = Field(..., description="Formatted natural language response")
    success: bool = Field(..., description="Whether the query was successful")
    session_id: str = Field(..., description="Session ID for this conversation")
    tool_name: str | None = Field(None, description="Name of the tool that was called")
    error: str | None = Field(None, description="Error message if unsuccessful")
```

### 5. Modify Claude Adapter for Conversation History

**File: `mcp-proxy-service/app/claude_adapter.py`**

Update `select_tool` method to accept and use conversation history:
```python
from typing import List, Dict, Optional

async def select_tool(
    self, 
    query: str, 
    available_tools: list,
    conversation_history: Optional[List[Dict]] = None
) -> Tuple[str, dict]:
    """Use Claude to determine which tool to call with conversation context"""
    
    # Build messages list with conversation history
    messages = []
    
    # Add previous conversation history
    if conversation_history:
        for conv in conversation_history:
            messages.append({
                "role": "user",
                "content": conv.get("query", "")
            })
            messages.append({
                "role": "assistant",
                "content": conv.get("response", "")
            })
    
    # Add current query
    tools_description = self._format_tools_for_claude(available_tools)
    user_prompt = f"""Available tools:
{tools_description}

User query: {query}

Respond with JSON only:"""
    
    messages.append({"role": "user", "content": user_prompt})
    
    # Update system prompt to mention context awareness
    system_prompt = """You are a tool selector for SD Elements operations.
You have access to the conversation history above, which shows previous questions and answers in this session.
Use this context to better understand follow-up questions and references to previous operations.

Given a user's natural language query, determine which tool should be called and with what arguments.

CRITICAL TOOL SELECTION RULES:

1. LIST vs CREATE REPORT (MOST IMPORTANT):
   - If the query asks to "list", "show", "get", "find", or "display" items → Use list_* tools
   - If the query explicitly asks to "create a report" or "generate a report" → Use create_advanced_report
   - NEVER use create_advanced_report for simple list queries, even if filtering is needed
   - For filtered lists (e.g., "projects that are not risk compliant"), use list_projects and filter results client-side
   - Examples:
     * "list projects that are not risk compliant" → list_projects (NOT create_advanced_report)
     * "show me all business units" → list_business_units
     * "create a risk compliance report" → create_advanced_report
     * "list projects created this month" → list_projects

2. TOOL PRIORITY:
   - Prefer list_* tools for retrieval queries (list, show, get all, find all)
   - Only use create_* tools when explicitly creating something new (create project, create report)
   - Use get_* tools for single item retrieval by ID (get project 123)
   - Use update_* tools for modifying existing items
   - Use delete_* tools for removing items

3. CONTEXT AWARENESS:
   - If the user references a previous operation (e.g., "the project I just created", "those answers"), use the conversation history to understand what they're referring to
   - For follow-up questions, consider what tool was used in previous queries to maintain context

4. You must respond with ONLY a JSON object in this exact format:
{
    "tool_name": "name_of_tool",
    "arguments": {
        "arg1": "value1",
        "arg2": "value2"
    }
}

5. If no tool matches the query, return:
{
    "tool_name": null,
    "arguments": {},
    "error": "No matching tool found"
}

6. Only provide arguments that are explicitly mentioned in the query or that you can reasonably infer. Do not make up values for required parameters unless you can infer them."""
    
    response = self.anthropic.messages.create(
        model=self.tool_selection_model,
        max_tokens=1000,
        system=system_prompt,
        messages=messages
    )
    # ... rest of existing code for parsing response
```

### 6. Modify Claude Formatter for Conversation History

**File: `mcp-proxy-service/app/claude_formatter.py`**

Update `format_result` method to include conversation history:
```python
from typing import List, Dict, Optional

async def format_result(
    self, 
    tool_name: str, 
    result: Dict[str, Any], 
    original_query: str,
    conversation_history: Optional[List[Dict]] = None
) -> str:
    """Format result with conversation context"""
    
    # Build messages with history
    messages = []
    
    if conversation_history:
        for conv in conversation_history:
            messages.append({
                "role": "user",
                "content": conv.get("query", "")
            })
            messages.append({
                "role": "assistant",
                "content": conv.get("response", "")
            })
    
    # Add current formatting request
    result_json = json.dumps(result, indent=2)
    user_prompt = f"""Tool: {tool_name}
Original user query: {original_query}

Tool result (JSON):
{result_json}

Format this result into natural language. Consider the conversation history above for context:"""
    
    messages.append({"role": "user", "content": user_prompt})
    
    # Update system prompt
    system_prompt = """You are a response formatter for SD Elements operations.
You have access to the conversation history above. Use this context to provide more relevant and contextual responses.

Guidelines:
- Be concise but informative
- Highlight key information (IDs, names, URLs, status)
- For lists, show count and key details for each item
- For errors, clearly explain what went wrong
- Use a friendly, professional tone
- Format dates/timestamps in a readable way
- Include relevant URLs when available
- Reference previous operations when relevant (e.g., "As mentioned earlier, 3 answers were deselected")

Respond with ONLY the formatted natural language text, no additional commentary."""
    
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: self.anthropic.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=messages
        )
    )
    
    return response.content[0].text
```

### 7. Update Main Application

**File: `mcp-proxy-service/app/main.py`**

Modify `/api/v1/query` endpoint:
```python
from app.minio_client import MinIOSessionStorage
import uuid

# Initialize MinIO storage in lifespan
minio_storage: MinIOSessionStorage | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_client, claude_selector, claude_formatter, fallback_formatter, minio_storage
    
    # ... existing initialization ...
    
    # Initialize MinIO storage
    minio_storage = MinIOSessionStorage(
        endpoint=Config.MINIO_ENDPOINT,
        access_key=Config.MINIO_ACCESS_KEY,
        secret_key=Config.MINIO_SECRET_KEY,
        bucket_name=Config.MINIO_BUCKET_NAME
    )
    logger.info(f"Initialized MinIO storage at {Config.MINIO_ENDPOINT}")

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    # Generate or use provided session_id
    session_id = request.session_id or str(uuid.uuid4())
    
    # Retrieve conversation history from MinIO
    session_context = minio_storage.get_session_context(session_id) if minio_storage else None
    conversation_history = session_context.get("conversations", []) if session_context else []
    
    # Get available tools
    tools = await mcp_client.get_tools()
    
    if not tools:
        return QueryResponse(
            response="No tools available from MCP server",
            success=False,
            error="No tools available",
            session_id=session_id
        )
    
    # Pass conversation history to Claude selector
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
    
    # Pass conversation history to Claude formatter
    try:
        formatted_response = await claude_formatter.format_result(
            tool_name=tool_name,
            result=result,
            original_query=request.query,
            conversation_history=conversation_history
        )
    except Exception as e:
        logger.warning(f"Claude formatting failed, using fallback: {e}")
        formatted_response = fallback_formatter.format_tool_result(tool_name, result)
    
    # Store conversation in MinIO
    if minio_storage:
        minio_storage.append_conversation(
            session_id=session_id,
            query=request.query,
            response=formatted_response,
            metadata={
                "tool_name": tool_name,
                "success": True
            }
        )
    
    return QueryResponse(
        response=formatted_response,
        success=True,
        session_id=session_id,
        tool_name=tool_name
    )
```

### 8. Add Dependencies

**File: `mcp-proxy-service/requirements.txt`**

Add MinIO client:
```
minio>=7.2.0
```

### 9. Update Environment Example

**File: `env.example`**

Add MinIO configuration:
```
# MinIO Configuration (for session context storage)
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=sessions
SESSION_MAX_CONVERSATIONS=50
```

## Key Changes Summary

1. **MinIO Integration**: Replace in-memory storage with persistent MinIO object storage
2. **Conversation History**: Store Q&A pairs per session in MinIO
3. **Claude Context**: Pass conversation history to both tool selection and response formatting
4. **Session Management**: Generate/use session_id, retrieve context before each query
5. **Persistent Storage**: Context survives service restarts via MinIO

## Benefits

- **Persistent Context**: Survives service restarts
- **Scalable Storage**: MinIO handles large volumes of session data
- **Context-Aware Responses**: Claude understands previous Q&A
- **Session Isolation**: Each session maintains its own conversation history
- **Docker-Based**: Easy to deploy and manage with docker-compose

## Example Usage

**First Query:**
```
User: "Add C++ and Python answers to project 123 survey"
Response: "Added 8 answers to the survey. 3 conflicting answers were automatically deselected."
Session ID: abc123
```

**Follow-up Query (using same session):**
```
User: "What answers were deselected?"
→ Claude receives conversation history showing previous query and response
→ Claude understands the context and can reference the deselected answers
Response: "The following answers were deselected: A2297 (Java), A2298 (Ruby), A2304 (Go)"
```

## Files to Modify

1. **New Files:**
   - `mcp-proxy-service/app/minio_client.py` (MinIO storage client)

2. **Modified Files:**
   - `docker-compose.yml` (add MinIO service)
   - `mcp-proxy-service/app/models.py` (add session_id fields)
   - `mcp-proxy-service/app/main.py` (integrate MinIO, pass context to Claude)
   - `mcp-proxy-service/app/config.py` (add MinIO config)
   - `mcp-proxy-service/app/claude_adapter.py` (accept conversation_history)
   - `mcp-proxy-service/app/claude_formatter.py` (accept conversation_history)
   - `mcp-proxy-service/requirements.txt` (add minio package)
   - `env.example` (add MinIO configuration)

## Testing Strategy

1. Start MinIO service: `docker-compose up minio`
2. Test session creation and storage
3. Test conversation history retrieval
4. Verify Claude receives and uses conversation history
5. Test session isolation (different sessions don't interfere)
6. Test persistence across service restarts

## Future Enhancements

- Session expiration/TTL cleanup
- Session sharing across multiple users (with authentication)
- Export session history for audit/debugging
- Session search and analytics
- Compression for large conversation histories
