"""
SubAgent Handlers - SubAgent 状态管理

Topics:
- subagent.wake: 唤醒 SubAgent (sleeping → awaking)
- subagent.set_awake: 设置 awake 状态 (awaking → awake)
- subagent.set_sleeping: 设置 sleeping 状态

使用 task_queue.business.SubAgentBusiness 业务逻辑层。
"""

from typing import Dict, Any
from . import register_handler
from ..business import SubAgentBusiness
from ..topics import TaskTopics


@register_handler(TaskTopics.SUBAGENT_WAKE)
def handle_subagent_wake(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    唤醒 SubAgent
    
    幂等性：CAS - 只有 sleeping/failed 状态才能唤醒
    
    Payload:
        agent_id: str
        subagent_id: str
        
    Returns:
        success: bool
        previous_status: str
        new_status: str
    """
    biz = SubAgentBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = biz.wake(
        agent_id=payload["agent_id"],
        subagent_id=payload["subagent_id"],
    )
    
    response = {
        "success": result.success,
        "previous_status": result.previous_status,
        "new_status": result.status,
    }
    
    if result.message:
        response["message"] = result.message
    if result.error:
        response["error"] = result.error
    
    return response


@register_handler(TaskTopics.SUBAGENT_SET_AWAKE)
def handle_subagent_set_awake(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 SubAgent 为 awake 状态（RuntimeStart Saga 完成后调用）
    
    状态转换：awaking → awake
    
    幂等性：
    - awaking → awake: 正常转换
    - awake: 已经是目标状态，成功
    - 其他状态: 失败
    
    Payload:
        agent_id: str
        subagent_id: str
        runtime_id: str
    """
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
    """
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
