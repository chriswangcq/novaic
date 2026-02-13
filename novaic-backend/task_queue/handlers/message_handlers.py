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
from . import register_handler
from ..business import SubAgentBusiness
from ..client import GatewayInternalClient
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
    """
    message_id = payload["message_id"]
    biz = MessageBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    return biz.claim_message(message_id)


@register_handler(TaskTopics.MESSAGE_ROUTE)
def handle_message_route(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    判断消息路由（v3）
    
    用于 MessageProcess Saga 判断是否需要启动 Runtime。
    使用 get_or_create_runtime 原子操作，替代 awaking 状态。
    
    Payload:
        agent_id: str
        subagent_id: str
        message_id: str
    
    Returns:
        action: "start_runtime" | "skip_active"
        runtime_id: str (如果有 active runtime)
        just_created: bool (是否新创建的 runtime)
    """
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    
    agent_id = payload["agent_id"]
    subagent_id = payload["subagent_id"]
    message_id = payload["message_id"]
    
    # 原子操作：获取或创建 active runtime
    result = client.get_or_create_runtime(agent_id, subagent_id)
    
    if not result:
        return {
            "success": False,
            "error": "Failed to get or create runtime",
            "message_id": message_id,
        }
    
    runtime_id = result.get("runtime_id")
    just_created = result.get("just_created", False)
    
    if just_created:
        # 新创建的 runtime，需要启动
        return {
            "success": True,
            "action": "start_runtime",
            "message_id": message_id,
            "runtime_id": runtime_id,
            "just_created": True,
        }
    else:
        # 已有 active runtime，消息会被 ReactLoop 消费
        return {
            "success": True,
            "action": "skip_active",
            "message_id": message_id,
            "runtime_id": runtime_id,
            "just_created": False,
            "message": "Message will be consumed by existing runtime",
        }
