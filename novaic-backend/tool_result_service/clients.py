"""
Tool Result Service - 外部服务 HTTP 客户端
"""

import logging
from typing import Optional

import httpx

from .config import FILE_SERVICE_URL, GATEWAY_URL

logger = logging.getLogger(__name__)


class FileServiceClient:
    """File Service HTTP 客户端"""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or FILE_SERVICE_URL).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, trust_env=False)
        return self._client

    async def save_from_base64(
        self,
        data: str,
        agent_id: str,
        category: str,
        mime_type: str = "application/octet-stream",
        subagent_id: Optional[str] = None,
        filename: Optional[str] = None,  # 新增：支持自定义文件名
    ) -> Optional[str]:
        """
        提交 base64 到 File Service，返回 URL 路径（如 /api/files/images/agent-1/xxx.png）
        使用 JSON body，无 multipart 大小限制
        """
        try:
            client = await self._get_client()
            payload = {
                "data": data,
                "agent_id": agent_id,
                "mime_type": mime_type,
                "category": category,
            }
            if subagent_id:
                payload["subagent_id"] = subagent_id
            if filename:
                payload["filename"] = filename

            # 使用 JSON body 而不是 multipart/form-data
            resp = await client.post(
                f"{self.base_url}/api/files/from-base64",
                json=payload,  # ✅ JSON，无大小限制
            )
            resp.raise_for_status()
            result = resp.json()
            url = result.get("url")
            if url:
                return url
            logger.warning(f"[FileServiceClient] No url in response: {result}")
        except Exception as e:
            logger.error(f"[FileServiceClient] save_from_base64 failed: {e}")
        return None

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


class GatewayClient:
    """Gateway HTTP 客户端（用于 create-completed）"""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or GATEWAY_URL).rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0, trust_env=False)
        return self._client

    async def create_completed(
        self,
        tool_name: str,
        truncated_result: str,
        full_output: str,
        agent_id: str,
        ttl_hours: int = 24,
    ) -> Optional[str]:
        """创建已完成任务，存储完整输出，返回 task_id"""
        try:
            client = await self._get_client()
            # Gateway internal API: /internal/tasks/create-completed
            resp = await client.post(
                f"{self.base_url.rstrip('/')}/internal/tasks/create-completed",
                json={
                    "tool_name": tool_name,
                    "truncated_result": truncated_result,
                    "full_output": full_output,
                    "agent_id": agent_id,
                    "ttl_hours": ttl_hours,
                },
            )
            resp.raise_for_status()
            result = resp.json()
            return result.get("task_id")
        except Exception as e:
            logger.warning(f"[GatewayClient] create_completed failed: {e}")
        return None

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
