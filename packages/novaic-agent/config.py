"""
NovAIC Agent Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Agent configuration settings"""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 9000  # Agent 端口 (宿主机本地)
    debug: bool = False
    
    # LLM API Settings
    llm_api_base: str = "https://api.nuwaapi.com"
    llm_api_key: Optional[str] = None
    
    # LLM Settings
    default_model: str = "gpt-5"
    max_tokens: int = 4096
    
    # API Style: "chat_completions" (OpenAI) or "responses" (Doubao)
    api_style: str = "chat_completions"
    
    # Doubao-specific settings (only used when api_style="responses")
    enable_prefix_caching: bool = True
    enable_thinking: bool = False
    
    # Executor Service (执行代理)
    executor_url: str = "http://127.0.0.1:8080"  # MCP Server (VM 内) 端口
    
    # Legacy: Execution Settings
    work_dir: str = "/tmp/novaic-workspace"
    upload_dir: str = "/tmp/novaic-uploads"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    
    # Timeouts
    command_timeout: int = 300  # 5 minutes
    llm_timeout: int = 120  # 2 minutes
    
    # Agent Loop
    max_iterations: int = 20  # Maximum iterations for ReAct loop
    
    # Execution Display
    visible_shell: bool = False  # Show shell execution in GUI terminal
    
    class Config:
        env_prefix = "NBCC_"
        env_file = ".env"


settings = Settings()

