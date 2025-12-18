"""Mock Seaglass Service - Simulates Seaglass for prototype testing"""
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Mock Seaglass Service")

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MCP_PROXY_URL = os.getenv("MCP_PROXY_URL", "http://localhost:8002")


class NLQueryRequest(BaseModel):
    query: str


class NLQueryResponse(BaseModel):
    response: str
    success: bool
    error: str | None = None


@app.get("/api/v1/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mock-seaglass"}


@app.get("/api/v1/sde-instance")
async def get_sde_instance():
    """Get SDE instance information"""
    try:
        # Try to get SDE instance info from MCP proxy
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_PROXY_URL}/api/v1/sde-instance")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    
    # Fallback: return unknown
    return {"instance_name": "Unknown", "instance_url": "Unknown"}


@app.post("/api/v1/nlquery", response_model=NLQueryResponse)
async def natural_language_query(request: NLQueryRequest):
    """Forward natural language query to MCP Proxy"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MCP_PROXY_URL}/api/v1/query",
                json={"query": request.query}
            )
            response.raise_for_status()
            data = response.json()
            return NLQueryResponse(
                response=data.get("response", ""),
                success=data.get("success", False),
                error=data.get("error")
            )
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        return NLQueryResponse(
            response="",
            success=False,
            error=error_msg
        )
    except httpx.TimeoutException:
        return NLQueryResponse(
            response="",
            success=False,
            error="Request timeout - MCP Proxy service did not respond in time"
        )
    except Exception as e:
        return NLQueryResponse(
            response="",
            success=False,
            error=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

