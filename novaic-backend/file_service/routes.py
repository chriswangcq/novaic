"""
File Service - HTTP 路由
"""

import base64
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from .config import (
    URL_PREFIX,
    get_category_and_ext,
    get_mime_for_ext,
    get_size_limit,
)
from .storage import FileStorage, _generate_filename

logger = logging.getLogger(__name__)


class FromBase64Request(BaseModel):
    """Base64 上传请求 (JSON body)"""
    data: str
    agent_id: str
    category: Optional[str] = None
    subagent_id: Optional[str] = None
    mime_type: Optional[str] = "application/octet-stream"
    filename: Optional[str] = None  # 方案 C：已忽略，由 File Service 生成唯一名


def create_router(storage: FileStorage) -> APIRouter:
    """创建 FastAPI 路由，需传入已初始化的 FileStorage"""
    router = APIRouter(prefix=URL_PREFIX, tags=["files"])

    @router.post("/upload")
    async def upload(
        file: UploadFile = File(...),
        agent_id: str = Form(...),
        category: Optional[str] = Form(None),
        subagent_id: Optional[str] = Form(None),
    ):
        """
        上传文件 (multipart)，返回 URL。
        """
        data = await file.read()

        # 推断 category 和 扩展名
        content_type = file.content_type or "application/octet-stream"
        cat, ext = get_category_and_ext(content_type, category)
        size_limit = get_size_limit(cat)
        if len(data) > size_limit:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {len(data)} > {size_limit}",
            )

        original_filename = file.filename or "file"
        if not original_filename or original_filename == "blob":
            original_filename = _generate_filename(data, ext)

        url = storage.save_bytes(data, cat, agent_id, subagent_id, filename=original_filename)
        # 从 URL 提取实际保存的文件名（File Service 可能会重命名）
        actual_filename = url.rsplit("/", 1)[-1] if "/" in url else original_filename
        ext = actual_filename.rsplit(".", 1)[-1].lower() if "." in actual_filename else "bin"
        mime_type = get_mime_for_ext(ext) if content_type == "application/octet-stream" else content_type
        return {
            "url": url,
            "filename": actual_filename,  # 返回实际保存的文件名
            "original_filename": original_filename,  # 保留原始文件名供参考
            "mime_type": mime_type,
            "category": cat,
            "size": len(data),
        }

    @router.post("/from-base64")
    async def from_base64(req: FromBase64Request):
        """
        提交 base64 数据，存盘后返回 URL。
        支持 JSON body，无 multipart 大小限制。
        """
        data = req.data
        mime_type = req.mime_type or "application/octet-stream"
        
        # 处理 data URI scheme
        if data.startswith("data:"):
            # data:image/png;base64,xxxxx
            parts = data.split(",", 1)
            if len(parts) == 2:
                header = parts[0]
                data = parts[1]
                if ":" in header and ";" in header:
                    mime_type = header.split(":")[1].split(";")[0]

        cat, _ = get_category_and_ext(mime_type, req.category)
        size_limit = get_size_limit(cat)
        # base64 大小约为原文 4/3
        estimated = len(data) * 3 // 4
        if estimated > size_limit:
            raise HTTPException(
                status_code=413,
                detail=f"Data too large: estimated {estimated} > {size_limit}",
            )

        # 方案 C：不传 filename，由 File Service 用 _generate_filename 生成唯一名，避免冲突
        url = storage.save_from_base64(
            data, cat, req.agent_id, req.subagent_id, mime_type,
            filename=None,
        )
        info = storage.get_info(url)
        filename = url.rsplit("/", 1)[-1].split("?")[0] if url else None
        return {
            "url": url,
            "category": cat,
            "size": info["size"] if info else 0,
            "mime_type": mime_type,
            "filename": filename,
        }

    @router.get("/info")
    async def info(url: str):
        """返回文件元信息"""
        info = storage.get_info(url)
        if not info:
            raise HTTPException(status_code=404, detail="File not found")
        return info

    @router.get("/{path:path}")
    async def get_file(path: str):
        """
        按 path 下载文件。
        path 格式: category/agent_id/[subagent_id/]filename
        """
        url = f"{URL_PREFIX}/{path}"
        file_path = storage._url_to_path(url)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        ext = file_path.suffix.lower().lstrip(".")
        media_type = get_mime_for_ext(ext)

        from fastapi.responses import FileResponse

        return FileResponse(file_path, media_type=media_type)

    @router.delete("/{path:path}")
    async def delete_file(path: str):
        """按 path 删除文件"""
        url = f"{URL_PREFIX}/{path}"
        ok = storage.delete(url)
        if not ok:
            raise HTTPException(status_code=404, detail="File not found")
        return {"deleted": True}

    return router
