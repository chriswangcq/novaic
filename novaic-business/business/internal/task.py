"""
Internal API module: task

Proxies task operations to Queue Service via HTTP.
TaskManager is Gateway-internal; Business Service delegates over the network.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import httpx

from common.config import ServiceConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])

_TIMEOUT = 10.0


def _queue_url() -> str:
    return ServiceConfig.QUEUE_SERVICE_URL.rstrip("/")


def _forward_get(path: str, params: Optional[Dict] = None) -> Any:
    """Forward a GET request to Queue Service."""
    try:
        resp = httpx.get(f"{_queue_url()}{path}", params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail=e.response.text[:500])
    except Exception as e:
        logger.error("[task] Queue Service GET %s failed: %s", path, e)
        raise HTTPException(status_code=503, detail="Queue Service unavailable")


def _forward_post(path: str, json_data: Optional[Dict] = None) -> Any:
    """Forward a POST request to Queue Service."""
    try:
        resp = httpx.post(f"{_queue_url()}{path}", json=json_data or {}, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail=e.response.text[:500])
    except Exception as e:
        logger.error("[task] Queue Service POST %s failed: %s", path, e)
        raise HTTPException(status_code=503, detail="Queue Service unavailable")


# ==================== TaskManager API (for Tools Server) ====================

@router.post("/tasks/spawn")
def task_spawn(data: Dict[str, Any]):
    """Spawn a new task. Proxied to Queue Service."""
    return _forward_post("/api/tasks/spawn", data)


@router.post("/tasks/create-completed")
def task_create_completed(data: Dict[str, Any]):
    """Create an immediately completed task for truncated output storage."""
    return _forward_post("/api/tasks/create-completed", data)


@router.get("/tasks/{task_id}")
def task_get_status(
    task_id: str,
    include_outputs: bool = False,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    tail_lines: Optional[int] = None,
):
    """Get task status by ID."""
    params: Dict[str, Any] = {}
    if include_outputs:
        params["include_outputs"] = "true"
    if start_line is not None:
        params["start_line"] = start_line
    if end_line is not None:
        params["end_line"] = end_line
    if tail_lines is not None:
        params["tail_lines"] = tail_lines
    return _forward_get(f"/api/tasks/{task_id}", params=params or None)


@router.get("/tasks")
def task_list(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """List tasks."""
    params: Dict[str, Any] = {}
    if status:
        params["status"] = status
    if agent_id:
        params["agent_id"] = agent_id
    return _forward_get("/api/tasks", params=params or None)


@router.post("/tasks/{task_id}/cancel")
def task_cancel(task_id: str, reason: Optional[str] = None):
    """Cancel a task."""
    return _forward_post(f"/api/tasks/{task_id}/cancel", {"reason": reason})


@router.get("/tasks/{task_id}/result")
def task_get_result(task_id: str, format: str = "summary"):
    """Get task result."""
    return _forward_get(f"/api/tasks/{task_id}/result", params={"format": format})


# ==================== Four-Quadrant Task API (四象限任务系统) ====================

class QuadrantTaskCreateRequest(BaseModel):
    title: str
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


class TaskProgressRequest(BaseModel):
    note: str
    set_ongoing: bool = False


# ==================== Agent-scoped Quadrant Task APIs ====================

@router.post("/agents/{agent_id}/quadrant-tasks")
def create_quadrant_task_by_agent(agent_id: str, request: QuadrantTaskCreateRequest):
    """创建四象限任务 (agent-scoped)"""
    from business.entity_store import get_entity_store

    store = get_entity_store()

    entry = store.create(
        "agent-tasks", "",
        data={
            "agent_id": agent_id,
            "title": request.title,
            "quadrant": request.quadrant,
            "source": request.source,
            "description": request.description or "",
            "reasoning": request.reasoning,
            "due_date": request.due_date,
            "context": request.context,
            "related_profile_keys": request.related_profile_keys or [],
            "status": "pending",
        },
        params={"agent_id": agent_id}
    )

    return {
        "success": True,
        "id": entry.get("id"),
        "title": entry.get("title"),
        "quadrant": entry.get("quadrant"),
        "source": entry.get("source"),
        "status": entry.get("status"),
    }


@router.get("/agents/{agent_id}/quadrant-tasks")
def list_quadrant_tasks_by_agent(
    agent_id: str,
    quadrant: Optional[str] = None,
    status: Optional[str] = "pending",
    limit: int = 20,
):
    """列出四象限任务 (agent-scoped)"""
    from business.entity_store import get_entity_store
    store = get_entity_store()

    tasks = store.list("agent-tasks", "", params={"agent_id": agent_id})

    if quadrant and quadrant != "all":
        tasks = [t for t in tasks if t.get("quadrant") == quadrant]
    if status and status != "all":
        tasks = [t for t in tasks if t.get("status") == status]

    def sort_key(t):
        q = t.get("quadrant")
        q_order = {"q1": 1, "q2": 2, "q3": 3, "q4": 4}.get(q, 5)
        due = t.get("due_date") or "9999-99-99"
        created = t.get("created_at") or ""
        return (q_order, due, created)

    tasks.sort(key=sort_key)
    tasks = tasks[:limit]

    return {
        "success": True,
        "tasks": tasks,
        "count": len(tasks),
    }


@router.get("/agents/{agent_id}/quadrant-tasks/board")
def get_quadrant_board_by_agent(agent_id: str):
    """获取四象限任务看板摘要 (agent-scoped)"""
    from business.entity_store import get_entity_store
    store = get_entity_store()

    tasks = store.list("agent-tasks", "", params={"agent_id": agent_id})
    tasks = [t for t in tasks if t.get("status") in ("pending", "in_progress")]

    board = {"q1": [], "q2": [], "q3": [], "q4": []}
    for t in tasks:
        q = t.get("quadrant")
        if q in board:
            board[q].append({
                "id": t.get("id"),
                "title": t.get("title"),
                "status": t.get("status"),
                "due_date": t.get("due_date"),
                "source": t.get("source"),
            })

    for q in board:
        board[q].sort(key=lambda x: x.get("due_date") or "9999-99-99")

    return {
        "success": True,
        "board": board,
        "total_active": sum(len(v) for v in board.values()),
        "counts": {q: len(v) for q, v in board.items()},
    }


@router.get("/agents/{agent_id}/quadrant-tasks/{task_id}")
def get_quadrant_task_by_agent(agent_id: str, task_id: int):
    """获取单个四象限任务详情 (agent-scoped)"""
    from business.entity_store import get_entity_store
    store = get_entity_store()

    task = store.get("agent-tasks", "", str(task_id), params={"agent_id": agent_id})
    if not task:
        return {"success": True, "found": False, "task": None}

    return {
        "success": True,
        "found": True,
        "task": task,
    }


@router.patch("/agents/{agent_id}/quadrant-tasks/{task_id}")
def update_quadrant_task_by_agent(agent_id: str, task_id: int, request: QuadrantTaskUpdateRequest):
    """更新四象限任务 (agent-scoped)"""
    from business.entity_store import get_entity_store
    from common.utils.time import utc_now_iso
    store = get_entity_store()

    updates = {}
    if request.status is not None:
        updates["status"] = request.status
        if request.status == "completed":
            updates["completed_at"] = utc_now_iso()
    if request.quadrant is not None:
        updates["quadrant"] = request.quadrant
    if request.title is not None:
        updates["title"] = request.title
    if request.description is not None:
        updates["description"] = request.description
    if request.due_date is not None:
        updates["due_date"] = request.due_date

    if not updates:
        return {"success": True, "message": "No fields to update"}

    store.update("agent-tasks", "", str(task_id), data=updates, params={"agent_id": agent_id})

    return {"success": True, "id": task_id}


@router.post("/agents/{agent_id}/quadrant-tasks/{task_id}/complete")
def complete_quadrant_task_by_agent(agent_id: str, task_id: int, request: QuadrantTaskCompleteRequest):
    """完成四象限任务 (agent-scoped)"""
    from business.entity_store import get_entity_store
    from common.utils.time import utc_now_iso
    store = get_entity_store()

    store.update(
        "agent-tasks", "", str(task_id),
        data={
            "status": "completed",
            "completed_at": utc_now_iso(),
            "completion_notes": request.notes
        },
        params={"agent_id": agent_id}
    )

    return {"success": True, "id": task_id, "status": "completed"}


@router.delete("/agents/{agent_id}/quadrant-tasks/{task_id}")
def delete_quadrant_task_by_agent(agent_id: str, task_id: int):
    """删除四象限任务 (agent-scoped)"""
    from business.entity_store import get_entity_store
    store = get_entity_store()

    store.delete("agent-tasks", "", str(task_id), params={"agent_id": agent_id})
    return {"success": True, "id": task_id}


@router.post("/agents/{agent_id}/quadrant-tasks/{task_id}/start")
def start_quadrant_task_by_agent(agent_id: str, task_id: int):
    """开始执行四象限任务 (agent-scoped)"""
    from business.entity_store import get_entity_store
    store = get_entity_store()

    task = store.get("agent-tasks", "", str(task_id), params={"agent_id": agent_id})
    if not task:
        return {"success": False, "error": "Task not found"}

    store.update("agent-tasks", "", str(task_id), data={"status": "in_progress"}, params={"agent_id": agent_id})
    task["status"] = "in_progress"

    return {
        "success": True,
        "task": task,
        "message": f"开始执行任务: {task.get('title')}",
    }


@router.post("/agents/{agent_id}/quadrant-tasks/{task_id}/progress")
def add_task_progress_by_agent(agent_id: str, task_id: int, request: TaskProgressRequest):
    """记录任务进展 (agent-scoped)"""
    from business.entity_store import get_entity_store
    from common.utils.time import utc_now_iso
    store = get_entity_store()

    task = store.get("agent-tasks", "", str(task_id), params={"agent_id": agent_id})
    if not task:
        return {"success": False, "error": "Task not found"}

    progress = task.get("progress_notes") or []
    progress.append({
        "timestamp": utc_now_iso(),
        "note": request.note,
    })

    updates = {"progress_notes": progress}
    if request.set_ongoing:
        updates["status"] = "ongoing"

    store.update("agent-tasks", "", str(task_id), data=updates, params={"agent_id": agent_id})

    return {
        "success": True,
        "id": task_id,
        "progress_count": len(progress),
    }


@router.post("/agents/{agent_id}/growth-logs")
def log_growth_by_agent(agent_id: str, request: GrowthLogRequest):
    """记录成长日志 (agent-scoped)"""
    from business.entity_store import get_entity_store

    store = get_entity_store()

    entry = store.create(
        "agent-notebook", "",
        data={
            "entry_type": "reflection",
            "title": f"Growth Log: {request.category}",
            "content": request.content,
            "source": f"agent:{agent_id}",
            "related_topics": [request.category, "growth"],
            "relevance_score": 0.7,
            "status": "draft"
        },
        params={"agent_id": agent_id}
    )

    return {
        "success": True,
        "id": entry.get("id"),
        "entry_type": entry.get("entry_type"),
        "title": entry.get("title"),
        "status": entry.get("status"),
    }
