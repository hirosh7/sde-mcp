"""Pydantic models for request/response validation"""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for natural language query"""
    query: str = Field(..., description="Natural language query", min_length=1)


class QueryResponse(BaseModel):
    """Response model for query result"""
    response: str = Field(..., description="Formatted natural language response")
    success: bool = Field(..., description="Whether the query was successful")
    tool_name: str | None = Field(None, description="Name of the tool that was called")
    error: str | None = Field(None, description="Error message if unsuccessful")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(default="healthy")
    service: str = Field(default="mcp-proxy")
    mcp_server_connected: bool = Field(default=False)

