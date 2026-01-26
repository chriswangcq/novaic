"""
API Request/Response Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


# ==================== Init ====================

class InitRequest(BaseModel):
    """Agent initialization request"""
    api_key: Optional[str] = Field(default=None, description="LLM API key (optional if provided via env)")
    api_base: str = Field(
        default="https://api.nuwaapi.com",
        description="LLM API base URL"
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use"
    )
    # API Style settings
    api_style: Optional[str] = Field(
        default=None,
        description="API style: 'chat_completions' (OpenAI) or 'responses' (Doubao)"
    )
    enable_prefix_caching: Optional[bool] = Field(
        default=None,
        description="Enable prefix caching (Doubao only)"
    )
    enable_thinking: Optional[bool] = Field(
        default=None,
        description="Enable thinking mode (Doubao only)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Max tokens for LLM response"
    )
    max_iterations: Optional[int] = Field(
        default=None,
        description="Maximum iterations for agent ReAct loop (default: 20)"
    )
    visible_shell: Optional[bool] = Field(
        default=None,
        description="Show shell execution in GUI terminal (default: false)"
    )


class InitResponse(BaseModel):
    """Agent initialization response"""
    status: str
    message: str


# ==================== Chat ====================

class ChatRequest(BaseModel):
    """Chat request"""
    message: str = Field(..., description="User message")


class ToolUseInfo(BaseModel):
    """Tool use information"""
    tool: str
    input: dict
    output: Optional[str] = None


class ChatResult(BaseModel):
    """Single chat result"""
    type: Literal["text", "thinking", "tool_start", "tool_end", "stdout", "stderr", "progress", "status", "warning", "final", "error"]
    data: Any


class ChatResponse(BaseModel):
    """Chat response (non-streaming)"""
    results: List[ChatResult]


# ==================== Files ====================

class FileUploadResponse(BaseModel):
    """File upload response"""
    status: str
    path: str
    filename: str
    size: int


class FileListResponse(BaseModel):
    """File list response"""
    path: str
    files: List[dict]


# ==================== History ====================

class Message(BaseModel):
    """Chat message"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class HistoryResponse(BaseModel):
    """Chat history response"""
    messages: List[Message]


# ==================== Health ====================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_initialized: bool
    version: str

