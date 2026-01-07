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
    # Default to Sonnet 4.5 for both formatting and tool selection (better context understanding)
    # Claude 4.5 Sonnet format: claude-sonnet-4-5-YYYYMMDD (note: different from 3.5 format)
    _claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    CLAUDE_MODEL = _claude_model
    # Tool selection model (can be different from formatting model for cost optimization)
    # Defaults to same as CLAUDE_MODEL if not specified
    CLAUDE_TOOL_SELECTION_MODEL = os.getenv("CLAUDE_TOOL_SELECTION_MODEL", _claude_model)
    
    # Performance
    ENABLE_TIMING = os.getenv("ENABLE_TIMING", "false").lower() in ("true", "1", "yes")
    # Claude formatting timeout (in seconds) - increased for longer responses
    CLAUDE_FORMATTER_TIMEOUT = float(os.getenv("CLAUDE_FORMATTER_TIMEOUT", "60.0"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8002"))
    
    # Redis Configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
    SESSION_MAX_CONVERSATIONS = int(os.getenv("SESSION_MAX_CONVERSATIONS", "50"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

