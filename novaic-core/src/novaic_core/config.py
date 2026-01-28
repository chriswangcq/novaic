"""
NovAIC Configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings"""
    
    # Server - 只绑定本地，外部通过 VSOCK 代理访问
    host: str = "127.0.0.1"
    port: int = 8080
    
    # Work directory
    work_dir: str = "/tmp/novaic-work"
    
    # Browser settings
    browser_headless: bool = False
    browser_timeout: int = 30000  # ms
    
    # Execution settings
    default_timeout: int = 60  # seconds
    
    class Config:
        env_prefix = "NOVAIC_"


settings = Settings()

