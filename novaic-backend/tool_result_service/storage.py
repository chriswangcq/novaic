"""
Tool Result Service - 结果存储
SQLite 永久存储
"""

import json
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class StoredResult:
    result_id: str
    agent_id: str
    tool_name: str
    tool_call_id: Optional[str]
    raw_result: Dict[str, Any]
    normalized: Dict[str, Any]
    full_texts: Dict[str, str]
    created_at: str


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
                    raw_result TEXT NOT NULL,
                    normalized TEXT NOT NULL,
                    full_texts TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_id ON tool_results(agent_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON tool_results(created_at)")

    def _generate_id(self) -> str:
        return f"trs_{uuid.uuid4().hex[:8]}"

    def generate_id(self) -> str:
        """生成新的 result_id"""
        return self._generate_id()

    def create(
        self,
        agent_id: str,
        tool_name: str = "unknown",
        tool_call_id: Optional[str] = None,
    ) -> str:
        """创建空 result，返回 result_id"""
        result_id = self._generate_id()
        created_at = datetime.utcnow().isoformat() + "Z"
        normalized = {"success": True, "content": []}

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO tool_results
                   (result_id, agent_id, tool_name, tool_call_id, raw_result, normalized, full_texts, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    result_id,
                    agent_id,
                    tool_name,
                    tool_call_id,
                    "{}",
                    json.dumps(normalized, ensure_ascii=False),
                    "{}",
                    created_at,
                ),
            )
        logger.debug(f"[ResultStorage] Created {result_id}")
        return result_id

    def append(
        self,
        result_id: str,
        item: Dict[str, Any],
        full_text: Optional[str] = None,
    ) -> bool:
        """追加 content 项，可选 full_text（长文本截断时）"""
        row = self.get(result_id)
        if not row:
            return False
        content = list(row.normalized.get("content", []))
        full_texts = dict(row.full_texts)
        idx = str(len(content))
        content.append(item)
        if full_text is not None:
            full_texts[idx] = full_text
        normalized = {**row.normalized, "content": content}
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE tool_results SET normalized = ?, full_texts = ? WHERE result_id = ?""",
                (json.dumps(normalized, ensure_ascii=False), json.dumps(full_texts, ensure_ascii=False), result_id),
            )
        return True

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
            raw_result=json.loads(row["raw_result"]),
            normalized=json.loads(row["normalized"]),
            full_texts=json.loads(row["full_texts"] or "{}"),
            created_at=row["created_at"],
        )
