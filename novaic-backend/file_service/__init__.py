"""
NovaIC File Service - 独立文件管理服务
"""

from .client import FileServiceClient, create_client
from .config import URL_PREFIX
from .routes import create_router
from .storage import FileStorage

__all__ = [
    "FileServiceClient",
    "FileStorage",
    "create_client",
    "create_router",
    "URL_PREFIX",
]
