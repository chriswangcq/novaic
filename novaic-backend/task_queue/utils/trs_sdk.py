"""
TRS SDK - 创建与消费 Tool Result 的统一入口

Create: create_from_raw() 将工具原始结果推入 TRS，返回 result_id
Consume: get_content_list()、get_types()、get_texts()、get_preview()、to_llm_content()
各场景统一通过 SDK 访问，按需获取。
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx

from common.config import ServiceConfig

logger = logging.getLogger(__name__)


ContentType = Literal["text", "image", "resource"]


@dataclass
class ContentItem:
    """
    TRS 中的单条 content 项。
    
    type: "text" | "image" | "resource"
    根据 type 不同，有效字段不同：
    - text: text
    - image: data (base64), mime_type; 或 url (未 resolve 时)
    - resource: data, mime_type; 或 url
    """

    type: Literal["text", "image", "resource"]
    index: int = 0

    # text 类型
    text: Optional[str] = None

    # image / resource 类型（resolve 后）
    data: Optional[str] = None  # base64
    mime_type: Optional[str] = None

    # image / resource 未 resolve 时（仅 URL）
    url: Optional[str] = None

    # 原始项，保留以备需要
    raw: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        """转为 dict，便于序列化"""
        d = {"type": self.type, "index": self.index}
        if self.text is not None:
            d["text"] = self.text
        if self.data is not None:
            d["data"] = self.data
        if self.mime_type is not None:
            d["mime_type"] = self.mime_type
        if self.url is not None:
            d["url"] = self.url
        return d


@dataclass
class ResultMeta:
    """result_id 的元信息"""
    result_id: str
    agent_id: Optional[str] = None
    tool_name: Optional[str] = None
    created_at: Optional[str] = None
    content_count: int = 0


def _get_trs_url() -> str:
    return ServiceConfig.TOOL_RESULT_SERVICE_URL.rstrip("/")


def _parse_raw_to_items(raw: Any) -> List[Tuple[str, Dict[str, Any]]]:
    """
    解析 raw tool result 为 (type, item) 列表。
    type: text | image | resource
    """
    from . import multimodal

    items: List[Tuple[str, Dict[str, Any]]] = []

    def add_inner(inner: Any):
        if inner is None:
            return
        if isinstance(inner, str):
            items.append(("text", {"text": inner}))
            return
        if isinstance(inner, list):
            for x in inner:
                add_inner(x)
            return
        if not isinstance(inner, dict):
            items.append(("text", {"text": str(inner)}))
            return

        if "result" in inner and isinstance(inner["result"], (dict, list, str)):
            add_inner(inner["result"])
            return

        t = inner.get("type")
        if t == "text":
            items.append(("text", {"text": inner.get("text", "")}))
            return
        if t == "image" and inner.get("data"):
            items.append(("image", {"data": inner["data"], "mimeType": inner.get("mimeType", "image/png")}))
            return
        if t == "resource":
            res = inner.get("resource", inner)
            blob = res.get("blob") if isinstance(res, dict) else None
            if blob:
                items.append(("resource", {"data": blob, "mimeType": (res or {}).get("mimeType", "application/octet-stream")}))
                return

        content = inner.get("content") or inner.get("_mcp_content")
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                t = item.get("type", "")
                if t == "text":
                    items.append(("text", {"text": item.get("text", "")}))
                elif t == "image":
                    data = item.get("data")
                    if data:
                        items.append(("image", {"data": data, "mimeType": item.get("mimeType", "image/png")}))
                elif t == "resource":
                    res = item.get("resource", {})
                    blob = res.get("blob")
                    if blob:
                        items.append(("resource", {"data": blob, "mimeType": res.get("mimeType", "application/octet-stream")}))
                    elif item.get("text"):
                        items.append(("text", {"text": item.get("text", "")}))
                else:
                    items.append(("text", {"text": json.dumps(item, ensure_ascii=False)}))
            return

        for field in multimodal.IMAGE_FIELD_NAMES:
            val = inner.get(field)
            if val and multimodal.has_images({field: val}):
                mime = "image/jpeg" if "jpeg" in field or "jpg" in field else "image/png"
                items.append(("image", {"data": val, "mimeType": mime}))
                break
        else:
            text_parts = []
            for k, v in inner.items():
                if k in ("result", "content", "_mcp_content") or k in multimodal.IMAGE_FIELD_NAMES:
                    continue
                if isinstance(v, str) and len(v) > 10000:
                    continue
                text_parts.append(f"{k}: {v}" if v is not None else k)
            if text_parts:
                items.append(("text", {"text": "\n".join(text_parts)}))

    add_inner(raw)
    return items


class TRSClient:
    """
    TRS SDK - 结构化访问
    
    Example:
        >>> client = TRSClient()
        >>> items = client.get_content_list("res_xxx")
        >>> for item in items:
        ...     print(item.type, item.text or item.data or item.url)
        >>> types = client.get_types("res_xxx")
        >>> texts = client.get_texts("res_xxx")
    """

    def __init__(self, base_url: Optional[str] = None):
        self._base_url = (base_url or _get_trs_url()).rstrip("/")
        self._timeout = 15.0

    # ==================== Create ====================

    def create_from_raw(
        self,
        raw_result: Any,
        agent_id: str,
        tool_name: str = "unknown",
        tool_call_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        将工具原始返回推入 TRS，返回 result_id。
        用于 Tools Server 在工具执行后创建。
        """
        items = _parse_raw_to_items(raw_result)
        if not items:
            items = [(
                "text",
                {"text": json.dumps(raw_result, ensure_ascii=False) if not isinstance(raw_result, str) else str(raw_result)},
            )]
        return self._create_from_items(items, agent_id, tool_name, tool_call_id)

    def _create_from_items(
        self,
        items: List[Tuple[str, Dict[str, Any]]],
        agent_id: str,
        tool_name: str,
        tool_call_id: Optional[str],
    ) -> Optional[str]:
        with httpx.Client(timeout=self._timeout, trust_env=False) as c:
            r = c.post(f"{self._base_url}/api/create", json={
                "agent_id": agent_id,
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
            })
            r.raise_for_status()
            result_id = r.json().get("result_id")
            if not result_id:
                raise ValueError(f"[TRSSDK] create returned no result_id")

            for typ, item in items:
                if typ == "text":
                    r2 = c.post(f"{self._base_url}/api/{result_id}/insert/text", json={"text": item.get("text", "")})
                elif typ == "image":
                    r2 = c.post(f"{self._base_url}/api/{result_id}/insert/image", json={
                        "data": item.get("data"),
                        "mimeType": item.get("mimeType", "image/png"),
                    })
                else:
                    r2 = c.post(f"{self._base_url}/api/{result_id}/insert/resource", json={
                        "data": item.get("data"),
                        "mimeType": item.get("mimeType", "application/octet-stream"),
                    })
                r2.raise_for_status()
            return result_id

    # ==================== Consume ====================

    def to_llm_content(
        self,
        result_id: str,
        provider: str = "openai",
    ) -> str:
        """
        转为 process_multimodal_messages 期望的 JSON 字符串。
        用于 LLM 调用前 expand tool 消息。
        """
        items = self._fetch_for_llm(result_id, provider)
        converted = []
        for it in items:
            if it.type == "text":
                converted.append({"type": "text", "text": it.text or ""})
            elif it.type == "image" and it.data:
                converted.append({"type": "image", "data": it.data, "mimeType": it.mime_type or "image/png"})
            else:
                converted.append({"type": "text", "text": str(it.raw or it)})
        return json.dumps({"_mcp_content": converted}, ensure_ascii=False)

    def get_content_list(
        self,
        result_id: str,
        *,
        resolve_images: bool = True,
        provider: str = "openai",
    ) -> List[ContentItem]:
        """
        获取 content 列表，每个 item 包含 type 及对应字段。

        Args:
            result_id: TRS result_id
            resolve_images: 是否将图片 URL 解析为 base64（默认 True，调用 /for-llm）
            provider: openai | anthropic，resolve 时使用

        Returns:
            ContentItem 列表
        """
        if resolve_images:
            return self._fetch_for_llm(result_id, provider)
        return self._fetch_raw(result_id)

    def _fetch_raw(self, result_id: str) -> List[ContentItem]:
        """GET /{result_id} 原始 normalized"""
        try:
            with httpx.Client(timeout=self._timeout, trust_env=False) as client:
                r = client.get(f"{self._base_url}/api/{result_id}")
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            logger.warning(f"[TRSSDK] get_content_list raw failed for {result_id}: {e}")
            return []

        normalized = data.get("normalized", {})
        content = normalized.get("content", [])
        items = []
        for i, raw in enumerate(content):
            t = raw.get("type", "text")
            if t == "text":
                items.append(ContentItem(
                    type="text",
                    index=i,
                    text=raw.get("text", ""),
                    raw=dict(raw),
                ))
            elif t == "image":
                items.append(ContentItem(
                    type="image",
                    index=i,
                    url=raw.get("url"),
                    mime_type=raw.get("mimeType"),
                    raw=dict(raw),
                ))
            elif t == "resource":
                items.append(ContentItem(
                    type="resource",
                    index=i,
                    url=raw.get("url"),
                    mime_type=raw.get("mimeType"),
                    raw=dict(raw),
                ))
            else:
                items.append(ContentItem(
                    type="text",
                    index=i,
                    text=str(raw),
                    raw=dict(raw) if isinstance(raw, dict) else None,
                ))
        return items

    def _fetch_for_llm(self, result_id: str, provider: str) -> List[ContentItem]:
        """GET /{result_id}/for-llm 含 base64 图片"""
        try:
            with httpx.Client(timeout=self._timeout, trust_env=False) as client:
                r = client.get(
                    f"{self._base_url}/api/{result_id}/for-llm",
                    params={"provider": provider},
                )
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            logger.warning(f"[TRSSDK] get_content_list for_llm failed for {result_id}: {e}")
            return []

        content = data.get("content", [])
        items = []
        for i, raw in enumerate(content):
            t = raw.get("type", "text")
            if t == "text":
                items.append(ContentItem(
                    type="text",
                    index=i,
                    text=raw.get("text", ""),
                    raw=dict(raw),
                ))
            elif t == "image_url":
                img = raw.get("image_url", {})
                url = img.get("url", "")
                data_b64 = ""
                mime = "image/png"
                if url.startswith("data:"):
                    parts = url.split(",", 1)
                    if len(parts) >= 1 and ";" in parts[0]:
                        mime = parts[0].split(";")[0].replace("data:", "")
                    data_b64 = parts[1] if len(parts) > 1 else ""
                items.append(ContentItem(
                    type="image",
                    index=i,
                    data=data_b64,
                    mime_type=mime,
                    raw=dict(raw),
                ))
            elif t == "image":
                src = raw.get("source", {})
                items.append(ContentItem(
                    type="image",
                    index=i,
                    data=src.get("data", ""),
                    mime_type=src.get("media_type", "image/png"),
                    raw=dict(raw),
                ))
            else:
                items.append(ContentItem(
                    type="text",
                    index=i,
                    text=str(raw),
                    raw=dict(raw) if isinstance(raw, dict) else None,
                ))
        return items

    def get_types(self, result_id: str) -> List[str]:
        """仅获取 type 列表，轻量（不 resolve 图片）"""
        items = self.get_content_list(result_id, resolve_images=False)
        return [it.type for it in items]

    def get_texts(self, result_id: str) -> List[str]:
        """仅提取 text 类型内容"""
        items = self.get_content_list(result_id, resolve_images=False)
        return [it.text or "" for it in items if it.type == "text"]

    def get_preview(self, result_id: str, max_text_len: int = 500) -> str:
        """文本预览，用于摘要等"""
        try:
            with httpx.Client(timeout=10.0, trust_env=False) as client:
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
                content_count=data.get("content_count", 0),
            )
        except Exception as e:
            logger.warning(f"[TRSSDK] get_meta failed for {result_id}: {e}")
            return None


# 默认单例，便于直接使用
_default_client: Optional[TRSClient] = None


def get_trs_client(base_url: Optional[str] = None) -> TRSClient:
    """获取 TRS 客户端。base_url 非空时返回一次性实例；否则返回默认单例。"""
    global _default_client
    if base_url is not None:
        return TRSClient(base_url)
    if _default_client is None:
        _default_client = TRSClient()
    return _default_client
