"""
Task Queue API Routes

暴露 TaskQueue 和 Saga 的 HTTP API，供 Worker 进程调用。
所有数据库操作集中在 Gateway 进程。
"""

from typing import Optional, List, Dict, Any
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .queue import TaskQueue
from .saga import SagaOrchestrator
from .exceptions import TaskNotFoundError, SagaError

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
    async def publish_task(req: PublishRequest):
        """发布任务"""
        task_id = await queue.publish(
            topic=req.topic,
            payload=req.payload,
            idempotency_key=req.idempotency_key,
            max_retries=req.max_retries,
        )
        return PublishResponse(task_id=task_id)
    
    @router.post("/tasks/claim", response_model=ClaimResponse)
    async def claim_task(req: ClaimRequest):
        """认领任务"""
        task = await queue.claim(
            topics=req.topics,
            worker_id=req.worker_id,
        )
        return ClaimResponse(task=task)
    
    @router.post("/tasks/{task_id}/complete", response_model=SuccessResponse)
    async def complete_task(task_id: str, req: CompleteRequest):
        """标记任务完成"""
        success = await queue.complete(task_id, req.result)
        if not success:
            logger.warning("[TaskQueue] Complete failed (task_id=%s)", task_id)
        else:
            logger.info("[TaskQueue] Task completed (task_id=%s)", task_id)
        return SuccessResponse(success=success)
    
    @router.post("/tasks/{task_id}/fail", response_model=StatusResponse)
    async def fail_task(task_id: str, req: FailRequest):
        """标记任务失败"""
        final_status = await queue.fail(task_id, req.error, req.retry)
        logger.warning(
            "[TaskQueue] Task failed (task_id=%s, final_status=%s, retry=%s)",
            task_id,
            final_status,
            req.retry,
        )
        return StatusResponse(final_status=final_status)
    
    @router.post("/tasks/{task_id}/heartbeat", response_model=SuccessResponse)
    async def heartbeat_task(task_id: str):
        """更新心跳"""
        success = await queue.heartbeat(task_id)
        return SuccessResponse(success=success)
    
    @router.get("/tasks/{task_id}", response_model=TaskResponse)
    async def get_task(task_id: str):
        """获取任务详情"""
        task = await queue.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskResponse(task=task)
    
    @router.get("/tasks/stats", response_model=StatsResponse)
    async def get_task_stats(topic: Optional[str] = None):
        """获取任务统计"""
        counts = await queue.count_by_status(topic)
        return StatsResponse(counts=counts)
    
    # ========================================
    # Saga APIs (if orchestrator provided)
    # ========================================
    
    if orchestrator:
        @router.post("/sagas/start", response_model=SagaStartResponse)
        async def start_saga(req: SagaStartRequest):
            """创建 Saga (立即返回，由 SagaWorker 执行)"""
            try:
                saga_id = await orchestrator.create(
                    saga_type=req.saga_type,
                    context=req.context,
                    idempotency_key=req.idempotency_key,
                )
                return SagaStartResponse(saga_id=saga_id)
            except SagaError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @router.post("/sagas/claim", response_model=SagaClaimResponse)
        async def claim_saga(req: SagaClaimRequest):
            """认领 Saga (SagaWorker 调用)"""
            saga = await orchestrator.claim(
                saga_types=req.saga_types,
                worker_id=req.worker_id,
            )
            return SagaClaimResponse(saga=saga)
        
        @router.get("/sagas/{saga_id}", response_model=SagaResponse)
        async def get_saga(saga_id: str):
            """获取 Saga 状态"""
            saga = await orchestrator.get(saga_id)
            if not saga:
                raise HTTPException(status_code=404, detail="Saga not found")
            return SagaResponse(saga=saga)
        
        @router.post("/sagas/{saga_id}/heartbeat", response_model=SuccessResponse)
        async def heartbeat_saga(saga_id: str):
            """更新 Saga 心跳 (SagaWorker 调用)"""
            success = await orchestrator.heartbeat(saga_id)
            return SuccessResponse(success=success)
        
        @router.post("/sagas/{saga_id}/progress", response_model=SuccessResponse)
        async def update_saga_progress(saga_id: str, req: SagaProgressRequest):
            """更新 Saga 进度 (Saga Worker 调用)"""
            await orchestrator.update_progress(
                saga_id=saga_id,
                current_step=req.current_step,
                step_results=req.step_results,
                status=req.status,
            )
            return SuccessResponse(success=True)
        
        @router.post("/sagas/{saga_id}/complete", response_model=SuccessResponse)
        async def complete_saga(saga_id: str, req: SagaCompleteRequest):
            """标记 Saga 完成 (Saga Worker 调用)"""
            await orchestrator.mark_completed(saga_id, req.step_results)
            return SuccessResponse(success=True)
        
        @router.post("/sagas/{saga_id}/fail", response_model=SuccessResponse)
        async def fail_saga(saga_id: str, req: SagaFailRequest):
            """标记 Saga 失败 (Saga Worker 调用)"""
            await orchestrator.mark_failed(saga_id, req.error)
            return SuccessResponse(success=True)
        
        @router.post("/sagas/{saga_id}/resume", response_model=SuccessResponse)
        async def resume_saga(saga_id: str):
            """恢复 Saga (发布 saga.run Task)"""
            try:
                await orchestrator.resume(saga_id)
                return SuccessResponse(success=True)
            except SagaError as e:
                raise HTTPException(status_code=400, detail=str(e))
    
    return router


# ============================================================
# Handler Execution API
# ============================================================

class HandlerExecRequest(BaseModel):
    topic: str
    payload: Dict[str, Any]


class HandlerExecResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def create_handler_router(get_context_func) -> APIRouter:
    """
    创建 Handler 执行 API 路由
    
    Handler 在 Gateway 中执行（因为需要直接访问 DB）
    Worker 通过 HTTP 调用此 API 执行 Handler
    
    异常处理：
    - RetryableError: 基础设施故障 → HTTP 503 → TaskWorker 重试
    - 其他异常: 业务失败 → HTTP 200 + success=True + result 包含错误信息
    
    Args:
        get_context_func: 获取 Handler 上下文的函数
        
    Returns:
        router: FastAPI Router
    """
    from .handlers import get_handler
    from .exceptions import RetryableError
    
    router = APIRouter(tags=["Handler Execution"])
    
    @router.post("/execute", response_model=HandlerExecResponse)
    async def execute_handler(req: HandlerExecRequest):
        """
        执行 Handler
        
        返回值：
        - 200 + success=True + result: Handler 正常返回（业务成功或业务失败都在 result 里）
        - 503: 基础设施故障，TaskWorker 应该重试
        - 404: Handler 不存在
        """
        try:
            handler = get_handler(req.topic)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        ctx = get_context_func()
        
        try:
            result = await handler(req.payload, ctx)
            return HandlerExecResponse(
                success=True,
                result=result,
            )
        except RetryableError as e:
            # 基础设施故障 → HTTP 503 → TaskWorker 重试
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            # 业务失败 → 返回结果（不是错误），让 Saga 处理
            return HandlerExecResponse(
                success=True,
                result={"success": False, "error": str(e)},
            )
    
    @router.get("/topics")
    async def list_topics():
        """列出所有可用的 Handler topics"""
        from .handlers import get_all_topics
        return {"topics": get_all_topics()}
    
    return router


# ============================================================
# Business Entry API
# ============================================================

class MessageProcessRequest(BaseModel):
    message_id: str
    agent_id: str
    content: str
    subagent_id: Optional[str] = None


class MessageProcessResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    saga_id: Optional[str] = None
    runtime_id: Optional[str] = None
    error: Optional[str] = None


def create_business_router(
    orchestrator: Optional[SagaOrchestrator],
    get_context_func,
) -> APIRouter:
    """
    创建业务入口 API 路由
    
    提供高层业务接口，如消息处理入口
    
    Args:
        orchestrator: SagaOrchestrator 实例
        get_context_func: 获取 Handler 上下文的函数
        
    Returns:
        router: FastAPI Router
    """
    router = APIRouter(tags=["Business Entry"])
    
    @router.post("/message/process", response_model=MessageProcessResponse)
    async def process_message(req: MessageProcessRequest):
        """
        处理用户消息 - 业务入口
        
        流程：
        1. 检查 SubAgent 状态
        2. 唤醒 SubAgent（如果需要）
        3. 启动 RuntimeStart Saga
        """
        from .handlers import get_handler
        
        ctx = get_context_func()
        
        # 使用 message.process handler
        try:
            handler = get_handler("message.process")
            
            # 注入 saga_client（使用 orchestrator）
            ctx_with_saga = {**ctx, "saga_client": orchestrator}
            
            result = await handler({
                "message_id": req.message_id,
                "agent_id": req.agent_id,
                "content": req.content,
                "subagent_id": req.subagent_id,
            }, ctx_with_saga)
            
            return MessageProcessResponse(
                success=result.get("success", False),
                action=result.get("action"),
                saga_id=result.get("saga_id"),
                runtime_id=result.get("runtime_id"),
                error=result.get("error"),
            )
            
        except Exception as e:
            return MessageProcessResponse(
                success=False,
                error=str(e),
            )
    
    return router


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
    async def recover_stale_tasks(timeout_seconds: int = 60):
        """恢复超时任务"""
        recovered = await queue.recover_stale(timeout_seconds)
        return RecoveryResponse(tasks_recovered=recovered)
    
    if orchestrator:
        @router.post("/sagas", response_model=RecoveryResponse)
        async def recover_stale_sagas(timeout_seconds: int = 120):
            """恢复超时 Saga"""
            recovered = await orchestrator.recover_stale(timeout_seconds)
            return RecoveryResponse(sagas_recovered=recovered)
    
    @router.post("/all", response_model=RecoveryResponse)
    async def recover_all(
        task_timeout: int = 60,
        saga_timeout: int = 120,
    ):
        """恢复所有超时任务和 Saga"""
        tasks_recovered = await queue.recover_stale(task_timeout)
        sagas_recovered = 0
        if orchestrator:
            sagas_recovered = await orchestrator.recover_stale(saga_timeout)
        return RecoveryResponse(
            tasks_recovered=tasks_recovered,
            sagas_recovered=sagas_recovered,
        )
    
    return router
