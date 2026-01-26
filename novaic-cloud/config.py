"""
NovAIC Cloud Service Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
import uuid


class Settings(BaseSettings):
    """Cloud service configuration"""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nbcc"
    
    # JWT
    # NOTE: In open-source mode, do NOT hardcode any real secret in the repo.
    # If not provided, we will generate an ephemeral secret at runtime (dev-friendly),
    # but tokens will be invalid across restarts.
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7
    
    # LLM API (中转站)
    llm_api_key: Optional[str] = None
    llm_api_base: str = "https://api.nuwaapi.com/v1"
    default_model: str = "gpt-4o"
    max_tokens: int = 4096
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # Subscription quotas (tokens per month)
    free_quota: int = 10000
    pro_quota: int = 1000000
    
    class Config:
        env_prefix = "NBCC_"
        env_file = ".env"


settings = Settings()

# Dev-friendly fallback: generate an ephemeral JWT secret if missing.
if not settings.jwt_secret:
    settings.jwt_secret = f"dev-{uuid.uuid4()}"

