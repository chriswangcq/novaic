"""
API Request/Response Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Literal
from datetime import datetime


# ==================== Provider Configs ====================

class OpenAIProviderConfig(BaseModel):
    """OpenAI provider configuration"""
    enabled: bool = False
    api_key: Optional[str] = None
    override_base_url: bool = False
    api_base: Optional[str] = None


class AnthropicProviderConfig(BaseModel):
    """Anthropic provider configuration"""
    api_key: Optional[str] = None
    api_base: Optional[str] = None  # Default: https://api.anthropic.com


class GoogleProviderConfig(BaseModel):
    """Google AI provider configuration"""
    api_key: Optional[str] = None
    api_base: Optional[str] = None  # Default: https://generativelanguage.googleapis.com/v1beta


class AzureProviderConfig(BaseModel):
    """Azure OpenAI provider configuration"""
    enabled: bool = False
    api_base: Optional[str] = None
    deployment_name: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = "2024-02-01"


# ==================== Init ====================

class InitRequest(BaseModel):
    """Agent initialization request - supports multiple LLM providers"""
    
    # Provider selection: "openai" | "anthropic" | "google" | "azure" | "bedrock"
    provider: str = Field(
        default="openai",
        description="LLM provider to use"
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use"
    )
    
    # Provider-specific configurations
    openai: Optional[OpenAIProviderConfig] = Field(default=None)
    anthropic: Optional[AnthropicProviderConfig] = Field(default=None)
    google: Optional[GoogleProviderConfig] = Field(default=None)
    azure: Optional[AzureProviderConfig] = Field(default=None)
    
    # Common settings
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
    
    # Legacy fields (for backward compatibility)
    api_key: Optional[str] = Field(default=None, description="[Legacy] LLM API key")
    api_base: Optional[str] = Field(default=None, description="[Legacy] LLM API base URL")
    api_style: Optional[str] = Field(default=None, description="[Legacy] API style")
    enable_prefix_caching: Optional[bool] = Field(default=None, description="[Legacy] Enable prefix caching")
    enable_thinking: Optional[bool] = Field(default=None, description="[Legacy] Enable thinking mode")


class InitResponse(BaseModel):
    """Agent initialization response"""
    status: str
    message: str


# ==================== Chat ====================

class ChatRequest(BaseModel):
    """Chat request"""
    message: str = Field(..., description="User message")
    model: Optional[str] = Field(None, description="Model to use for this request")
    mode: Optional[str] = Field("agent", description="Chat mode: 'agent' or 'chat'")


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

