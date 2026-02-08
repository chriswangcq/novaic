"""
NovAIC Gateway - API Request/Response Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


# ==================== Chat ====================

class ChatRequest(BaseModel):
    """Chat request"""
    message: str = Field(..., description="User message")
    agent_id: Optional[str] = Field(None, description="Target agent ID (uses current agent if not provided)")
    model: Optional[str] = Field(None, description="Model to use")
    
    # API configuration - optional, uses config defaults if not provided
    provider: Optional[str] = Field(None, description="Provider type")
    api_base: Optional[str] = Field(None, description="API base URL")
    api_key: Optional[str] = Field(None, description="API key")
    api_key_id: Optional[str] = Field(None, description="API key ID from config")


class ChatResult(BaseModel):
    """Single chat result"""
    type: Literal["text", "thinking", "tool_start", "tool_end", "status", "warning", "final", "error", "skills_loaded"]
    data: Any
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response (non-streaming)"""
    results: List[ChatResult]


# ==================== Config ====================

class ApiKeyCreate(BaseModel):
    """Create API key request"""
    provider: str
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None


class ApiKeyUpdate(BaseModel):
    """Update API key request"""
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None


class ModelToggle(BaseModel):
    """Toggle model enabled state"""
    model_id: str
    api_key_id: str
    enabled: bool


class CustomModelAdd(BaseModel):
    """Add custom model request"""
    id: str  # Model ID
    name: Optional[str] = None  # Model name (defaults to id)


class SettingsUpdate(BaseModel):
    """Update settings request"""
    default_model: Optional[str] = None
    max_tokens: Optional[int] = None
    max_iterations: Optional[int] = None
    visible_shell: Optional[bool] = None


# ==================== Health ====================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    agent_initialized: bool
    mcp_healthy: bool
    tools_count: int
    vmcontrol_healthy: Optional[bool] = None


# ==================== History ====================

class Message(BaseModel):
    """Chat message (legacy format for OpenAI-style)"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class ChatHistoryMessage(BaseModel):
    """Chat message from database"""
    id: str
    type: str  # USER_MESSAGE, AGENT_REPLY, etc.
    content: str
    timestamp: str
    read: bool


class HistoryResponse(BaseModel):
    """Chat history response"""
    messages: List[ChatHistoryMessage]


# ==================== WebSocket ====================

class WSMessage(BaseModel):
    """WebSocket message format"""
    type: str  # "chat", "interrupt", "clear", "ping"
    data: Optional[Any] = None
    
    # For chat messages
    message: Optional[str] = None
    model: Optional[str] = None
    api_key_id: Optional[str] = None


class WSEvent(BaseModel):
    """WebSocket event format (server -> client)"""
    type: str  # "text", "thinking", "tool_start", "tool_end", "final", "error", "pong"
    data: Any
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
