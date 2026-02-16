"""
File Service - 存储层
磁盘读写、路径生成、URL 解析
"""

import base64
import hashlib
import logging
import re
import time
from pathlib import Path
from typing import Optional, Tuple

from .config import (
    CATEGORIES,
    get_category_and_ext,
    get_mime_for_ext,
    get_size_limit,
    MIME_TO_CATEGORY,
    URL_PREFIX,
)

logger = logging.getLogger(__name__)

# 安全的路径片段：只允许字母数字、下划线、连字符、点
_SAFE_SEGMENT = re.compile(r"^[a-zA-Z0-9_.-]+$")


def _is_safe_segment(segment: str) -> bool:
    return bool(segment and segment not in ("..", ".") and _SAFE_SEGMENT.match(segment))


def _generate_filename(data: bytes, extension: str) -> str:
    """生成唯一文件名：timestamp_hash.ext"""
    content_hash = hashlib.md5(data).hexdigest()[:8]
    timestamp = int(time.time() * 1000)
    return f"{timestamp}_{content_hash}.{extension}"


def _detect_image_type(data: bytes) -> Tuple[str, str]:
    """从二进制检测图片类型，返回 (ext, mime)"""
    if len(data) < 12:
        return "bin", "application/octet-stream"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png", "image/png"
    if data[:2] == b"\xff\xd8":
        return "jpg", "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif", "image/gif"
    if data[:4] == b"RIFF" and len(data) >= 12 and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    return "bin", "application/octet-stream"


class FileStorage:
    """
    磁盘存储实现。
    目录结构: base_dir / category / agent_id / [subagent_id /] filename
    """

    def __init__(self, base_dir: str, url_prefix: str = URL_PREFIX):
        self.base_dir = Path(base_dir)
        self.url_prefix = url_prefix.rstrip("/")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileStorage] base_dir={self.base_dir}, url_prefix={self.url_prefix}")

    def _get_dir(self, category: str, agent_id: str, subagent_id: Optional[str] = None) -> Path:
        """获取或创建存储目录"""
        if category not in CATEGORIES:
            category = "binaries"
        if not _is_safe_segment(agent_id):
            raise ValueError(f"Invalid agent_id: {agent_id}")
        if subagent_id is not None and not _is_safe_segment(subagent_id):
            raise ValueError(f"Invalid subagent_id: {subagent_id}")

        parts = [category, agent_id]
        if subagent_id:
            parts.append(subagent_id)
        dir_path = self.base_dir.joinpath(*parts)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def _url_to_path(self, url: str) -> Optional[Path]:
        """
        URL 转本地路径。仅接受本服务前缀，并做路径遍历校验。
        """
        if not url.startswith(self.url_prefix):
            return None
        relative = url[len(self.url_prefix) :].lstrip("/")
        if not relative or ".." in relative:
            return None
        parts = relative.split("/")
        if not all(_is_safe_segment(p) for p in parts):
            return None
        file_path = self.base_dir.joinpath(*parts)
        try:
            file_path.resolve().relative_to(self.base_dir.resolve())
        except ValueError:
            return None
        return file_path

    def _path_to_url(self, relative_path: Path) -> str:
        """相对路径转 URL"""
        parts = relative_path.parts
        return f"{self.url_prefix}/{'/'.join(parts)}"

    def save_bytes(
        self,
        data: bytes,
        category: str,
        agent_id: str,
        subagent_id: Optional[str] = None,
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> str:
        """
        存储字节，返回 URL。
        """
        size_limit = get_size_limit(category)
        if len(data) > size_limit:
            raise ValueError(f"File too large: {len(data)} > {size_limit}")

        # 确定扩展名：优先从原始文件名提取，其次从 MIME 类型推断
        ext = "bin"
        if filename and "." in filename:
            # 从原始文件名提取扩展名
            ext = filename.rsplit(".", 1)[-1].lower()
        elif category == "images":
            ext, _ = _detect_image_type(data)
        elif mime_type and mime_type in MIME_TO_CATEGORY:
            _, ext = MIME_TO_CATEGORY[mime_type]
        
        # 生成唯一文件名（保留扩展名）
        filename = _generate_filename(data, ext)

        dir_path = self._get_dir(category, agent_id, subagent_id)
        file_path = dir_path / filename
        file_path.write_bytes(data)

        rel = file_path.relative_to(self.base_dir)
        url = self._path_to_url(rel)
        logger.debug(f"[FileStorage] Saved {len(data)} bytes -> {url}")
        return url

    def save_from_base64(
        self,
        base64_data: str,
        category: str,
        agent_id: str,
        subagent_id: Optional[str] = None,
        mime_type: str = "application/octet-stream",
        filename: Optional[str] = None,  # 新增：支持自定义文件名
    ) -> str:
        """base64 存盘，返回 URL"""
        if base64_data.startswith("data:"):
            # data:image/png;base64,xxxxx
            prefix, b64 = base64_data.split(",", 1)
            mime_from_prefix = prefix.split(":")[1].split(";")[0] if ":" in prefix else mime_type
            mime_type = mime_from_prefix
        else:
            b64 = base64_data
        data = base64.b64decode(b64)
        return self.save_bytes(data, category, agent_id, subagent_id, filename=filename, mime_type=mime_type)

    def load_bytes(self, url: str) -> Optional[bytes]:
        """URL -> 原始字节"""
        path = self._url_to_path(url)
        if path and path.exists():
            return path.read_bytes()
        return None

    def load_as_base64(self, url: str) -> Optional[str]:
        """URL -> base64 字符串"""
        data = self.load_bytes(url)
        if data is not None:
            return base64.b64encode(data).decode("utf-8")
        return None

    def get_local_path(self, url: str) -> Optional[Path]:
        """URL -> 本地 Path（直接指向文件，无需拷贝）"""
        path = self._url_to_path(url)
        if path and path.exists():
            return path
        return None

    def get_info(self, url: str) -> Optional[dict]:
        """URL -> 元信息 {size, mime_type, created}"""
        path = self._url_to_path(url)
        if path and path.exists():
            stat = path.stat()
            ext = path.suffix.lower().lstrip(".")
            return {
                "size": stat.st_size,
                "mime_type": get_mime_for_ext(ext),
                "created": stat.st_ctime,
            }
        return None

    def delete(self, url: str) -> bool:
        """按 URL 删除"""
        path = self._url_to_path(url)
        if path and path.exists():
            try:
                path.unlink()
                logger.debug(f"[FileStorage] Deleted {url}")
                return True
            except OSError as e:
                logger.warning(f"[FileStorage] Failed to delete {url}: {e}")
        return False

    def is_valid_file_url(self, value: str) -> bool:
        """是否为本服务的文件 URL"""
        if not isinstance(value, str):
            return False
        return value.startswith(self.url_prefix + "/")
