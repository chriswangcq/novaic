"""
NovAIC Agent Configuration - Multi-Provider LLM Support
"""

from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import Optional, Literal


# ==================== Provider Configs ====================

class OpenAIConfig(BaseModel):
    """OpenAI provider configuration"""
    enabled: bool = False
    api_key: Optional[str] = None
    override_base_url: bool = False
    api_base: Optional[str] = None  # Default: https://api.openai.com/v1


class AnthropicConfig(BaseModel):
    """Anthropic provider configuration"""
    api_key: Optional[str] = None
    # Anthropic uses fixed API base: https://api.anthropic.com


class GoogleConfig(BaseModel):
    """Google AI provider configuration"""
    api_key: Optional[str] = None
    # Google AI uses fixed API base: https://generativelanguage.googleapis.com


class AzureConfig(BaseModel):
    """Azure OpenAI provider configuration"""
    enabled: bool = False
    api_base: Optional[str] = None  # e.g. https://{resource}.openai.azure.com
    deployment_name: Optional[str] = None
    api_key: Optional[str] = None
    api_version: str = "2024-02-01"


class BedrockConfig(BaseModel):
    """AWS Bedrock provider configuration"""
    enabled: bool = False
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    region: str = "us-east-1"
    default_model: Optional[str] = None  # e.g. anthropic.claude-3-5-sonnet-20241022-v2:0


# ==================== Model to Provider Mapping ====================

# 模型名称前缀/关键词到Provider的映射
MODEL_PROVIDER_MAPPING = {
    # OpenAI models
    "gpt-4": "openai",
    "gpt-3.5": "openai",
    "gpt-5": "openai",
    "o1": "openai",
    "o3": "openai",
    "chatgpt": "openai",
    
    # Anthropic models
    "claude": "anthropic",
    
    # Google models
    "gemini": "google",
    "palm": "google",
    
    # Azure (需要显式指定，因为模型名可能和OpenAI相同)
    # Azure通过provider参数显式指定
    
    # 其他OpenAI兼容的模型（如Doubao等）通过默认fallback处理
}


def infer_provider_from_model(model: str, default_provider: str = "openai") -> str:
    """
    根据模型名称推断对应的Provider
    
    Args:
        model: 模型名称
        default_provider: 如果无法推断，使用的默认provider
        
    Returns:
        provider名称: "openai" | "anthropic" | "google" | "azure" | "bedrock"
    """
    if not model:
        return default_provider
    
    model_lower = model.lower()
    
    # 按前缀/关键词匹配
    for prefix, provider in MODEL_PROVIDER_MAPPING.items():
        if prefix in model_lower:
            return provider
    
    # 未匹配到，返回默认provider
    return default_provider


# ==================== Main Settings ====================

class Settings(BaseSettings):
    """Agent configuration settings"""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 19999
    debug: bool = False
    
    # Default LLM Provider: "openai" | "anthropic" | "google" | "azure" | "bedrock"
    default_provider: str = "openai"
    default_model: str = "gpt-4o"
    max_tokens: int = 4096
    
    # Provider configurations (set via runtime, not env)
    # These are initialized empty and populated from InitRequest
    openai_api_key: Optional[str] = None
    openai_override_base_url: bool = False
    openai_api_base: Optional[str] = None
    
    anthropic_api_key: Optional[str] = None
    anthropic_api_base: Optional[str] = None  # Default: https://api.anthropic.com
    
    google_api_key: Optional[str] = None
    google_api_base: Optional[str] = None  # Default: https://generativelanguage.googleapis.com/v1beta
    
    azure_enabled: bool = False
    azure_api_base: Optional[str] = None
    azure_deployment_name: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_api_version: str = "2024-02-01"
    
    
    # Legacy settings (for backward compatibility)
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: Optional[str] = None
    api_style: str = "chat_completions"
    enable_prefix_caching: bool = True
    enable_thinking: bool = False
    
    # Executor Service
    executor_url: str = "http://127.0.0.1:8080"
    
    # Legacy: Execution Settings
    work_dir: str = "/tmp/novaic-workspace"
    upload_dir: str = "/tmp/novaic-uploads"
    max_upload_size: int = 100 * 1024 * 1024
    
    # Timeouts
    command_timeout: int = 300
    llm_timeout: int = 300  # 5 minutes for LLM response (images need more time)
    llm_max_retries: int = 3  # Retry on timeout
    
    # Agent Loop
    max_iterations: int = 20
    
    # Execution Display
    visible_shell: bool = False
    
    class Config:
        env_prefix = "NBCC_"
        env_file = ".env"
    
    def get_provider_config(self, provider: str) -> dict:
        """Get configuration for a specific provider"""
        if provider == "openai":
            return {
                "api_key": self.openai_api_key or self.llm_api_key,
                "api_base": self.openai_api_base if self.openai_override_base_url else "https://api.openai.com/v1",
            }
        elif provider == "anthropic":
            return {
                "api_key": self.anthropic_api_key,
                "api_base": "https://api.anthropic.com",
            }
        elif provider == "google":
            return {
                "api_key": self.google_api_key,
                "api_base": "https://generativelanguage.googleapis.com/v1beta",
            }
        elif provider == "azure":
            return {
                "api_key": self.azure_api_key,
                "api_base": self.azure_api_base,
                "deployment_name": self.azure_deployment_name,
                "api_version": self.azure_api_version,
            }
        elif provider == "bedrock":
            return {
                "access_key_id": self.bedrock_access_key_id,
                "secret_access_key": self.bedrock_secret_access_key,
                "region": self.bedrock_region,
                "default_model": self.bedrock_default_model,
            }
        else:
            # Fallback to legacy OpenAI-compatible
            return {
                "api_key": self.llm_api_key,
                "api_base": self.llm_api_base,
            }


settings = Settings()

