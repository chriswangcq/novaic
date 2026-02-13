"""
Task Queue 单例管理 (v3)

提供 TaskQueue、SagaOrchestrator 的全局单例访问。
在 Gateway 启动时初始化，供 API routes 使用。

v3 变更：
- 使用 queue_service.saga_repo 中的 SagaOrchestrator
"""

from typing import Optional, Dict, Any

from .queue import TaskQueue
from queue_service.saga_repo import SagaOrchestrator, SagaRepository
from .sagas import get_all_saga_definitions

# 全局单例
_task_queue: Optional[TaskQueue] = None
_saga_orchestrator: Optional[SagaOrchestrator] = None
_handler_context: Dict[str, Any] = {}


async def init_task_queue(db) -> TaskQueue:
    """
    初始化 TaskQueue 单例
    
    Args:
        db: 数据库连接
        
    Returns:
        TaskQueue 实例
    """
    global _task_queue
    
    if _task_queue is None:
        _task_queue = TaskQueue(db)
        print("[TaskQueue] Initialized")
    
    return _task_queue


async def init_saga_orchestrator(db) -> SagaOrchestrator:
    """
    初始化 SagaOrchestrator 单例
    
    Args:
        db: 数据库连接
        
    Returns:
        SagaOrchestrator 实例
    """
    global _saga_orchestrator, _task_queue
    
    if _saga_orchestrator is None:
        if _task_queue is None:
            _task_queue = TaskQueue(db)
        
        _saga_orchestrator = SagaOrchestrator(_task_queue, db)
        
        # 注册所有 Saga 定义
        for saga_def in get_all_saga_definitions():
            _saga_orchestrator.register(saga_def)
            print(f"[Saga] Registered: {saga_def.name} ({len(saga_def.steps)} steps)")
        
        print("[SagaOrchestrator] Initialized")
    
    return _saga_orchestrator


def set_handler_context(ctx: Dict[str, Any]):
    """
    设置 Handler 执行上下文
    
    Args:
        ctx: 上下文字典，包含 db, mcp_manager, llm_client 等
    """
    global _handler_context
    _handler_context = ctx
    print(f"[Handler] Context set: {list(ctx.keys())}")


def get_handler_context() -> Dict[str, Any]:
    """获取 Handler 执行上下文"""
    return _handler_context


def get_task_queue() -> Optional[TaskQueue]:
    """获取 TaskQueue 单例"""
    return _task_queue


def get_saga_orchestrator() -> Optional[SagaOrchestrator]:
    """获取 SagaOrchestrator 单例"""
    return _saga_orchestrator


async def shutdown_task_queue():
    """关闭 TaskQueue（清理资源）"""
    global _task_queue, _saga_orchestrator, _handler_context
    
    _task_queue = None
    _saga_orchestrator = None
    _handler_context = {}
    
    print("[TaskQueue] Shutdown")
