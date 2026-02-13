"""
Saga repository/orchestrator (Gateway DB implementation).

This module holds the DB-backed SagaRepository/SagaOrchestrator so that
non-gateway code does not directly touch the database.

v3 变更：
- 删除对异步 SagaExecutor 的依赖
- SagaOrchestrator 仅用于测试，内联同步执行逻辑
"""

import json
import uuid
from typing import Optional, Dict, Any, List

from queue_service.exceptions import SagaError, SagaStepError
from common.utils.time import utc_now_iso
from task_queue.saga import SagaDefinition, StepType


class SagaRepository:
    """
    Saga 仓库 - Gateway 端
    
    Saga 表本身就是任务队列：
    - create(): 创建记录 (status=pending)
    - claim(): 原子认领 (和 TaskQueue 一样)
    - 不需要额外的 saga.run Task
    """
    
    def __init__(self, db, queue=None):
        """
        Args:
            db: 数据库连接
            queue: TaskQueue (可选，用于 Saga 内部发布子 Task)
        """
        self.db = db
        self.queue = queue
    
    def create(
        self,
        saga_type: str,
        context: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> str:
        """
        创建 Saga (只创建记录，不发布 Task)
        """
        if idempotency_key:
            existing = self.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing["id"]
        
        saga_id = f"saga-{uuid.uuid4().hex[:12]}"
        now = utc_now_iso()
        
        with self.db.transaction(lock_type="global"):
            self.db.execute("""
                INSERT INTO tq_sagas (
                    id, saga_type, context, idempotency_key,
                    current_step, status, step_results, created_at
                )
                VALUES (?, ?, ?, ?, 0, 'pending', '{}', ?)
            """, (saga_id, saga_type, json.dumps(context), idempotency_key, now))
        
        return saga_id
    
    def claim(
        self,
        saga_types: List[str],
        worker_id: str,
    ) -> Optional[Dict[str, Any]]:
        """原子认领一个 pending 状态的 Saga (CAS)"""
        if not saga_types:
            return None
        
        type_placeholders = ",".join("?" * len(saga_types))
        now = utc_now_iso()
        
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(f"""
                UPDATE tq_sagas 
                SET status = 'running',
                    claimed_by = ?,
                    claimed_at = ?,
                    heartbeat_at = ?
                WHERE id = (
                    SELECT id FROM tq_sagas 
                    WHERE status = 'pending' 
                      AND saga_type IN ({type_placeholders})
                    ORDER BY created_at
                    LIMIT 1
                )
                RETURNING *
            """, (worker_id, now, now, *saga_types))
            
            row = cursor.fetchone()
            cursor.close()
        
        return self._row_to_dict(row) if row else None
    
    def heartbeat(self, saga_id: str) -> bool:
        """更新心跳"""
        now = utc_now_iso()
        with self.db.transaction(lock_type="saga", resource_id=saga_id):
            cursor = self.db.execute("""
                UPDATE tq_sagas 
                SET heartbeat_at = ?
                WHERE id = ? AND status = 'running'
            """, (now, saga_id))
        return cursor.rowcount > 0
    
    def recover_stale(self, timeout_seconds: int = 300) -> int:
        """恢复超时的 Saga (重置为 pending)"""
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(f"""
                UPDATE tq_sagas
                SET status = 'pending',
                    claimed_by = NULL,
                    claimed_at = NULL,
                    heartbeat_at = NULL
                WHERE status = 'running'
                  AND (heartbeat_at IS NULL OR datetime(heartbeat_at) < datetime('now', '-{timeout_seconds} seconds'))
                RETURNING id
            """)
            rows = cursor.fetchall()
            cursor.close()
        return len(rows) if rows else 0
    
    def get(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """获取 Saga"""
        with self.db.transaction(lock_type="saga", resource_id=saga_id):
            cursor = self.db.execute(
                "SELECT * FROM tq_sagas WHERE id = ?", (saga_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def get_by_idempotency_key(self, key: str) -> Optional[Dict[str, Any]]:
        """通过幂等键获取"""
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(
                "SELECT * FROM tq_sagas WHERE idempotency_key = ?", (key,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def update_progress(
        self,
        saga_id: str,
        current_step: int,
        step_results: Dict[str, Any],
        status: str = "running",
    ):
        """更新进度"""
        now = utc_now_iso()
        with self.db.transaction(lock_type="saga", resource_id=saga_id):
            self.db.execute("""
                UPDATE tq_sagas 
                SET current_step = ?, step_results = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (current_step, json.dumps(step_results), status, now, saga_id))
    
    def mark_completed(self, saga_id: str, step_results: Dict[str, Any]):
        """标记完成"""
        now = utc_now_iso()
        with self.db.transaction(lock_type="saga", resource_id=saga_id):
            cursor = self.db.execute("""
                UPDATE tq_sagas 
                SET status = 'completed', step_results = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
            """, (json.dumps(step_results), now, now, saga_id))
            cursor.close()
    
    def mark_failed(self, saga_id: str, error: str):
        """标记失败"""
        now = utc_now_iso()
        with self.db.transaction(lock_type="saga", resource_id=saga_id):
            self.db.execute("""
                UPDATE tq_sagas 
                SET status = 'failed', error = ?, updated_at = ?
                WHERE id = ?
            """, (error, now, saga_id))
    
    def release(self, saga_id: str, reason: str = "") -> bool:
        """
        释放 Saga 回 pending 状态（用于可重试错误）
        
        Args:
            saga_id: Saga ID
            reason: 释放原因（用于日志）
            
        Returns:
            是否成功释放
        """
        now = utc_now_iso()
        with self.db.transaction(lock_type="saga", resource_id=saga_id):
            cursor = self.db.execute("""
                UPDATE tq_sagas 
                SET status = 'pending',
                    claimed_by = NULL,
                    claimed_at = NULL,
                    heartbeat_at = NULL,
                    updated_at = ?
                WHERE id = ? AND status = 'running'
            """, (now, saga_id))
            success = cursor.rowcount > 0
            cursor.close()
        return success
    
    def get_pending(self) -> List[Dict[str, Any]]:
        """获取待执行/运行中的 Saga"""
        with self.db.transaction(lock_type="global"):
            cursor = self.db.execute(
                "SELECT * FROM tq_sagas WHERE status IN ('pending', 'running') ORDER BY created_at"
            )
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
    
    def start(
        self,
        saga_type: str,
        context: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> str:
        """启动 Saga (兼容接口)"""
        return self.create(saga_type, context, idempotency_key)
    
    def cancel_all(self, agent_id: Optional[str] = None) -> int:
        """
        取消所有 pending/running 状态的 Saga
        
        Args:
            agent_id: 可选，只取消指定 agent 的 saga（通过 context 中的 agent_id 字段）
            
        Returns:
            取消的 saga 数量
        """
        now = utc_now_iso()
        
        with self.db.transaction(lock_type="global"):
            if agent_id:
                # 取消指定 agent 的 saga
                cursor = self.db.execute("""
                    UPDATE tq_sagas 
                    SET status = 'cancelled',
                        error = 'Cancelled by interrupt',
                        updated_at = ?
                    WHERE status IN ('pending', 'running')
                      AND context LIKE ?
                    RETURNING id
                """, (now, f'%"agent_id":"{agent_id}"%'))
            else:
                # 取消所有 saga
                cursor = self.db.execute("""
                    UPDATE tq_sagas 
                    SET status = 'cancelled',
                        error = 'Cancelled by interrupt',
                        updated_at = ?
                    WHERE status IN ('pending', 'running')
                    RETURNING id
                """, (now,))
            
            rows = cursor.fetchall()
            cursor.close()
            
            return len(rows) if rows else 0
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """行转字典"""
        if hasattr(row, "keys"):
            result = dict(row)
        else:
            columns = [
                "id", "saga_type", "context", "idempotency_key",
                "current_step", "status", "step_results", "error",
                "created_at", "updated_at", "completed_at"
            ]
            result = dict(zip(columns, row))
        
        for field in ("context", "step_results"):
            if result.get(field):
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    if field == "step_results":
                        result[field] = {}
        
        return result


class SagaOrchestrator(SagaRepository):
    """
    兼容旧接口的 Saga 协调器 (用于测试)
    
    注意：此类仅用于测试目的，生产环境使用 SagaWorkerSync
    """
    
    def __init__(self, queue, db):
        super().__init__(db, queue)
        self._definitions: Dict[str, SagaDefinition] = {}
    
    def register(self, definition: SagaDefinition):
        """注册 Saga 定义"""
        self._definitions[definition.name] = definition
    
    def get_definition(self, saga_type: str) -> Optional[SagaDefinition]:
        """获取定义"""
        return self._definitions.get(saga_type)
    
    def get_pending_sagas(self) -> List[Dict[str, Any]]:
        """获取待执行的 Saga (兼容旧接口)"""
        return self.get_pending()
    
    def _get_saga(self, saga_id: str) -> Optional[Dict[str, Any]]:
        return self.get(saga_id)
