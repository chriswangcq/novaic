"""
Tool Result Service - HTTP 路由

normalized 结构（三要素）:
{
    "text": "...",
    "files_created": [{url, filename, modality}, ...],
    "display_files": [{url, filename, modality}, ...]
}
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .resolver import resolve_url_to_base64
from .storage import ResultStorage, StoredResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tool-result"])

# 全局存储实例
_storage: Optional[ResultStorage] = None


def get_storage() -> ResultStorage:
    global _storage
    if _storage is None:
        _storage = ResultStorage()
    return _storage


# ==================== Create ====================


class FileRefModel(BaseModel):
    url: str
    filename: str = ""
    modality: str = "resource"  # "image" | "resource"


class CreateRequest(BaseModel):
    agent_id: str
    tool_name: Optional[str] = "unknown"
    tool_call_id: Optional[str] = None
    # 三要素
    text: str = ""
    files_created: List[FileRefModel] = []
    display_files: List[FileRefModel] = []


@router.post("/create")
async def api_create(req: CreateRequest):
    """
    创建 tool result，直接传入三要素。

    Args:
        agent_id: Agent ID
        tool_name: 工具名称
        tool_call_id: Tool call ID
        text: 文本说明
        files_created: 创建的文件 [{url, filename, modality}]
        display_files: 展示给 LLM 的文件 [{url, filename, modality}]

    Returns:
        {"success": true, "result_id": "trs_xxx"}
    """
    if not req.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    storage = get_storage()
    result_id = storage.create(
        agent_id=req.agent_id,
        tool_name=req.tool_name or "unknown",
        tool_call_id=req.tool_call_id,
        text=req.text,
        files_created=[f.model_dump() for f in req.files_created],
        display_files=[f.model_dump() for f in req.display_files],
    )
    return {"success": True, "result_id": result_id}


# ==================== Read ====================


@router.get("/{result_id}")
async def api_get_result(result_id: str):
    """返回 normalized 结果（三要素结构）"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"success": True, "result_id": result_id, "normalized": row.normalized}


@router.get("/{result_id}/for-llm")
async def api_get_for_llm(
    result_id: str,
    provider: str = "openai",
    include_display: bool = True,
):
    """
    返回 LLM 可用的格式。

    Args:
        result_id: Result ID
        provider: "openai" | "anthropic"
        include_display: 是否包含 display_files 中的图片。
                         True: 当前 round，展示图片
                         False: 历史 round，仅返回文本

    Returns:
        {"success": true, "content": [...]}
        content 是 LLM 消息格式的数组
    """
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    content: List[Dict[str, Any]] = []

    # 1. 文本部分（始终包含）
    if row.text:
        content.append({"type": "text", "text": row.text})

    # 2. display_files（根据 include_display 决定）
    if include_display:
        for f in row.display_files:
            url = f.get("url", "")
            modality = f.get("modality", "resource")
            if modality == "image":
                b64 = await resolve_url_to_base64(url)
                if b64:
                    mime = "image/png"  # 可从 filename 推断，暂用默认
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
                    content.append({"type": "text", "text": f"[Image load failed: {url}]"})
            else:
                # resource: 仅文本提示
                content.append({"type": "text", "text": f"[Resource: {url}]"})

    return {"success": True, "content": content}


@router.get("/{result_id}/preview")
async def api_get_preview(result_id: str, max_text_len: int = 500):
    """前端预览：缩略文本 + 元数据"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    summary_parts = []

    # 文本
    text = row.text
    if text:
        if len(text) > max_text_len:
            text = text[:max_text_len] + "..."
        summary_parts.append(text)

    # files_created
    if row.files_created:
        summary_parts.append(f"[{len(row.files_created)} file(s) created]")

    # display_files
    if row.display_files:
        img_count = sum(1 for f in row.display_files if f.get("modality") == "image")
        if img_count:
            summary_parts.append(f"[{img_count} image(s) to display]")

    return {
        "success": True,
        "result_id": result_id,
        "agent_id": row.agent_id,
        "tool_name": row.tool_name,
        "created_at": row.created_at,
        "summary": "\n".join(summary_parts) if summary_parts else "(empty)",
        "files_created_count": len(row.files_created),
        "display_files_count": len(row.display_files),
    }


@router.get("/{result_id}/full")
async def api_get_full(result_id: str):
    """返回完整内容（与 GET /{result_id} 相同，兼容旧前端）"""
    storage = get_storage()
    row = storage.get(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"success": True, "normalized": row.normalized}


# ==================== Utility ====================


class ResolveRequest(BaseModel):
    url: str


@router.post("/resolve")
async def api_resolve(req: ResolveRequest):
    """单 URL 解析为 base64"""
    b64 = await resolve_url_to_base64(req.url)
    if not b64:
        raise HTTPException(status_code=404, detail="Failed to resolve URL")
    return {"success": True, "data": b64}
