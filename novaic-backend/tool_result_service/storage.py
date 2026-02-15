"""
Tool Result Service - 结果存储
SQLite 永久存储

normalized 结构（三要素）:
{
    "text": "...",                    # 文本说明
    "files_created": [{url, filename, modality}, ...],  # 创建的文件
    "display_files": [{url, filename, modality}, ...]   # 展示给 LLM 的文件
}
"""

import json
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FileRef:
    """文件引用"""
    url: str
    filename: str
    modality: str  # "image" | "resource"

    def to_dict(self) -> Dict[str, Any]:
        return {"url": self.url, "filename": self.filename, "modality": self.modality}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FileRef":
        return cls(
            url=d.get("url", ""),
            filename=d.get("filename", ""),
            modality=d.get("modality", "resource"),
        )


@dataclass
class StoredResult:
    result_id: str
    agent_id: str
    tool_name: str
    tool_call_id: Optional[str]
    normalized: Dict[str, Any]  # {text, files_created, display_files}
    created_at: str

    @property
    def text(self) -> str:
        return self.normalized.get("text", "")

    @property
    def files_created(self) -> List[Dict[str, Any]]:
        return self.normalized.get("files_created", [])

    @property
    def display_files(self) -> List[Dict[str, Any]]:
        return self.normalized.get("display_files", [])


class ResultStorage:
    """SQLite 存储"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = os.environ.get("NOVAIC_DATA_DIR", os.path.expanduser("~/.novaic"))
            Path(data_dir).mkdir(parents=True, exist_ok=True)
            db_path = str(Path(data_dir) / "tool_results.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_results (
                    result_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_call_id TEXT,
                    normalized TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON tool_results(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON tool_results(created_at)")

    def _generate_id(self) -> str:
        return f"trs_{uuid.uuid4().hex[:8]}"

    def create(
        self,
        agent_id: str,
        tool_name: str = "unknown",
        tool_call_id: Optional[str] = None,
        text: str = "",
        files_created: Optional[List[Dict[str, Any]]] = None,
        display_files: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        创建 result，直接传入三要素。

        Args:
            agent_id: Agent ID
            tool_name: 工具名称
            tool_call_id: Tool call ID
            text: 文本说明
            files_created: 创建的文件 [{url, filename, modality}]
            display_files: 展示给 LLM 的文件 [{url, filename, modality}]

        Returns:
            result_id
        """
        result_id = self._generate_id()
        created_at = datetime.utcnow().isoformat() + "Z"
        normalized = {
            "text": text,
            "files_created": files_created or [],
            "display_files": display_files or [],
        }

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO tool_results
                   (result_id, agent_id, tool_name, tool_call_id, normalized, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    result_id,
                    agent_id,
                    tool_name,
                    tool_call_id,
                    json.dumps(normalized, ensure_ascii=False),
                    created_at,
                ),
            )
        logger.debug(f"[ResultStorage] Created {result_id}")
        return result_id

    def get(self, result_id: str) -> Optional[StoredResult]:
        """按 ID 获取"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM tool_results WHERE result_id = ?", (result_id,)
            ).fetchone()
        if not row:
            return None
        return StoredResult(
            result_id=row["result_id"],
            agent_id=row["agent_id"],
            tool_name=row["tool_name"],
            tool_call_id=row["tool_call_id"],
            normalized=json.loads(row["normalized"]),
            created_at=row["created_at"],
        )

    def delete(self, result_id: str) -> bool:
        """删除 result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM tool_results WHERE result_id = ?", (result_id,)
            )
            return cursor.rowcount > 0
