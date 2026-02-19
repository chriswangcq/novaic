"""
TaskQueue - 纯粹的任务队列 (Gateway DB 实现)

核心 API：
- publish(): 发布任务
- claim(): 原子认领任务
- complete(): 标记完成
- fail(): 标记失败/重试
- heartbeat(): 心跳续约
- recover_stale(): 超时恢复
"""

import json
import uuid
# threading import removed - using db.transaction() instead
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from queue_service.exceptions import TaskNotFoundError
from common.utils.time import utc_now_iso


class TaskQueue:
    """
    纯粹的任务队列，不涉及任何业务逻辑
    
    使用方式：
        queue = TaskQueue(db)
        
        # 发布任务
        task_id = queue.publish("my_topic", {"key": "value"})
        
        # 认领任务
        task = queue.claim(["my_topic"], "worker-1")
        
        # 处理完成
        queue.complete(task["id"], {"result": "ok"})
    """
    
    def __init__(self, db):
        """
        初始化 TaskQueue
        
        Args:
            db: 数据库连接（aiosqlite connection）
        """
        self.db = db
    
    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
    ) -> str:
        """
        发布任务到队列
        """
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        payload_json = json.dumps(payload, ensure_ascii=False)
        now = utc_now_iso()
        
        try:
            with self.db.transaction(lock_type="global"):
                self.db.execute("""
                    INSERT INTO tq_tasks (
                        id, topic, payload, idempotency_key, 
                        max_retries, status, created_at, next_retry_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                """, (task_id, topic, payload_json, idempotency_key, max_retries, now, now))
                return task_id
            
        except Exception as e:
            # 检查是否是唯一约束冲突
            if "UNIQUE constraint" in str(e) and idempotency_key:
                with self.db.transaction(lock_type="global"):
                    cursor = self.db.execute(
                        "SELECT id FROM tq_tasks WHERE idempotency_key = ?",
                        (idempotency_key,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return row[0]
            raise
    
    def claim(
        self,
        topics: List[str],
        worker_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        原子性认领一个任务（CAS）
        """
        if not topics:
            return None
        
        with self.db.transaction(lock_type="global"):
            topic_placeholders = ",".join("?" * len(topics))
            now = utc_now_iso()
            
            cursor = self.db.execute(f"""
                UPDATE tq_tasks 
                SET status = 'claimed',
                    claimed_by = ?,
                    claimed_at = ?,
                    heartbeat_at = ?,
                    started_at = ?,
                    next_retry_at = NULL,
                    version = version + 1
                WHERE id = (
                    SELECT id FROM tq_tasks 
                    WHERE status = 'pending' 
                      AND (next_retry_at IS NULL OR datetime(next_retry_at) <= datetime('now'))
                      AND topic IN ({topic_placeholders})
                    ORDER BY created_at
                    LIMIT 1
                )
                RETURNING *
            """, (worker_id, now, now, now, *topics))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    def complete(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """标记任务完成"""
        with self.db.transaction(lock_type="task", resource_id=task_id):
            result_json = json.dumps(result, ensure_ascii=False) if result else None
            now = utc_now_iso()
            
            cursor = self.db.execute("""
                UPDATE tq_tasks 
                SET status = 'done',
                    result = ?,
                    finished_at = ?
                WHERE id = ? AND status = 'claimed'
            """, (result_json, now, task_id))
            rowcount = cursor.rowcount
            cursor.close()
            
            return rowcount > 0
    
    def fail(
        self,
        task_id: str,
        error: str,
        retry: bool = True,
        retry_delay_seconds: Optional[float] = None,
    ) -> str:
        """标记任务失败"""
        with self.db.transaction(lock_type="task", resource_id=task_id):
            now = utc_now_iso()
            cursor = self.db.execute(
                "SELECT retry_count, max_retries, status FROM tq_tasks WHERE id = ?",
                (task_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            if not row:
                return "unknown"
            retry_count, max_retries, status = row
            if status != "claimed":
                return "unknown"

            if retry:
                next_retry_count = int(retry_count) + 1
                can_retry = int(retry_count) < int(max_retries)
                final_status = "pending" if can_retry else "failed"
                next_retry_at = (
                    self._compute_next_retry_at(
                        now=now,
                        attempt=next_retry_count,
                        delay_override_seconds=retry_delay_seconds,
                    )
                    if can_retry
                    else None
                )
                self.db.execute(
                    """
                    UPDATE tq_tasks
                    SET status = ?,
                        retry_count = ?,
                        claimed_by = NULL,
                        claimed_at = NULL,
                        heartbeat_at = NULL,
                        next_retry_at = ?,
                        error = ?,
                        finished_at = ?
                    WHERE id = ? AND status = 'claimed'
                    """,
                    (
                        final_status,
                        next_retry_count,
                        next_retry_at,
                        error,
                        None if can_retry else now,
                        task_id,
                    ),
                )
                return final_status

            self.db.execute(
                """
                UPDATE tq_tasks
                SET status = 'failed',
                    error = ?,
                    next_retry_at = NULL,
                    finished_at = ?
                WHERE id = ? AND status = 'claimed'
                """,
                (error, now, task_id),
            )
            return "failed"
    
    def heartbeat(self, task_id: str) -> bool:
        """更新心跳时间"""
        with self.db.transaction(lock_type="task", resource_id=task_id):
            now = utc_now_iso()
            
            cursor = self.db.execute("""
                UPDATE tq_tasks 
                SET heartbeat_at = ?
                WHERE id = ? AND status = 'claimed'
            """, (now, task_id))
            
            return cursor.rowcount > 0
    
    def recover_stale(self, timeout_seconds: int = 60) -> int:
        """恢复超时任务"""
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(
                f"""
                SELECT id, retry_count, max_retries
                FROM tq_tasks
                WHERE status = 'claimed'
                  AND datetime(heartbeat_at) < datetime('now', '-{timeout_seconds} seconds')
                """
            )
            stale_rows = cursor.fetchall()
            cursor.close()

            if not stale_rows:
                return 0

            now = utc_now_iso()
            for task_id, retry_count, max_retries in stale_rows:
                next_retry_count = int(retry_count) + 1
                can_retry = int(retry_count) < int(max_retries)
                status = "pending" if can_retry else "failed"
                error = (
                    "Heartbeat timeout, will retry"
                    if can_retry
                    else "Heartbeat timeout, max retries exceeded"
                )
                next_retry_at = (
                    self._compute_next_retry_at(now=now, attempt=next_retry_count)
                    if can_retry
                    else None
                )
                self.db.execute(
                    """
                    UPDATE tq_tasks
                    SET status = ?,
                        retry_count = ?,
                        claimed_by = NULL,
                        claimed_at = NULL,
                        heartbeat_at = NULL,
                        next_retry_at = ?,
                        error = ?,
                        finished_at = ?
                    WHERE id = ? AND status = 'claimed'
                    """,
                    (
                        status,
                        next_retry_count,
                        next_retry_at,
                        error,
                        None if can_retry else now,
                        task_id,
                    ),
                )

            return len(stale_rows)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        with self.db.transaction(lock_type="task", resource_id=task_id):
            cursor = self.db.execute(
                "SELECT * FROM tq_tasks WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    def get_task_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """通过幂等键获取任务"""
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(
                "SELECT * FROM tq_tasks WHERE idempotency_key = ?",
                (idempotency_key,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    def count_by_status(
        self,
        topic: Optional[str] = None,
    ) -> Dict[str, int]:
        """统计各状态任务数量"""
        with self.db.transaction(lock_type="global"):
            if topic:
                cursor = self.db.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM tq_tasks 
                    WHERE topic = ?
                    GROUP BY status
                """, (topic,))
            else:
                cursor = self.db.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM tq_tasks 
                    GROUP BY status
                """)
            
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}
    
    def cancel_all(self, agent_id: Optional[str] = None) -> int:
        """
        取消所有 pending/claimed 状态的任务
        
        Args:
            agent_id: 可选，只取消指定 agent 的任务（通过 payload 中的 agent_id 字段）
            
        Returns:
            取消的任务数量
        """
        now = utc_now_iso()
        
        with self.db.transaction(lock_type="global"):
            if agent_id:
                # 取消指定 agent 的任务
                cursor = self.db.execute("""
                    UPDATE tq_tasks 
                    SET status = 'cancelled',
                        error = 'Cancelled by interrupt',
                        finished_at = ?
                    WHERE status IN ('pending', 'claimed')
                      AND payload LIKE ?
                    RETURNING id
                """, (now, f'%"agent_id":"{agent_id}"%'))
            else:
                # 取消所有任务
                cursor = self.db.execute("""
                    UPDATE tq_tasks 
                    SET status = 'cancelled',
                        error = 'Cancelled by interrupt',
                        finished_at = ?
                    WHERE status IN ('pending', 'claimed')
                    RETURNING id
                """, (now,))
            
            rows = cursor.fetchall()
            cursor.close()
            
            return len(rows) if rows else 0
    
    def get_topics(self) -> List[str]:
        """
        获取所有已知的 topics
        
        Returns:
            所有在 tq_tasks 表中出现过的 topic 列表
        """
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute("""
                SELECT DISTINCT topic FROM tq_tasks ORDER BY topic
            """)
            rows = cursor.fetchall()
            cursor.close()
            return [row[0] for row in rows]

    def acquire_idempotency_execution(
        self,
        task_id: str,
        idempotency_key: str,
        owner_token: str,
        lease_seconds: int = 120,
    ) -> Dict[str, Any]:
        """
        Acquire cross-process execution guard for idempotent side effects.

        Returns:
            {"action": "acquired" | "in_progress" | "completed", "result": Optional[Dict]}
        """
        if not idempotency_key:
            return {"action": "acquired"}

        now = utc_now_iso()
        lease_until = self._compute_next_retry_at(
            now=now,
            attempt=1,
            delay_override_seconds=max(1, int(lease_seconds)),
        )

        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(
                """
                SELECT status, owner_token, task_id, result, lease_until
                FROM tq_idempotency_ledger
                WHERE idempotency_key = ?
                """,
                (idempotency_key,),
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                self.db.execute(
                    """
                    INSERT INTO tq_idempotency_ledger (
                        idempotency_key, status, owner_token, task_id, result,
                        contention_count, last_contended_at, lease_until, updated_at
                    ) VALUES (?, 'in_progress', ?, ?, NULL, 0, NULL, ?, ?)
                    """,
                    (idempotency_key, owner_token, task_id, lease_until, now),
                )
                return {"action": "acquired"}

            status, existing_owner, existing_task_id, existing_result, existing_lease_until = row

            if status == "completed":
                parsed_result = None
                if existing_result:
                    try:
                        parsed_result = json.loads(existing_result)
                    except (json.JSONDecodeError, TypeError):
                        parsed_result = None
                return {"action": "completed", "result": parsed_result}

            lease_active = False
            if existing_lease_until:
                try:
                    lease_active = datetime.fromisoformat(
                        existing_lease_until.replace("Z", "+00:00")
                    ) > datetime.fromisoformat(now.replace("Z", "+00:00"))
                except Exception:
                    lease_active = False

            if status == "in_progress" and lease_active and existing_owner != owner_token:
                self.db.execute(
                    """
                    UPDATE tq_idempotency_ledger
                    SET contention_count = COALESCE(contention_count, 0) + 1,
                        last_contended_at = ?,
                        updated_at = ?
                    WHERE idempotency_key = ?
                    """,
                    (now, now, idempotency_key),
                )
                return {"action": "in_progress"}

            self.db.execute(
                """
                UPDATE tq_idempotency_ledger
                SET status = 'in_progress',
                    owner_token = ?,
                    task_id = ?,
                    last_contended_at = COALESCE(last_contended_at, NULL),
                    lease_until = ?,
                    updated_at = ?
                WHERE idempotency_key = ?
                """,
                (owner_token, task_id, lease_until, now, idempotency_key),
            )
            return {"action": "acquired"}

    def complete_idempotency_execution(
        self,
        task_id: str,
        idempotency_key: str,
        owner_token: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Mark idempotent side effect as completed persistently."""
        if not idempotency_key:
            return True
        now = utc_now_iso()
        result_json = json.dumps(result, ensure_ascii=False) if result is not None else None
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(
                """
                UPDATE tq_idempotency_ledger
                SET status = 'completed',
                    result = ?,
                    lease_until = NULL,
                    updated_at = ?
                WHERE idempotency_key = ?
                  AND status = 'in_progress'
                  AND owner_token = ?
                  AND task_id = ?
                """,
                (result_json, now, idempotency_key, owner_token, task_id),
            )
            updated = cursor.rowcount > 0
            cursor.close()

            if updated:
                return True

            self.db.execute(
                """
                INSERT INTO tq_idempotency_ledger (
                    idempotency_key, status, owner_token, task_id, result,
                    contention_count, last_contended_at, lease_until, updated_at
                ) VALUES (?, 'completed', ?, ?, ?, 0, NULL, NULL, ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    status = 'completed',
                    owner_token = excluded.owner_token,
                    task_id = excluded.task_id,
                    result = excluded.result,
                    lease_until = NULL,
                    updated_at = excluded.updated_at
                """,
                (idempotency_key, owner_token, task_id, result_json, now),
            )
            return True

    def release_idempotency_execution(
        self,
        task_id: str,
        idempotency_key: str,
        owner_token: str,
    ) -> bool:
        """Release in-progress idempotency lock for retry path."""
        if not idempotency_key:
            return True
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(
                """
                DELETE FROM tq_idempotency_ledger
                WHERE idempotency_key = ?
                  AND status = 'in_progress'
                  AND owner_token = ?
                  AND task_id = ?
                """,
                (idempotency_key, owner_token, task_id),
            )
            deleted = cursor.rowcount > 0
            cursor.close()
            return deleted

    def get_idempotency_diagnostics(
        self,
        limit: int = 20,
        only_contended: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return top ledger rows by contention_count for diagnostics visibility."""
        safe_limit = max(1, min(int(limit), 200))
        with self.db.transaction(lock_type="global"):
            if only_contended:
                cursor = self.db.execute(
                    """
                    SELECT idempotency_key, status, owner_token, task_id,
                           contention_count, last_contended_at, lease_until, updated_at
                    FROM tq_idempotency_ledger
                    WHERE COALESCE(contention_count, 0) > 0
                    ORDER BY contention_count DESC, updated_at DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                )
            else:
                cursor = self.db.execute(
                    """
                    SELECT idempotency_key, status, owner_token, task_id,
                           contention_count, last_contended_at, lease_until, updated_at
                    FROM tq_idempotency_ledger
                    ORDER BY contention_count DESC, updated_at DESC
                    LIMIT ?
                    """,
                    (safe_limit,),
                )
            rows = cursor.fetchall()
            cursor.close()
            diagnostics: List[Dict[str, Any]] = []
            for row in rows:
                diagnostics.append(
                    {
                        "idempotency_key": row[0],
                        "status": row[1],
                        "owner_token": row[2],
                        "task_id": row[3],
                        "contention_count": int(row[4] or 0),
                        "last_contended_at": row[5],
                        "lease_until": row[6],
                        "updated_at": row[7],
                    }
                )
            return diagnostics
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        if hasattr(row, "keys"):
            result = dict(row)
        else:
            columns = [
                "id", "idempotency_key", "topic", "payload",
                "status", "claimed_by", "claimed_at", "heartbeat_at",
                "retry_count", "max_retries", "next_retry_at", "result", "error",
                "created_at", "started_at", "finished_at", "version"
            ]
            result = dict(zip(columns, row))
        
        if result.get("payload"):
            try:
                result["payload"] = json.loads(result["payload"])
            except (json.JSONDecodeError, TypeError):
                pass
        
        if result.get("result"):
            try:
                result["result"] = json.loads(result["result"])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return result

    def _compute_next_retry_at(
        self,
        *,
        now: str,
        attempt: int,
        delay_override_seconds: Optional[float] = None,
    ) -> str:
        """Compute next retry time from attempt index and config."""
        if delay_override_seconds is not None:
            delay = max(0.0, float(delay_override_seconds))
        else:
            # Backward compatible default for callers that do not provide delay.
            delay = 0.0
        now_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
        return (now_dt + timedelta(seconds=delay)).isoformat().replace("+00:00", "Z")
