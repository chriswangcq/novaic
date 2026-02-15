"""
File Service - 配置
category、MIME、大小限制等
"""

from typing import Dict, Optional, Tuple

# 支持的 category
CATEGORIES = ("images", "apk", "audio", "video", "documents", "binaries")

# category -> (默认扩展名, 大小限制 bytes)
CATEGORY_CONFIG: Dict[str, Tuple[str, int]] = {
    "images": ("png", 10 * 1024 * 1024),      # 10MB
    "apk": ("apk", 200 * 1024 * 1024),         # 200MB
    "audio": ("bin", 50 * 1024 * 1024),        # 50MB
    "video": ("mp4", 200 * 1024 * 1024),       # 200MB
    "documents": ("pdf", 50 * 1024 * 1024),    # 50MB
    "binaries": ("bin", 100 * 1024 * 1024),   # 100MB
}

# MIME -> (category, 扩展名)
MIME_TO_CATEGORY: Dict[str, Tuple[str, str]] = {
    "image/png": ("images", "png"),
    "image/jpeg": ("images", "jpg"),
    "image/jpg": ("images", "jpg"),
    "image/gif": ("images", "gif"),
    "image/webp": ("images", "webp"),
    "application/vnd.android.package-archive": ("apk", "apk"),
    "audio/wav": ("audio", "wav"),
    "audio/mp3": ("audio", "mp3"),
    "audio/mpeg": ("audio", "mp3"),
    "audio/m4a": ("audio", "m4a"),
    "video/mp4": ("video", "mp4"),
    "video/webm": ("video", "webm"),
    "application/pdf": ("documents", "pdf"),
    "application/octet-stream": ("binaries", "bin"),
}

# 扩展名 -> MIME（用于返回 Content-Type）
EXT_TO_MIME: Dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
    "apk": "application/vnd.android.package-archive",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/m4a",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "pdf": "application/pdf",
    "bin": "application/octet-stream",
}

URL_PREFIX = "/api/files"


def get_category_and_ext(mime_type: str, category_override: Optional[str] = None) -> Tuple[str, str]:
    """
    根据 MIME 或指定 category 得到 (category, ext)。
    """
    if category_override and category_override in CATEGORIES:
        default_ext, _ = CATEGORY_CONFIG[category_override]
        return category_override, default_ext
    if mime_type in MIME_TO_CATEGORY:
        return MIME_TO_CATEGORY[mime_type]
    return "binaries", "bin"


def get_size_limit(category: str) -> int:
    """返回 category 的大小限制（bytes）"""
    if category in CATEGORY_CONFIG:
        return CATEGORY_CONFIG[category][1]
    return CATEGORY_CONFIG["binaries"][1]


def get_mime_for_ext(ext: str) -> str:
    """根据扩展名返回 MIME"""
    ext_lower = ext.lower().lstrip(".")
    return EXT_TO_MIME.get(ext_lower, "application/octet-stream")
