"""
Tool Result Service - 配置
"""

import os

# 服务端口
SERVICE_PORT = int(os.getenv("TOOL_RESULT_SERVICE_PORT", "19994"))

# 依赖服务 URL
FILE_SERVICE_URL = os.getenv("FILE_SERVICE_URL", "http://127.0.0.1:19995")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:19999")

# 文本截断阈值（字节）
TEXT_TRUNCATE_THRESHOLD = 4 * 1024  # 4KB
TEXT_REFERENCE_ONLY_THRESHOLD = 10 * 1024  # 10KB
TEXT_HEAD_TAIL_SIZE = 1536  # 1.5KB each

# 传统图片字段名（legacy 格式）
LEGACY_IMAGE_FIELDS = (
    "screenshot",
    "image",
    "image_data",
    "image_base64",
    "base64_image",
    "png_data",
    "jpeg_data",
    "data",
)

# MIME → File Service category
MIME_TO_CATEGORY = {
    "image/png": "images",
    "image/jpeg": "images",
    "image/jpg": "images",
    "image/gif": "images",
    "image/webp": "images",
    "application/vnd.android.package-archive": "apk",
    "audio/wav": "audio",
    "audio/mp3": "audio",
    "audio/mpeg": "audio",
    "audio/m4a": "audio",
    "video/mp4": "video",
    "video/webm": "video",
    "application/pdf": "documents",
    "application/octet-stream": "binaries",
}


def get_category_for_mime(mime_type: str) -> str:
    """根据 MIME 返回 File Service category"""
    return MIME_TO_CATEGORY.get(mime_type or "", "binaries")
