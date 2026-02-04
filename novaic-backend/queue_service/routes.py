"""
Task Queue API Routes

暴露 TaskQueue 和 Saga 的 HTTP API，供 Worker 进程调用。
所有数据库操作集中在 Gateway 进程。
"""

from typing import Optional, List, Dict, Any
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from queue_service.queue_db import TaskQueue
from queue_service.saga_repo import SagaRepository, SagaOrchestrator
from queue_service.exceptions import TaskNotFoundError, SagaError

logger = logging.getLogger(__name__)


# ============================================================
# Request/Response Models
# ============================================================

class PublishRequest(BaseModel):
    topic: str
    payload: Dict[str, Any]
    idempotency_key: Optional[str] = None
    max_retries: int = 3


class PublishResponse(BaseModel):
    task_id: str


class ClaimRequest(BaseModel):
    topics: List[str]
    worker_id: str


class ClaimResponse(BaseModel):
    task: Optional[Dict[str, Any]] = None


class CompleteRequest(BaseModel):
    result: Optional[Dict[str, Any]] = None


class FailRequest(BaseModel):
    error: str
    retry: bool = True


class SuccessResponse(BaseModel):
    success: bool


class StatusResponse(BaseModel):
    final_status: str


class TaskResponse(BaseModel):
    task: Optional[Dict[str, Any]] = None


class SagaStartRequest(BaseModel):
    saga_type: str
    context: Dict[str, Any]
    idempotency_key: Optional[str] = None


class SagaStartResponse(BaseModel):
    saga_id: str


class SagaClaimRequest(BaseModel):
    saga_types: List[str]
    worker_id: str


class SagaClaimResponse(BaseModel):
    saga: Optional[Dict[str, Any]] = None


class SagaResponse(BaseModel):
    saga: Optional[Dict[str, Any]] = None


class SagaProgressRequest(BaseModel):
    current_step: int
    step_results: Dict[str, Any]
    status: str = "running"


class SagaCompleteRequest(BaseModel):
    step_results: Dict[str, Any]


class SagaFailRequest(BaseModel):
    error: str


class StatsResponse(BaseModel):
    counts: Dict[str, int]


# ============================================================
# Router Factory
# ============================================================

def create_task_queue_router(
    queue: TaskQueue,
    orchestrator: Optional[SagaOrchestrator] = None,
) -> APIRouter:
    """
    创建 Task Queue API 路由
    
    Args:
        queue: TaskQueue 实例
        orchestrator: SagaOrchestrator 实例（可选）
        
    Returns:
        router: FastAPI Router
        
    Usage:
        queue = TaskQueue(db)
        orchestrator = SagaOrchestrator(queue, db)
        router = create_task_queue_router(queue, orchestrator)
        app.include_router(router, prefix="/internal/tq")
    """
    router = APIRouter(tags=["Task Queue"])
    
    # ========================================
    # Task APIs
    # ========================================
    
    @router.post("/tasks/publish", response_model=PublishResponse)
    def publish_task(req: PublishRequest):
        """发布任务"""
        task_id = queue.publish(
            topic=req.topic,
            payload=req.payload,
            idempotency_key=req.idempotency_key,
            max_retries=req.max_retries,
        )
        return PublishResponse(task_id=task_id)
    
    @router.post("/tasks/claim", response_model=ClaimResponse)
    def claim_task(req: ClaimRequest):
        """认领任务"""
        task = queue.claim(
            topics=req.topics,
            worker_id=req.worker_id,
        )
        return ClaimResponse(task=task)
    
    @router.post("/tasks/{task_id}/complete", response_model=SuccessResponse)
    def complete_task(task_id: str, req: CompleteRequest):
        """标记任务完成"""
        success = queue.complete(task_id, req.result)
        if not success:
            logger.warning("[TaskQueue] Complete failed (task_id=%s)", task_id)
        else:
            logger.info("[TaskQueue] Task completed (task_id=%s)", task_id)
        return SuccessResponse(success=success)
    
    @router.post("/tasks/{task_id}/fail", response_model=StatusResponse)
    def fail_task(task_id: str, req: FailRequest):
        """标记任务失败"""
        final_status = queue.fail(task_id, req.error, req.retry)
        logger.warning(
            "[TaskQueue] Task failed (task_id=%s, final_status=%s, retry=%s)",
            task_id,
            final_status,
            req.retry,
        )
        return StatusResponse(final_status=final_status)
    
    @router.post("/tasks/{task_id}/heartbeat", response_model=SuccessResponse)
    def heartbeat_task(task_id: str):
        """更新心跳"""
        success = queue.heartbeat(task_id)
        return SuccessResponse(success=success)
    
    @router.get("/tasks/{task_id}", response_model=TaskResponse)
    def get_task(task_id: str):
        """获取任务详情"""
        task = queue.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskResponse(task=task)
    
    @router.get("/tasks/stats", response_model=StatsResponse)
    def get_task_stats(topic: Optional[str] = None):
        """获取任务统计"""
        counts = queue.count_by_status(topic)
        return StatsResponse(counts=counts)
    
    @router.get("/topics")
    def get_topics():
        """获取所有已知的 topics (Task Worker 启动时调用)"""
        topics = queue.get_topics()
        return {"topics": topics, "count": len(topics)}
    
    # ========================================
    # Saga APIs (if orchestrator provided)
    # ========================================
    
    if orchestrator:
        @router.post("/sagas/start", response_model=SagaStartResponse)
        def start_saga(req: SagaStartRequest):
            """创建 Saga (立即返回，由 SagaWorker 执行)"""
            try:
                saga_id = orchestrator.create(
                    saga_type=req.saga_type,
                    context=req.context,
                    idempotency_key=req.idempotency_key,
                )
                return SagaStartResponse(saga_id=saga_id)
            except SagaError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @router.post("/sagas/claim", response_model=SagaClaimResponse)
        def claim_saga(req: SagaClaimRequest):
            """认领 Saga (SagaWorker 调用)"""
            saga = orchestrator.claim(
                saga_types=req.saga_types,
                worker_id=req.worker_id,
            )
            return SagaClaimResponse(saga=saga)
        
        @router.get("/sagas/{saga_id}", response_model=SagaResponse)
        def get_saga(saga_id: str):
            """获取 Saga 状态"""
            saga = orchestrator.get(saga_id)
            if not saga:
                raise HTTPException(status_code=404, detail="Saga not found")
            return SagaResponse(saga=saga)
        
        @router.post("/sagas/{saga_id}/heartbeat", response_model=SuccessResponse)
        def heartbeat_saga(saga_id: str):
            """更新 Saga 心跳 (SagaWorker 调用)"""
            success = orchestrator.heartbeat(saga_id)
            return SuccessResponse(success=success)
        
        @router.post("/sagas/{saga_id}/progress", response_model=SuccessResponse)
        def update_saga_progress(saga_id: str, req: SagaProgressRequest):
            """更新 Saga 进度 (Saga Worker 调用)"""
            orchestrator.update_progress(
                saga_id=saga_id,
                current_step=req.current_step,
                step_results=req.step_results,
                status=req.status,
            )
            return SuccessResponse(success=True)
        
        @router.post("/sagas/{saga_id}/complete", response_model=SuccessResponse)
        def complete_saga(saga_id: str, req: SagaCompleteRequest):
            """标记 Saga 完成 (Saga Worker 调用)"""
            orchestrator.mark_completed(saga_id, req.step_results)
            return SuccessResponse(success=True)
        
        @router.post("/sagas/{saga_id}/fail", response_model=SuccessResponse)
        def fail_saga(saga_id: str, req: SagaFailRequest):
            """标记 Saga 失败 (Saga Worker 调用)"""
            orchestrator.mark_failed(saga_id, req.error)
            return SuccessResponse(success=True)
        
        @router.post("/sagas/{saga_id}/resume", response_model=SuccessResponse)
        def resume_saga(saga_id: str):
            """恢复 Saga (发布 saga.run Task)"""
            try:
                orchestrator.resume(saga_id)
                return SuccessResponse(success=True)
            except SagaError as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    return router


# ============================================================
# Handler Execution API - 已移至 Gateway
# ============================================================
#
# v2.1: Handler 执行 API 由 Gateway 提供
# 端点: POST /internal/tq/handlers/execute
# 
# Queue Service 是纯调度中间件，不执行业务逻辑
#


# ============================================================
# Business Entry API - 已移至 Gateway
# ============================================================
#
# v2.1: 业务入口 API 由 Gateway 提供
# Queue Service 是纯调度中间件，不处理业务入口
#


# ============================================================
# Recovery API (for HealthMonitor)
# ============================================================

class RecoveryResponse(BaseModel):
    tasks_recovered: int = 0
    sagas_recovered: int = 0


def create_recovery_router(
    queue: TaskQueue,
    orchestrator: Optional[SagaOrchestrator] = None,
) -> APIRouter:
    """
    创建恢复 API 路由（供 HealthMonitor 调用）
    
    Args:
        queue: TaskQueue 实例
        orchestrator: SagaOrchestrator 实例（可选）
        
    Returns:
        router: FastAPI Router
    """
    router = APIRouter(tags=["Task Queue Recovery"])
    
    @router.post("/tasks", response_model=RecoveryResponse)
    def recover_stale_tasks(timeout_seconds: int = 60):
        """恢复超时任务"""
        recovered = queue.recover_stale(timeout_seconds)
        return RecoveryResponse(tasks_recovered=recovered)
    
    if orchestrator:
        @router.post("/sagas", response_model=RecoveryResponse)
        def recover_stale_sagas(timeout_seconds: int = 120):
            """恢复超时 Saga"""
            recovered = orchestrator.recover_stale(timeout_seconds)
            return RecoveryResponse(sagas_recovered=recovered)
    
    @router.post("/all", response_model=RecoveryResponse)
    def recover_all(
        task_timeout: int = 60,
        saga_timeout: int = 120,
    ):
        """恢复所有超时任务和 Saga"""
        tasks_recovered = queue.recover_stale(task_timeout)
        sagas_recovered = 0
        if orchestrator:
            sagas_recovered = orchestrator.recover_stale(saga_timeout)
        return RecoveryResponse(
            tasks_recovered=tasks_recovered,
            sagas_recovered=sagas_recovered,
        )
    
    @router.post("/cancel-all")
    def cancel_all(agent_id: Optional[str] = None):
        """
        取消所有 pending/running 的任务和 Saga
        
        用于 interrupt 操作，由 Watchdog 调用。
        
        Args:
            agent_id: 可选，只取消指定 agent 的任务/sagas
            
        Returns:
            cancelled_tasks: 取消的任务数
            cancelled_sagas: 取消的 saga 数
        """
        cancelled_tasks = queue.cancel_all(agent_id)
        cancelled_sagas = 0
        if orchestrator:
            cancelled_sagas = orchestrator.cancel_all(agent_id)
        return {
            "cancelled_tasks": cancelled_tasks,
            "cancelled_sagas": cancelled_sagas,
        }
    
    return router
