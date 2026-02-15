"""
TRS SDK - Tool Result Service 客户端

Create: create_from_raw() 将工具结果推入 TRS，返回 result_id
Consume: to_llm_content() 获取 LLM 可用的内容

normalized 结构（三要素）:
{
    "text": "...",
    "files_created": [{url, filename, modality}, ...],
    "display_files": [{url, filename, modality}, ...]
}
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from common.config import ServiceConfig

logger = logging.getLogger(__name__)


@dataclass
class FileRef:
    """文件引用"""
    url: str
    filename: str
    modality: str  # "image" | "resource"

    def to_dict(self) -> Dict[str, Any]:
        return {"url": self.url, "filename": self.filename, "modality": self.modality}


@dataclass
class ResultMeta:
    """result_id 的元信息"""
    result_id: str
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    created_at: Optional[str] = None
    files_created_count: int = 0
    display_files_count: int = 0


def _get_trs_url() -> str:
    return ServiceConfig.TOOL_RESULT_SERVICE_URL.rstrip("/")


def _parse_tool_result(raw: Any) -> Dict[str, Any]:
    """
    解析工具原始结果为三要素格式。

    支持的输入格式：
    1. 统一格式: {text, files_created, display_files}
    2. 旧格式: {text, files} -> files 作为 display_files
    3. MCP 格式: {content: [{type, text/data}]}
    4. 纯文本: str

    Returns:
        {"text": "...", "files_created": [...], "display_files": [...]}
    """
    if raw is None:
        return {"text": "", "files_created": [], "display_files": []}

    if isinstance(raw, str):
        return {"text": raw, "files_created": [], "display_files": []}

    if not isinstance(raw, dict):
        return {"text": str(raw), "files_created": [], "display_files": []}

    # 解包嵌套的 result 字段
    if "result" in raw and isinstance(raw["result"], dict):
        raw = raw["result"]

    # 1. 统一格式（三要素）
    if "display_files" in raw or "files_created" in raw:
        text_parts = []
        if raw.get("text"):
            text_parts.append(str(raw["text"]))
        # 把 files_created 的 URL 写入文本
        files_created = raw.get("files_created") or []
        if files_created and isinstance(files_created, list):
            urls = [f.get("url") for f in files_created if isinstance(f, dict) and f.get("url")]
            if urls:
                text_parts.append(f"file_url: {urls[0]}" if len(urls) == 1 else f"file_urls: {', '.join(urls)}")
        return {
            "text": "\n".join(text_parts),
            "files_created": files_created,
            "display_files": raw.get("display_files") or [],
        }

    # 2. 旧格式 files 字段（向后兼容）
    if "files" in raw and isinstance(raw["files"], list):
        text_parts = []
        if raw.get("text"):
            text_parts.append(str(raw["text"]))
        files = raw["files"]
        urls = [f.get("url") for f in files if isinstance(f, dict) and f.get("url")]
        if urls:
            text_parts.append(f"file_url: {urls[0]}" if len(urls) == 1 else f"file_urls: {', '.join(urls)}")
        return {
            "text": "\n".join(text_parts),
            "files_created": [],
            "display_files": files,  # 旧 files 作为 display_files
        }

    # 3. MCP 格式 content 数组
    content = raw.get("content") or raw.get("_mcp_content")
    if isinstance(content, list):
        text_parts = []
        display_files = []
        for item in content:
            if not isinstance(item, dict):
                continue
            t = item.get("type", "")
            if t == "text":
                text_parts.append(item.get("text", ""))
            elif t == "image":
                # base64 图片 -> 需要先上传到 File Service（由调用方处理）
                # 这里只记录 URL
                if item.get("url"):
                    display_files.append({
                        "url": item["url"],
                        "filename": "",
                        "modality": "image",
                    })
            elif t == "resource":
                if item.get("url"):
                    display_files.append({
                        "url": item["url"],
                        "filename": "",
                        "modality": "resource",
                    })
        return {
            "text": "\n".join(text_parts),
            "files_created": [],
            "display_files": display_files,
        }

    # 4. 其他 dict：提取 text 字段或序列化
    if raw.get("text"):
        return {"text": str(raw["text"]), "files_created": [], "display_files": []}

    # 5. 兜底：序列化为 JSON
    return {"text": json.dumps(raw, ensure_ascii=False), "files_created": [], "display_files": []}


class TRSClient:
    """
    TRS SDK - 结构化访问

    Example:
        >>> client = TRSClient()
        >>> result_id = client.create_from_raw(raw_result, "agent-1", "screenshot")
        >>> content = client.to_llm_content(result_id, include_display=True)
    """

    def __init__(self, base_url: Optional[str] = None):
        self._base_url = (base_url or _get_trs_url()).rstrip("/")
        self._timeout = 15.0

    # ==================== Create ====================

    def create(
        self,
        agent_id: str,
        tool_name: str = "unknown",
        tool_call_id: Optional[str] = None,
        text: str = "",
        files_created: Optional[List[Dict[str, Any]]] = None,
        display_files: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """
        创建 tool result，直接传入三要素。

        Returns:
            result_id
        """
        with httpx.Client(timeout=self._timeout, trust_env=False) as c:
            r = c.post(f"{self._base_url}/api/create", json={
                "agent_id": agent_id,
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "text": text,
                "files_created": files_created or [],
                "display_files": display_files or [],
            })
            r.raise_for_status()
            return r.json().get("result_id")

    def create_from_raw(
        self,
        raw_result: Any,
        agent_id: str,
        tool_name: str = "unknown",
        tool_call_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        将工具原始返回推入 TRS，返回 result_id。
        自动解析为三要素格式。
        """
        parsed = _parse_tool_result(raw_result)
        return self.create(
            agent_id=agent_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            text=parsed["text"],
            files_created=parsed["files_created"],
            display_files=parsed["display_files"],
        )

    # ==================== Consume ====================

    def to_llm_content(
        self,
        result_id: str,
        provider: str = "openai",
        include_display: bool = True,
    ) -> str:
        """
        转为 LLM 消息格式的 JSON 字符串。

        Args:
            result_id: TRS result_id
            provider: "openai" | "anthropic"
            include_display: 是否包含 display_files 中的图片。
                             True: 当前 round，展示图片
                             False: 历史 round，仅返回文本

        Returns:
            JSON 字符串，格式为 {"_mcp_content": [...]}
        """
        try:
            with httpx.Client(timeout=self._timeout, trust_env=False) as client:
                r = client.get(
                    f"{self._base_url}/api/{result_id}/for-llm",
                    params={"provider": provider, "include_display": str(include_display).lower()},
                )
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            logger.warning(f"[TRSSDK] to_llm_content failed for {result_id}: {e}")
            return json.dumps({"_mcp_content": [{"type": "text", "text": f"[Failed to load result: {e}]"}]})

        content = data.get("content", [])
        # 转换为 _mcp_content 格式
        converted = []
        for item in content:
            t = item.get("type", "text")
            if t == "text":
                converted.append({"type": "text", "text": item.get("text", "")})
            elif t == "image_url":
                # OpenAI 格式 -> 提取 data URL
                img = item.get("image_url", {})
                url = img.get("url", "")
                if url.startswith("data:"):
                    parts = url.split(",", 1)
                    mime = "image/png"
                    if len(parts) >= 1 and ";" in parts[0]:
                        mime = parts[0].split(";")[0].replace("data:", "")
                    data_b64 = parts[1] if len(parts) > 1 else ""
                    converted.append({"type": "image", "data": data_b64, "mimeType": mime})
                else:
                    converted.append({"type": "text", "text": f"[Image: {url}]"})
            elif t == "image":
                # Anthropic 格式
                src = item.get("source", {})
                converted.append({
                    "type": "image",
                    "data": src.get("data", ""),
                    "mimeType": src.get("media_type", "image/png"),
                })
            else:
                converted.append({"type": "text", "text": str(item)})

        return json.dumps({"_mcp_content": converted}, ensure_ascii=False)

    def get_normalized(self, result_id: str) -> Optional[Dict[str, Any]]:
        """获取 normalized 结构（三要素）"""
        try:
            with httpx.Client(timeout=self._timeout, trust_env=False) as client:
                r = client.get(f"{self._base_url}/api/{result_id}")
                r.raise_for_status()
                return r.json().get("normalized")
        except Exception as e:
            logger.warning(f"[TRSSDK] get_normalized failed for {result_id}: {e}")
            return None

    def get_preview(self, result_id: str, max_text_len: int = 500) -> str:
        """文本预览，用于摘要等"""
        try:
            with httpx.Client(timeout=self._timeout, trust_env=False) as client:
                r = client.get(
                    f"{self._base_url}/api/{result_id}/preview",
                    params={"max_text_len": max_text_len},
                )
                r.raise_for_status()
                return r.json().get("summary", "(empty)")
        except Exception as e:
            logger.warning(f"[TRSSDK] get_preview failed for {result_id}: {e}")
            return f"[Failed: {e}]"

    def get_meta(self, result_id: str) -> Optional[ResultMeta]:
        """获取 result 元信息"""
        try:
            with httpx.Client(timeout=self._timeout, trust_env=False) as client:
                r = client.get(f"{self._base_url}/api/{result_id}/preview")
                r.raise_for_status()
                data = r.json()
            return ResultMeta(
                result_id=result_id,
                agent_id=data.get("agent_id"),
                tool_name=data.get("tool_name"),
                created_at=data.get("created_at"),
                files_created_count=data.get("files_created_count", 0),
                display_files_count=data.get("display_files_count", 0),
            )
        except Exception as e:
            logger.warning(f"[TRSSDK] get_meta failed for {result_id}: {e}")
            return None


# 默认单例
_default_client: Optional[TRSClient] = None


def get_trs_client(base_url: Optional[str] = None) -> TRSClient:
    """获取 TRS 客户端。base_url 非空时返回一次性实例；否则返回默认单例。"""
    global _default_client
    if base_url is not None:
        return TRSClient(base_url)
    if _default_client is None:
        _default_client = TRSClient()
    return _default_client
