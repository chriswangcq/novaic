"""
File Service - 内部 Client
供 Gateway、Executor 等调用，不暴露给 Agent
"""

from pathlib import Path
from typing import Optional

from .resolver import resolve_to_base64, resolve_to_path
from .storage import FileStorage


class FileServiceClient:
    """
    文件服务内部 Client。
    封装 Storage + 便捷方法，供系统各组件使用。
    """

    def __init__(self, storage: FileStorage):
        self._storage = storage

    @property
    def storage(self) -> FileStorage:
        return self._storage

    # ---------- 写入 ----------

    def save_bytes(
        self,
        data: bytes,
        category: str,
        agent_id: str,
        subagent_id: Optional[str] = None,
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> str:
        """存储字节，返回 URL"""
        return self._storage.save_bytes(
            data, category, agent_id, subagent_id, filename, mime_type
        )

    def save_from_base64(
        self,
        base64_data: str,
        category: str,
        agent_id: str,
        subagent_id: Optional[str] = None,
        mime_type: str = "application/octet-stream",
    ) -> str:
        """base64 存盘，返回 URL"""
        return self._storage.save_from_base64(
            base64_data, category, agent_id, subagent_id, mime_type
        )

    # ---------- 读取（仅内部使用）----------

    def load_bytes(self, url: str) -> Optional[bytes]:
        """URL -> 原始字节"""
        return self._storage.load_bytes(url)

    def load_as_base64(self, url: str) -> Optional[str]:
        """URL -> base64"""
        return self._storage.load_as_base64(url)

    def get_local_path(self, url: str) -> Optional[Path]:
        """URL -> 本地 Path（供 adb install 等需要 path 的场景）"""
        return self._storage.get_local_path(url)

    def get_local_path_str(self, url: str) -> Optional[str]:
        """URL -> 本地路径字符串"""
        return resolve_to_path(self._storage, url)

    # ---------- Resolve（对 Agent 透明，仅在调用点使用）----------

    def resolve_to_base64(self, value: str) -> str:
        """
        URL 或 base64 -> base64。
        若为文件 URL 则加载，否则透传（假定已是 base64）。
        """
        return resolve_to_base64(self._storage, value)

    # ---------- 工具 ----------

    def is_valid_file_url(self, value: str) -> bool:
        """是否为本服务的文件 URL"""
        return self._storage.is_valid_file_url(value)

    def delete(self, url: str) -> bool:
        """按 URL 删除"""
        return self._storage.delete(url)

    def get_info(self, url: str) -> Optional[dict]:
        """URL -> 元信息"""
        return self._storage.get_info(url)


def create_client(base_dir: str, url_prefix: str = "/api/files") -> FileServiceClient:
    """工厂函数：创建 FileServiceClient"""
    from .storage import FileStorage

    storage = FileStorage(base_dir=base_dir, url_prefix=url_prefix)
    return FileServiceClient(storage)
