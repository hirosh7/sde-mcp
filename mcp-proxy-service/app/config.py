"""Configuration management for MCP Proxy Service"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    # MCP Server URL
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001/mcp")
    
    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")
    # Tool selection model (can be different from formatting model for cost optimization)
    CLAUDE_TOOL_SELECTION_MODEL = os.getenv("CLAUDE_TOOL_SELECTION_MODEL", "claude-3-5-haiku-20241022")
    
    # Performance
    ENABLE_TIMING = os.getenv("ENABLE_TIMING", "false").lower() in ("true", "1", "yes")
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8002"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

