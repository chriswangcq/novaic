"""
Saga repository/orchestrator (Gateway DB implementation).

This module holds the DB-backed SagaRepository/SagaOrchestrator so that
non-gateway code does not directly touch the database.
"""

import threading
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from task_queue.exceptions import SagaError, SagaStepError
from task_queue.saga import TaskQueueProtocol, SagaDefinition, SagaExecutor, StepType


class SagaRepository:
    """
    Saga 仓库 - Gateway 端
    
    Saga 表本身就是任务队列：
    - create(): 创建记录 (status=pending)
    - claim(): 原子认领 (和 TaskQueue 一样)
    - 不需要额外的 saga.run Task
    """
    
    def __init__(self, db, queue: Optional[TaskQueueProtocol] = None):
        """
        Args:
            db: 数据库连接
            queue: TaskQueue (可选，用于 Saga 内部发布子 Task)
        """
        self.db = db
        self.queue = queue
        self._lock = threading.Lock()
    
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
        now = datetime.utcnow().isoformat()
        
        with self._lock:
            self.db.execute("""
                INSERT INTO tq_sagas (
                    id, saga_type, context, idempotency_key,
                    current_step, status, step_results, created_at
                )
                VALUES (?, ?, ?, ?, 0, 'pending', '{}', ?)
            """, (saga_id, saga_type, json.dumps(context), idempotency_key, now))
            self.db.commit()
        
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
        now = datetime.utcnow().isoformat()
        
        with self._lock:
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
            cursor.close()  # ← 必须先关闭cursor
            self.db.commit()
        
        return self._row_to_dict(row) if row else None
    
    def heartbeat(self, saga_id: str) -> bool:
        """更新心跳"""
        now = datetime.utcnow().isoformat()
        with self._lock:
            cursor = self.db.execute("""
                UPDATE tq_sagas 
                SET heartbeat_at = ?
                WHERE id = ? AND status = 'running'
            """, (now, saga_id))
            self.db.commit()
        return cursor.rowcount > 0
    
    def recover_stale(self, timeout_seconds: int = 300) -> int:
        """恢复超时的 Saga (重置为 pending)"""
        with self._lock:
            cursor = self.db.execute(f"""
                UPDATE tq_sagas
                SET status = 'pending',
                    claimed_by = NULL,
                    claimed_at = NULL,
                    heartbeat_at = NULL
                WHERE status = 'running'
                  AND (heartbeat_at IS NULL OR heartbeat_at < datetime('now', '-{timeout_seconds} seconds'))
                RETURNING id
            """)
            rows = cursor.fetchall()
            cursor.close()  # ← 必须先关闭cursor
            self.db.commit()
        return len(rows) if rows else 0
    
    def get(self, saga_id: str) -> Optional[Dict[str, Any]]:
        """获取 Saga"""
        with self._lock:
            cursor = self.db.execute(
                "SELECT * FROM tq_sagas WHERE id = ?", (saga_id,)
            )
            row = cursor.fetchone()
        return self._row_to_dict(row) if row else None
    
    def get_by_idempotency_key(self, key: str) -> Optional[Dict[str, Any]]:
        """通过幂等键获取"""
        with self._lock:
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
        now = datetime.utcnow().isoformat()
        with self._lock:
            self.db.execute("""
                UPDATE tq_sagas 
                SET current_step = ?, step_results = ?, status = ?, updated_at = ?
                WHERE id = ?
            """, (current_step, json.dumps(step_results), status, now, saga_id))
            self.db.commit()
    
    def mark_completed(self, saga_id: str, step_results: Dict[str, Any]):
        """标记完成"""
        now = datetime.utcnow().isoformat()
        with self._lock:
            cursor = self.db.execute("""
                UPDATE tq_sagas 
                SET status = 'completed', step_results = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
            """, (json.dumps(step_results), now, now, saga_id))
            cursor.close()  # ← 必须先关闭cursor
            self.db.commit()
    
    def mark_failed(self, saga_id: str, error: str):
        """标记失败"""
        now = datetime.utcnow().isoformat()
        with self._lock:
            self.db.execute("""
                UPDATE tq_sagas 
                SET status = 'failed', error = ?, updated_at = ?
                WHERE id = ?
            """, (error, now, saga_id))
            self.db.commit()
    
    def get_pending(self) -> List[Dict[str, Any]]:
        """获取待执行/运行中的 Saga"""
        with self._lock:
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
    
    提供两种模式：
    1. 异步模式 (推荐): create() 立即返回，由 SagaWorker 执行
    2. 同步模式 (测试): start() 同步执行 (在同进程)
    """
    
    def __init__(self, queue: TaskQueueProtocol, db):
        super().__init__(db, queue)
        self._definitions: Dict[str, SagaDefinition] = {}
    
    def register(self, definition: SagaDefinition):
        """注册 Saga 定义"""
        self._definitions[definition.name] = definition
    
    def get_definition(self, saga_type: str) -> Optional[SagaDefinition]:
        """获取定义"""
        return self._definitions.get(saga_type)
    
    def start(
        self,
        saga_type: str,
        context: Dict[str, Any],
        idempotency_key: Optional[str] = None,
    ) -> str:
        """启动 Saga (同步执行，用于测试)"""
        if saga_type not in self._definitions:
            raise SagaError(f"Unknown saga type: {saga_type}")
        
        if idempotency_key:
            existing = self.get_by_idempotency_key(idempotency_key)
            if existing:
                return existing["id"]
        
        saga_id = f"saga-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        self.db.execute("""
            INSERT INTO tq_sagas (
                id, saga_type, context, idempotency_key,
                current_step, status, step_results, created_at
            )
            VALUES (?, ?, ?, ?, 0, 'running', '{}', ?)
        """, (saga_id, saga_type, json.dumps(context), idempotency_key, now))
        self.db.commit()
        
        definition = self._definitions[saga_type]
        executor = SagaExecutor(self.queue, self, self._definitions)
        
        saga = self.get(saga_id)
        step_results = saga["step_results"]
        
        for i in range(len(definition.steps)):
            step = definition.steps[i]
            
            if step.condition:
                decision = step_results.get("_decision", {})
                if not step.condition(decision):
                    continue
            
            try:
                result = executor._execute_step(saga_id, step, context, step_results)
                
                if step.step_type == StepType.DECISION:
                    step_results["_decision"] = result
                else:
                    step_results[step.name] = result
                
                self.update_progress(saga_id, i + 1, step_results)
                
            except Exception as e:
                if step.optional:
                    step_results[step.name] = {"error": str(e)}
                    self.update_progress(saga_id, i + 1, step_results)
                else:
                    self.mark_failed(saga_id, str(e))
                    raise SagaStepError(step.name, str(e), e)
        
        self.mark_completed(saga_id, step_results)
        return saga_id
    
    def resume(self, saga_id: str):
        """恢复执行"""
        saga = self.get(saga_id)
        if not saga or saga["status"] not in ("pending", "running"):
            return
        
        self.update_progress(saga_id, saga["current_step"], saga["step_results"], "running")
        
        definition = self._definitions.get(saga["saga_type"])
        if not definition:
            return
        
        executor = SagaExecutor(self.queue, self, self._definitions)
        context = saga["context"]
        step_results = saga["step_results"]
        
        for i in range(saga["current_step"], len(definition.steps)):
            step = definition.steps[i]
            
            if step.condition:
                decision = step_results.get("_decision", {})
                if not step.condition(decision):
                    continue
            
            try:
                result = executor._execute_step(saga_id, step, context, step_results)
                
                if step.step_type == StepType.DECISION:
                    step_results["_decision"] = result
                else:
                    step_results[step.name] = result
                
                self.update_progress(saga_id, i + 1, step_results)
                
            except Exception as e:
                if step.optional:
                    step_results[step.name] = {"error": str(e)}
                    self.update_progress(saga_id, i + 1, step_results)
                else:
                    self.mark_failed(saga_id, str(e))
                    raise
        
        self.mark_completed(saga_id, step_results)
    
    def get_pending_sagas(self) -> List[Dict[str, Any]]:
        """获取待执行的 Saga (兼容旧接口)"""
        return self.get_pending()
    
    def _get_saga(self, saga_id: str) -> Optional[Dict[str, Any]]:
        return self.get(saga_id)
