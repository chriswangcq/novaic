"""
Message Handlers - 消息处理 (v3)

Topics:
- message.process: 处理用户消息，触发 Runtime 启动流程 (DEPRECATED)
- message.claim: 认领消息 (sending → sent)
- message.route: 判断消息路由，决定是否启动 Runtime (v3)

v3 变更：
- 删除 awaking 状态，用 get_or_create_runtime 原子操作替代
- 简化状态：sleeping / awake
"""

from typing import Dict, Any
from common.enums import SubagentStatus
from common.exceptions import ValidationError
from . import register_handler
from ..business import SubAgentBusiness
from ..business import MessageBusiness
from ..topics import TaskTopics


# DEPRECATED: handle_message_process 已弃用，使用 message_process Saga + handle_message_route


@register_handler(TaskTopics.MESSAGE_CLAIM)
def handle_message_claim(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    认领消息 (sending → sent)
    
    幂等性：CAS
    
    Payload:
        message_id: str
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("message_id"):
        raise ValidationError("Missing required field: message_id")
    
    message_id = payload["message_id"]
    biz = MessageBusiness(
        ctx["gateway_url"],
        gateway_client=ctx.get("gateway_client"),
        ro_client=ctx.get("ro_client"),
    )
    return biz.claim_message(message_id)


@register_handler(TaskTopics.MESSAGE_NOTIFY_PARENT)
def handle_message_notify_parent(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    Sub SubAgent 完成后通知 Parent SubAgent
    
    发送 SUBAGENT_COMPLETED 消息到 Parent SubAgent（通常是 Main）。
    消息会被 Watchdog 监测，如果 Parent 正在运行会被 ReactThink 读取，
    如果 Parent 已休眠会触发唤醒。
    
    Payload:
        agent_id: str
        subagent_id: str (完成的 Sub SubAgent ID)
        parent_subagent_id: str (通知目标，通常是 main-xxx)
        result: str (可选，任务执行结果摘要)
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    # 验证必填字段
    if not payload.get("agent_id"):
        raise ValidationError("Missing required field: agent_id")
    if not payload.get("subagent_id"):
        raise ValidationError("Missing required field: subagent_id")
    
    agent_id = payload["agent_id"]
    subagent_id = payload["subagent_id"]
    parent_subagent_id = payload.get("parent_subagent_id")
    result = payload.get("result", "")
    
    # 只有 Sub SubAgent 才需要通知 Parent
    if not subagent_id.startswith("sub-"):
        return {
            "success": True,
            "skipped": True,
            "reason": "Not a sub subagent, no notification needed",
        }
    
    # 如果没有指定 parent，默认通知 main
    if not parent_subagent_id:
        parent_subagent_id = f"main-{agent_id[:8]}"
    
    # 构建通知消息内容
    result_summary = ""
    if result:
        result_summary = result[:200] + "..." if len(result) > 200 else result
    content = f"[子任务完成通知]\n\n子任务 {subagent_id} 已完成。\n\n结果摘要: {result_summary}" if result_summary else f"[子任务完成通知]\n\n子任务 {subagent_id} 已完成。"
    
    gateway_client = ctx.get("gateway_client")
    if not gateway_client:
        raise ValidationError(
            "Missing required client in ctx: gateway_client "
            "(fallback creation is disabled)"
        )
    try:
        response = gateway_client.inject_subagent_completed_message(
            agent_id=agent_id,
            subagent_id=subagent_id,
            parent_subagent_id=parent_subagent_id,
            result=result,
        )
        
        return {
            "success": response.get("success", False),
            "message_id": response.get("message_id"),
            "target_subagent_id": parent_subagent_id,
        }
    except Exception as e:
        # 通知失败不应该阻塞整个流程
        print(f"[MESSAGE_NOTIFY_PARENT] Failed to notify parent: {e}")
        return {
            "success": False,
            "error": str(e),
            "target_subagent_id": parent_subagent_id,
        }


@register_handler(TaskTopics.MESSAGE_ROUTE)
def handle_message_route(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    判断消息路由（v3.1）
    
    用于 MessageProcess Saga 判断是否需要启动 Runtime。
    使用 get_or_create_runtime 原子操作，替代 awaking 状态。
    
    v3.1 变更：
    - 增加 SubAgent 状态检查
    - 如果 SubAgent 是 sleeping 但有残留 active Runtime，先清理再创建新的
    - 解决 SUBAGENT_COMPLETED 消息无法唤醒 sleeping Main 的问题
    
    Payload:
        agent_id: str
        subagent_id: str
        message_id: str
    
    Returns:
        action: "start_runtime" | "skip_active"
        runtime_id: str (如果有 active runtime)
        just_created: bool (是否新创建的 runtime)
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    # 验证必填字段
    if not payload.get("agent_id"):
        raise ValidationError("Missing required field: agent_id")
    if not payload.get("subagent_id"):
        raise ValidationError("Missing required field: subagent_id")
    if not payload.get("message_id"):
        raise ValidationError("Missing required field: message_id")
    
    ro_client = ctx.get("ro_client")
    if not ro_client:
        raise ValidationError(
            "Missing required client in ctx: ro_client "
            "(fallback creation is disabled)"
        )
    agent_id = payload["agent_id"]
    subagent_id = payload["subagent_id"]
    message_id = payload["message_id"]
    
    # v3.1: 先检查 SubAgent 状态
    try:
        subagent_info = ro_client.get_subagent_status(agent_id, subagent_id)
        subagent_status = subagent_info.get("status", "sleeping")
    except Exception as e:
        print(f"[MESSAGE_ROUTE] Failed to get subagent status: {e}, assuming sleeping")
        subagent_status = "sleeping"
    
    # 原子操作：获取或创建 active runtime
    result = ro_client.get_or_create_runtime(agent_id, subagent_id)
    
    if not result:
        return {
            "success": False,
            "error": "Failed to get or create runtime",
            "message_id": message_id,
        }
    
    runtime_id = result.get("runtime_id")
    just_created = result.get("just_created", False)
    runtime_status = result.get("status", "active")
    
    if just_created:
        # 新创建的 runtime，需要启动
        return {
            "success": True,
            "action": "start_runtime",
            "message_id": message_id,
            "runtime_id": runtime_id,
            "just_created": True,
        }
    
    # 已有 active runtime，消息会被 ReactLoop 消费
    return {
        "success": True,
        "action": "skip_active",
        "message_id": message_id,
        "runtime_id": runtime_id,
        "just_created": False,
        "message": "Message will be consumed by existing runtime",
    }
