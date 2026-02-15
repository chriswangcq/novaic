"""
File Service - Resolver
URL 解析与转换，供内部调用（LLM、Executor 等）
"""

from typing import Optional

from .storage import FileStorage


def resolve_to_base64(storage: FileStorage, value: str) -> str:
    """
    URL 或 base64 -> base64。
    若为本服务 URL，则加载并返回 base64；否则视为已是 base64 透传。

    注意：仅内部使用，不暴露给 Agent。
    """
    if not value:
        return value
    if storage.is_valid_file_url(value):
        loaded = storage.load_as_base64(value)
        if loaded:
            return loaded
    return value


def resolve_to_bytes(storage: FileStorage, value: str) -> Optional[bytes]:
    """URL -> 字节。若非有效 URL 返回 None。"""
    if storage.is_valid_file_url(value):
        return storage.load_bytes(value)
    return None


def resolve_to_path(storage: FileStorage, value: str) -> Optional[str]:
    """
    URL -> 本地路径字符串。
    供 adb install 等需要 path 的场景使用。
    """
    path = storage.get_local_path(value)
    if path:
        return str(path)
    return None
