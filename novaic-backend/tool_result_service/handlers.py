"""
Tool Result Service - HTTP 路由
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .clients import FileServiceClient
from .config import (
    FILE_SERVICE_URL,
    get_category_for_mime,
    TEXT_HEAD_TAIL_SIZE,
    TEXT_REFERENCE_ONLY_THRESHOLD,
    TEXT_TRUNCATE_THRESHOLD,
)


def _head_tail_truncate(
    text: str,
    head_size: int = TEXT_HEAD_TAIL_SIZE,
    tail_size: int = TEXT_HEAD_TAIL_SIZE,
) -> str:
    """头尾截断"""
    if len(text) <= head_size + tail_size:
        return text
    return text[:head_size] + "\n\n... [middle content removed] ...\n\n" + text[-tail_size:]
from .resolver import resolve_url_to_base64
from .storage import ResultStorage, StoredResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tool-result"])

# 全局存储实例
_storage: Optional[ResultStorage] = None
_file_client: Optional[FileServiceClient] = None


def get_storage() -> ResultStorage:
    global _storage
    if _storage is None:
        _storage = ResultStorage()
    return _storage


def get_file_client() -> FileServiceClient:
    global _file_client
    if _file_client is None:
        _file_client = FileServiceClient(FILE_SERVICE_URL)
    return _file_client


# ---- create + insert (方案 A) ----

class CreateRequest(BaseModel):
    agent_id: str
    tool_name: Optional[str] = "unknown"
    tool_call_id: Optional[str] = None


@router.post("/create")
async def api_create(req: CreateRequest):
    """创建空 result，返回 result_id"""
    if not req.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    storage = get_storage()
    result_id = storage.create(
        agent_id=req.agent_id,
        tool_name=req.tool_name or "unknown",
        tool_call_id=req.tool_call_id,
    )
    return {"success": True, "result_id": result_id}


class InsertTextRequest(BaseModel):
    text: str


@router.post("/{result_id}/insert/text")
async def api_insert_text(result_id: str, req: InsertTextRequest):
    """追加文本项，长文本自动截断"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    idx = str(len(row.normalized.get("content", [])))
    text = req.text or ""
    full_text = None
    if len(text) > TEXT_TRUNCATE_THRESHOLD:
        full_text = text
        if len(text) > TEXT_REFERENCE_ONLY_THRESHOLD:
            truncated = _head_tail_truncate(text)
            strategy = "reference_only"
        else:
            truncated = _head_tail_truncate(text)
            strategy = "head_tail"
        item = {
            "type": "text",
            "text": truncated,
            "_truncated": True,
            "_truncation": {
                "strategy": strategy,
                "original_size": len(text),
                "result_id": result_id,
                "item_index": idx,
                "message": f"Use GET /api/{result_id}/full for full content.",
            },
        }
    else:
        item = {"type": "text", "text": text}
    ok = storage.append(result_id, item, full_text=full_text)
    if not ok:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"success": True, "result_id": result_id}


class InsertImageRequest(BaseModel):
    url: Optional[str] = None
    data: Optional[str] = None  # base64
    mimeType: Optional[str] = "image/png"


@router.post("/{result_id}/insert/image")
async def api_insert_image(result_id: str, req: InsertImageRequest):
    """追加图片项。提供 url 或 data（base64）"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    if req.url:
        item = {"type": "image", "url": req.url, "mimeType": req.mimeType or "image/png"}
    elif req.data:
        url = await get_file_client().save_from_base64(
            req.data, row.agent_id, "images", mime_type=req.mimeType or "image/png"
        )
        if not url:
            raise HTTPException(status_code=500, detail="File Service save failed")
        url = url if url.startswith("/") else url.split("/api/files", 1)[-1] or url
        item = {"type": "image", "url": url, "mimeType": req.mimeType or "image/png"}
    else:
        raise HTTPException(status_code=400, detail="url or data is required")
    ok = storage.append(result_id, item)
    if not ok:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"success": True, "result_id": result_id}


class InsertResourceRequest(BaseModel):
    url: Optional[str] = None
    data: Optional[str] = None  # base64
    mimeType: Optional[str] = "application/octet-stream"


@router.post("/{result_id}/insert/resource")
async def api_insert_resource(result_id: str, req: InsertResourceRequest):
    """追加资源项。提供 url 或 data（base64）"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    if req.url:
        item = {"type": "resource", "url": req.url, "mimeType": req.mimeType or "application/octet-stream"}
    elif req.data:
        mime = req.mimeType or "application/octet-stream"
        category = get_category_for_mime(mime)
        url = await get_file_client().save_from_base64(req.data, row.agent_id, category, mime_type=mime)
        if not url:
            raise HTTPException(status_code=500, detail="File Service save failed")
        url = url if url.startswith("/") else url.split("/api/files", 1)[-1] or url
        item = {"type": "resource", "url": url, "mimeType": mime}
    else:
        raise HTTPException(status_code=400, detail="url or data is required")
    ok = storage.append(result_id, item)
    if not ok:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"success": True, "result_id": result_id}


@router.get("/{result_id}")
async def api_get_result(result_id: str):
    """返回 normalized 结果"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"success": True, "result_id": result_id, "normalized": row.normalized}


@router.get("/{result_id}/for-llm")
async def api_get_for_llm(result_id: str, provider: str = "openai"):
    """
    返回 LLM 可用的格式：URL 已解析为 base64。
    provider: openai | anthropic
    """
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    content: List[Dict[str, Any]] = []
    for item in row.normalized.get("content", []):
        item = dict(item)
        if item.get("type") == "image" and item.get("url"):
            b64 = await resolve_url_to_base64(item["url"])
            if b64:
                mime = item.get("mimeType", "image/png")
                if provider == "anthropic":
                    content.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": b64},
                    })
                else:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    })
            else:
                content.append({"type": "text", "text": f"[Image load failed: {item.get('url', '')}]"})
        elif item.get("type") == "resource" and item.get("url"):
            b64 = await resolve_url_to_base64(item["url"])
            if b64:
                mime = item.get("mimeType", "application/octet-stream")
                content.append({
                    "type": "text",
                    "text": f"[Resource {mime}, base64 length={len(b64)}]",
                })
            else:
                content.append({"type": "text", "text": "[Resource load failed]"})
        else:
            content.append(item)
    return {"success": True, "content": content}


@router.get("/{result_id}/preview")
async def api_get_preview(result_id: str, max_text_len: int = 500):
    """前端预览：缩略文本 + 元数据"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    summary_parts = []
    for i, item in enumerate(row.normalized.get("content", [])):
        if item.get("type") == "text":
            text = item.get("text", "")
            if len(text) > max_text_len:
                text = text[:max_text_len] + "..."
            summary_parts.append(text)
        elif item.get("type") == "image":
            summary_parts.append("[Image]")
        elif item.get("type") == "resource":
            summary_parts.append(f"[Resource: {item.get('mimeType', 'unknown')}]")

    return {
        "success": True,
        "result_id": result_id,
        "agent_id": row.agent_id,
        "tool_name": row.tool_name,
        "created_at": row.created_at,
        "summary": "\n".join(summary_parts) if summary_parts else "(empty)",
        "content_count": len(row.normalized.get("content", [])),
    }


@router.get("/{result_id}/full")
async def api_get_full(result_id: str):
    """完整内容，长文本项由 full_texts 还原"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    content: List[Dict[str, Any]] = []
    for i, item in enumerate(row.normalized.get("content", [])):
        item = dict(item)
        idx = str(i)
        if item.get("_truncated") and idx in row.full_texts:
            item["text"] = row.full_texts[idx]
            item.pop("_truncated", None)
            item.pop("_truncation", None)
        content.append(item)

    return {
        "success": True,
        "normalized": {**row.normalized, "content": content},
    }


class ResolveRequest(BaseModel):
    url: str


@router.post("/resolve")
async def api_resolve(req: ResolveRequest):
    """单 URL 解析为 base64"""
    b64 = await resolve_url_to_base64(req.url)
    if not b64:
        raise HTTPException(status_code=404, detail="Failed to resolve URL")
    return {"success": True, "data": b64}
