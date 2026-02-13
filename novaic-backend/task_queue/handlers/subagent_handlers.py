"""
SubAgent Handlers - SubAgent 状态管理 (v3)

Topics:
- subagent.set_awake: 设置 awake 状态 (sleeping → awake)
- subagent.set_sleeping: 设置 sleeping 状态

v3 变更：
- 删除 awaking 中间状态
- 删除 subagent.wake，用 get_or_create_runtime 原子操作替代
- set_awake 直接从 sleeping 转换为 awake
"""

from typing import Dict, Any
from . import register_handler
from ..business import SubAgentBusiness
from ..topics import TaskTopics
from common.exceptions import ValidationError


@register_handler(TaskTopics.SUBAGENT_SET_AWAKE)
def handle_subagent_set_awake(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 SubAgent 为 awake 状态（RuntimeStart Saga 完成后调用）
    
    状态转换：sleeping → awake（v3: 删除 awaking 中间状态）
    
    幂等性：
    - sleeping → awake: 正常转换
    - awake: 已经是目标状态，成功
    
    Payload:
        agent_id: str
        subagent_id: str
        runtime_id: str
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    # 验证必填字段
    if not payload.get("agent_id"):
        raise ValidationError("Missing required field: agent_id")
    if not payload.get("subagent_id"):
        raise ValidationError("Missing required field: subagent_id")
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    biz = SubAgentBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = biz.set_awake(
        agent_id=payload["agent_id"],
        subagent_id=payload["subagent_id"],
        runtime_id=payload["runtime_id"],
    )
    
    response = {
        "success": result.success,
        "subagent_id": result.subagent_id,
        "runtime_id": payload["runtime_id"],
        "previous_status": result.previous_status,
        "status": result.status,
    }
    
    if result.message:
        response["message"] = result.message
    if result.error:
        response["error"] = result.error
    
    return response


@register_handler(TaskTopics.SUBAGENT_SET_SLEEPING)
def handle_subagent_set_sleeping(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 SubAgent 为 sleeping 状态
    
    幂等性：无论当前状态，都设置为 sleeping
    
    Payload:
        agent_id: str
        subagent_id: str
        runtime_id: str (可选，用于验证)
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    # 验证必填字段
    if not payload.get("agent_id"):
        raise ValidationError("Missing required field: agent_id")
    if not payload.get("subagent_id"):
        raise ValidationError("Missing required field: subagent_id")
    
    biz = SubAgentBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = biz.set_sleeping(
        agent_id=payload["agent_id"],
        subagent_id=payload["subagent_id"],
    )
    
    return {
        "success": result.success,
        "subagent_id": result.subagent_id,
        "status": result.status,
    }
