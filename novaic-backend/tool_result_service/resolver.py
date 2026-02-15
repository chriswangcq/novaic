"""
Tool Result Service - URL 解析
调用 File Service 将 URL 转为 base64
"""

import logging
from typing import Optional

import httpx

from .config import FILE_SERVICE_URL

logger = logging.getLogger(__name__)


async def resolve_url_to_base64(url: str) -> Optional[str]:
    """
    将 File Service URL 解析为 base64。
    url 可为相对路径 /api/files/... 或完整 URL。
    """
    base = FILE_SERVICE_URL.rstrip("/")
    if url.startswith("/"):
        fetch_url = f"{base}{url}"
    elif url.startswith("http"):
        fetch_url = url
    else:
        fetch_url = f"{base}/api/files/{url.lstrip('/')}"

    try:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            resp = await client.get(fetch_url)
            resp.raise_for_status()
            import base64
            return base64.b64encode(resp.content).decode("utf-8")
    except Exception as e:
        logger.warning(f"[Resolver] resolve_url_to_base64 failed: {e}")
    return None
