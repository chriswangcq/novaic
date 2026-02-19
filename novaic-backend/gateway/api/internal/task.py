"""
Internal API module: task

Only quadrant task APIs are kept.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from gateway.db.access import get_db
from .helpers import resolve_agent_id_from_subagent

router = APIRouter(tags=["internal"])


# ==================== Four-Quadrant Task API (四象限任务系统) ====================
# Internal API for tools_server to manage quadrant tasks


class QuadrantTaskCreateRequest(BaseModel):
    title: str
    task_type: Optional[str] = "one_time"  # one_time/recurring/ongoing
    quadrant: str  # q1/q2/q3/q4
    source: str
    description: Optional[str] = ""
    reasoning: Optional[str] = None
    due_date: Optional[str] = None
    context: Optional[str] = None
    related_profile_keys: Optional[List[str]] = None


class QuadrantTaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    quadrant: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None


class QuadrantTaskCompleteRequest(BaseModel):
    notes: Optional[str] = None


class GrowthLogRequest(BaseModel):
    content: str
    category: Optional[str] = "learning"


@router.post("/subagents/{subagent_id}/quadrant-tasks")
def create_quadrant_task(subagent_id: str, request: QuadrantTaskCreateRequest):
    """创建四象限任务
    
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.create(
        agent_id=agent_id,
        title=request.title,
        task_type=request.task_type or "one_time",
        quadrant=request.quadrant,
        source=request.source,
        description=request.description or "",
        reasoning=request.reasoning,
        due_date=request.due_date,
        context=request.context,
        related_profile_keys=request.related_profile_keys,
    )


@router.get("/subagents/{subagent_id}/quadrant-tasks")
def list_quadrant_tasks(
    subagent_id: str,
    quadrant: Optional[str] = None,
    status: Optional[str] = "pending",
    limit: int = 20,
):
    """列出四象限任务
    
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.list_by_quadrant(
        agent_id=agent_id,
        quadrant=quadrant,
        status=status,
        limit=limit,
    )


@router.get("/subagents/{subagent_id}/quadrant-tasks/board")
def get_quadrant_board(subagent_id: str):
    """获取四象限任务看板摘要
    
    供 tools_server 调用的内部 API。
    返回按象限分组的活跃任务。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.get_board_summary(agent_id=agent_id)


@router.get("/subagents/{subagent_id}/quadrant-tasks/{task_id}")
def get_quadrant_task(subagent_id: str, task_id: int):
    """获取单个四象限任务详情
    
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.get(agent_id=agent_id, task_id=task_id)


@router.patch("/subagents/{subagent_id}/quadrant-tasks/{task_id}")
def update_quadrant_task(subagent_id: str, task_id: int, request: QuadrantTaskUpdateRequest):
    """更新四象限任务
    
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.update(
        agent_id=agent_id,
        task_id=task_id,
        status=request.status,
        quadrant=request.quadrant,
        title=request.title,
        description=request.description,
        due_date=request.due_date,
    )


@router.post("/subagents/{subagent_id}/quadrant-tasks/{task_id}/complete")
def complete_quadrant_task(subagent_id: str, task_id: int, request: QuadrantTaskCompleteRequest):
    """完成四象限任务
    
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.complete(
        agent_id=agent_id,
        task_id=task_id,
        notes=request.notes,
    )


@router.delete("/subagents/{subagent_id}/quadrant-tasks/{task_id}")
def delete_quadrant_task(subagent_id: str, task_id: int):
    """删除四象限任务
    
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.delete(agent_id=agent_id, task_id=task_id)


@router.post("/subagents/{subagent_id}/quadrant-tasks/{task_id}/start")
def start_quadrant_task(subagent_id: str, task_id: int):
    """开始执行四象限任务
    
    将任务状态设为 in_progress 并返回任务详情。
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.start_task(agent_id=agent_id, task_id=task_id)


class TaskProgressRequest(BaseModel):
    note: str
    set_ongoing: bool = False


@router.post("/subagents/{subagent_id}/quadrant-tasks/{task_id}/progress")
def add_task_progress(subagent_id: str, task_id: int, request: TaskProgressRequest):
    """记录任务进展
    
    用于持续性任务，记录阶段性进展。
    供 tools_server 调用的内部 API。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.task import TaskRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = TaskRepository(db)
    
    return repo.add_progress(
        agent_id=agent_id,
        task_id=task_id,
        note=request.note,
        set_ongoing=request.set_ongoing,
    )


@router.post("/subagents/{subagent_id}/growth-logs")
def log_growth(subagent_id: str, request: GrowthLogRequest):
    """记录成长日志
    
    供 tools_server 调用的内部 API。
    存储到 agent_drive.growth_log JSON 字段（如果存在）或 notebook。
    Gateway business API: subagent_id-only input, no runtime lookup.
    """
    from gateway.db.repositories.notebook import NotebookRepository
    
    agent_id = resolve_agent_id_from_subagent(subagent_id)
    
    db = get_db()
    repo = NotebookRepository(db)
    
    # 使用 notebook 存储成长日志
    return repo.write(
        agent_id=agent_id,
        entry_type="reflection",  # 成长日志作为反思类型
        title=f"Growth Log: {request.category}",
        content=request.content,
        source=f"subagent:{subagent_id}",
        related_topics=[request.category, "growth"],
        relevance_score=0.7,  # 成长日志有较高相关性
    )
