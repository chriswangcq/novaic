"""
Self Drive API - 自驱系统内部 API

提供自驱系统状态查询和配置管理的 API 端点。
这些端点主要供内部服务调用，用于：
- 获取完整的自驱系统状态
- 更新内驱力配置
- 获取用户画像评估
- 获取任务建议
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from gateway.db import get_db
from gateway.db.repositories.drive import DriveRepository
from gateway.db.repositories.task import TaskRepository
from .helpers import resolve_runtime_ids

router = APIRouter(tags=["self-drive"])


# ========================================
# Request/Response Models
# ========================================

class DriveConfigUpdateRequest(BaseModel):
    """内驱力配置更新请求"""
    curiosity: Optional[float] = None
    knowledge: Optional[float] = None
    growth: Optional[float] = None
    proactive_level: Optional[float] = None
    core_value: Optional[str] = None
    reflection_frequency: Optional[str] = None


class SelfDriveStateResponse(BaseModel):
    """自驱系统状态响应"""
    success: bool
    drive_config: Dict[str, Any]
    user_profile: Dict[str, Any]
    profile_assessment: Dict[str, Any]
    task_board: Dict[str, Any]
    growth_log: List[Dict[str, Any]]
    suggested_tasks: List[Dict[str, Any]]


# ========================================
# API Endpoints
# ========================================

@router.get("/rt/{runtime_id}/self-drive/state")
def get_self_drive_state(runtime_id: str) -> Dict[str, Any]:
    """
    获取完整的自驱系统状态
    
    返回：
    - 内驱力配置
    - 用户画像及评估
    - 四象限任务看板
    - 成长日志
    - 任务建议
    """
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    db = get_db()
    
    drive_repo = DriveRepository(db)
    task_repo = TaskRepository(db)
    
    # 获取内驱力配置
    drive_config_result = drive_repo.get_drive_config(agent_id)
    drive_config = drive_config_result.get("config", {})
    
    # 获取用户画像
    drive_data = drive_repo.get_or_create(agent_id)
    user_profile = drive_data.get("user_profile", {})
    
    # 评估用户画像
    profile_completeness = drive_repo.get_profile_completeness(agent_id)
    
    # 获取任务看板
    task_board = task_repo.get_board_summary(agent_id)
    
    # 获取成长日志
    growth_log_result = drive_repo.get_growth_log(agent_id, limit=10)
    growth_log = growth_log_result.get("entries", [])
    
    # 生成任务建议
    suggested_tasks = _generate_task_suggestions(
        user_profile=user_profile,
        drive_config=drive_config,
        existing_tasks=_extract_existing_tasks(task_board),
    )
    
    return {
        "success": True,
        "drive_config": drive_config,
        "user_profile": user_profile,
        "profile_assessment": {
            "completeness": profile_completeness.get("completeness", 0),
            "known_count": profile_completeness.get("known_count", 0),
            "total_dimensions": profile_completeness.get("total_dimensions", 8),
        },
        "task_board": task_board,
        "growth_log": growth_log,
        "suggested_tasks": suggested_tasks,
    }


@router.get("/rt/{runtime_id}/self-drive/config")
def get_drive_config(runtime_id: str) -> Dict[str, Any]:
    """获取内驱力配置"""
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    db = get_db()
    drive_repo = DriveRepository(db)
    return drive_repo.get_drive_config(agent_id)


@router.patch("/rt/{runtime_id}/self-drive/config")
def update_drive_config(runtime_id: str, request: DriveConfigUpdateRequest) -> Dict[str, Any]:
    """更新内驱力配置"""
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    db = get_db()
    drive_repo = DriveRepository(db)
    
    # 只更新非空字段
    config_updates = {}
    if request.curiosity is not None:
        config_updates["curiosity"] = max(0.0, min(1.0, request.curiosity))
    if request.knowledge is not None:
        config_updates["knowledge"] = max(0.0, min(1.0, request.knowledge))
    if request.growth is not None:
        config_updates["growth"] = max(0.0, min(1.0, request.growth))
    if request.proactive_level is not None:
        config_updates["proactive_level"] = max(0.0, min(1.0, request.proactive_level))
    if request.core_value is not None:
        config_updates["core_value"] = request.core_value
    if request.reflection_frequency is not None:
        config_updates["reflection_frequency"] = request.reflection_frequency
    
    if not config_updates:
        return {"success": True, "message": "No changes"}
    
    return drive_repo.update_drive_config(agent_id, config_updates)


@router.get("/rt/{runtime_id}/self-drive/profile-assessment")
def get_profile_assessment(runtime_id: str) -> Dict[str, Any]:
    """
    获取用户画像评估
    
    返回详细的画像完整度评估，包括：
    - 完整度百分比
    - 已知信息
    - 缺失信息
    - 高优先级缺失项
    """
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    db = get_db()
    drive_repo = DriveRepository(db)
    
    # 获取用户画像
    drive_data = drive_repo.get_or_create(agent_id)
    user_profile = drive_data.get("user_profile", {})
    
    # 使用完整的评估模块
    try:
        from task_queue.utils.profile_assessment import assess_profile_completeness
        assessment = assess_profile_completeness(user_profile)
        return {
            "success": True,
            **assessment,
        }
    except ImportError:
        # 降级到简化版本
        return drive_repo.get_profile_completeness(agent_id)


@router.get("/rt/{runtime_id}/self-drive/task-suggestions")
def get_task_suggestions(runtime_id: str, limit: int = 5) -> Dict[str, Any]:
    """
    获取基于内驱力的任务建议
    
    根据当前的用户画像和内驱力配置，自动生成建议的任务。
    """
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    db = get_db()
    
    drive_repo = DriveRepository(db)
    task_repo = TaskRepository(db)
    
    # 获取配置和画像
    drive_config = drive_repo.get_drive_config(agent_id).get("config", {})
    drive_data = drive_repo.get_or_create(agent_id)
    user_profile = drive_data.get("user_profile", {})
    
    # 获取现有任务
    task_board = task_repo.get_board_summary(agent_id)
    existing_tasks = _extract_existing_tasks(task_board)
    
    # 生成建议
    suggestions = _generate_task_suggestions(
        user_profile=user_profile,
        drive_config=drive_config,
        existing_tasks=existing_tasks,
        max_tasks=limit,
    )
    
    return {
        "success": True,
        "suggestions": suggestions,
        "profile_completeness": drive_repo.get_profile_completeness(agent_id).get("completeness", 0),
    }


@router.get("/rt/{runtime_id}/self-drive/growth-log")
def get_growth_log(
    runtime_id: str,
    limit: int = 20,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """获取成长日志"""
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    db = get_db()
    drive_repo = DriveRepository(db)
    return drive_repo.get_growth_log(agent_id, limit=limit, category=category)


@router.post("/rt/{runtime_id}/self-drive/growth-log")
def add_growth_log(
    runtime_id: str,
    content: str,
    category: str = "learning",
) -> Dict[str, Any]:
    """添加成长日志"""
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    db = get_db()
    drive_repo = DriveRepository(db)
    return drive_repo.add_growth_log(agent_id, content=content, category=category)


# ========================================
# Helper Functions
# ========================================

def _extract_existing_tasks(task_board: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从任务看板提取所有任务"""
    tasks = []
    for quadrant in ["q1", "q2", "q3", "q4"]:
        q_data = task_board.get(quadrant, {})
        tasks.extend(q_data.get("tasks", []))
    return tasks


def _generate_task_suggestions(
    user_profile: Dict[str, Any],
    drive_config: Dict[str, Any],
    existing_tasks: List[Dict[str, Any]],
    max_tasks: int = 5,
) -> List[Dict[str, Any]]:
    """生成任务建议"""
    try:
        from task_queue.utils.drive_config import DriveConfig
        from task_queue.utils.task_generator import generate_self_driven_tasks
        
        config = DriveConfig.from_dict(drive_config)
        return generate_self_driven_tasks(
            user_profile=user_profile,
            drive_config=config,
            existing_tasks=existing_tasks,
            max_tasks=max_tasks,
        )
    except ImportError:
        # 如果模块不可用，返回空列表
        return []
