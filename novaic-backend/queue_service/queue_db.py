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
from datetime import datetime
from typing import Optional, List, Dict, Any

from queue_service.exceptions import TaskNotFoundError


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
        now = datetime.utcnow().isoformat()
        
        try:
            with self.db.transaction(lock_type="global"):
                self.db.execute("""
                    INSERT INTO tq_tasks (
                        id, topic, payload, idempotency_key, 
                        max_retries, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """, (task_id, topic, payload_json, idempotency_key, max_retries, now))
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
            now = datetime.utcnow().isoformat()
            
            cursor = self.db.execute(f"""
                UPDATE tq_tasks 
                SET status = 'claimed',
                    claimed_by = ?,
                    claimed_at = ?,
                    heartbeat_at = ?,
                    started_at = ?,
                    version = version + 1
                WHERE id = (
                    SELECT id FROM tq_tasks 
                    WHERE status = 'pending' 
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
            now = datetime.utcnow().isoformat()
            
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
    ) -> str:
        """标记任务失败"""
        with self.db.transaction(lock_type="task", resource_id=task_id):
            now = datetime.utcnow().isoformat()
            
            if retry:
                cursor = self.db.execute("""
                    UPDATE tq_tasks 
                    SET status = CASE 
                            WHEN retry_count < max_retries THEN 'pending'
                            ELSE 'failed'
                        END,
                        retry_count = retry_count + 1,
                        claimed_by = NULL,
                        claimed_at = NULL,
                        heartbeat_at = NULL,
                        error = ?,
                        finished_at = CASE 
                            WHEN retry_count >= max_retries THEN ?
                            ELSE NULL
                        END
                    WHERE id = ? AND status = 'claimed'
                    RETURNING status
                """, (error, now, task_id))
                
                row = cursor.fetchone()
                cursor.close()
                
                return row[0] if row else "unknown"
            else:
                self.db.execute("""
                    UPDATE tq_tasks 
                    SET status = 'failed',
                        error = ?,
                        finished_at = ?
                    WHERE id = ? AND status = 'claimed'
                """, (error, now, task_id))
                
                return "failed"
    
    def heartbeat(self, task_id: str) -> bool:
        """更新心跳时间"""
        with self.db.transaction(lock_type="task", resource_id=task_id):
            now = datetime.utcnow().isoformat()
            
            cursor = self.db.execute("""
                UPDATE tq_tasks 
                SET heartbeat_at = ?
                WHERE id = ? AND status = 'claimed'
            """, (now, task_id))
            
            return cursor.rowcount > 0
    
    def recover_stale(self, timeout_seconds: int = 60) -> int:
        """恢复超时任务"""
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(f"""
                UPDATE tq_tasks 
                SET status = CASE 
                        WHEN retry_count < max_retries THEN 'pending'
                        ELSE 'failed'
                    END,
                    retry_count = retry_count + 1,
                    claimed_by = NULL,
                    claimed_at = NULL,
                    heartbeat_at = NULL,
                    error = CASE 
                        WHEN retry_count >= max_retries 
                        THEN 'Heartbeat timeout, max retries exceeded'
                        ELSE 'Heartbeat timeout, will retry'
                    END
                WHERE status = 'claimed'
                  AND datetime(heartbeat_at) < datetime('now', '-{timeout_seconds} seconds')
                RETURNING id
            """)
            
            rows = cursor.fetchall()
            cursor.close()
            
            return len(rows) if rows else 0
    
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
        now = datetime.utcnow().isoformat()
        
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
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        if hasattr(row, "keys"):
            result = dict(row)
        else:
            columns = [
                "id", "idempotency_key", "topic", "payload",
                "status", "claimed_by", "claimed_at", "heartbeat_at",
                "retry_count", "max_retries", "result", "error",
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
