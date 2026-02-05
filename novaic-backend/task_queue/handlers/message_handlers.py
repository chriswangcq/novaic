"""
Message Handlers - 消息处理

Topics:
- message.process: 处理用户消息，触发 Runtime 启动流程 (v1, 即将弃用)
- message.claim: 认领消息 (sending → sent)
- message.route: 判断消息路由，决定是否唤醒 SubAgent (v2)
"""

from typing import Dict, Any
from common.enums import SubagentStatus
from . import register_handler
from ..business import SubAgentBusiness
from ..client import GatewayInternalClient
from ..business import MessageBusiness
from ..topics import TaskTopics


@register_handler(TaskTopics.MESSAGE_PROCESS)
def handle_message_process(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    处理用户消息
    
    流程：
    1. 检查 SubAgent 状态
    2. 根据状态决定行为：
       - sleeping/failed: CAS 唤醒 → awaking → 创建 Saga
       - awaking: 正在启动中，跳过
       - awake: 查找 active Runtime，追加消息或跳过
    
    状态转换：
    - sleeping/failed → awaking (message_handler)
    - awaking → awake (RuntimeStart Saga 完成后)
    
    Payload:
        message_id: str
        agent_id: str
        content: str
        subagent_id: str (可选，默认 "main")
    """
    saga_client = ctx.get("saga_client")
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    
    message_id = payload["message_id"]
    agent_id = payload["agent_id"]
    content = payload["content"]
    subagent_id = payload.get("subagent_id", f"main-{agent_id[:8]}")
    
    # 1. 检查 SubAgent
    status_resp = client.get_subagent_status(agent_id, subagent_id)
    subagent_status = status_resp.get("status")
    if not subagent_status:
        return {
            "success": False,
            "error": "SubAgent not found",
            "message_id": message_id,
        }
    
    # 2. 根据状态决定行为
    
    # 2a. awaking: 正在启动中，跳过（等待现有 Saga 完成）
    if subagent_status == "awaking":
        return {
            "success": True,
            "message_id": message_id,
            "action": "pending",
            "message": "Runtime is starting, please wait",
        }
    
    # 2b. awake: 查找 active Runtime
    if subagent_status == SubagentStatus.AWAKE.value:
        active_runtime = client.get_subagent_runtime(agent_id, subagent_id)
        if active_runtime:
            # 追加消息到 context
            return {
                "success": True,
                "message_id": message_id,
                "action": "append_to_runtime",
                "runtime_id": active_runtime["runtime_id"],
            }
        else:
            # awake 但没有 active runtime，异常情况
            # 重置为 sleeping 以便重新创建 runtime
            client.set_subagent_sleeping(agent_id, subagent_id)
            subagent_status = SubagentStatus.SLEEPING.value  # 继续走 sleeping 流程
    
    # 3. sleeping/failed: CAS 唤醒 → awaking
    woke_up = False
    if subagent_status in (SubagentStatus.SLEEPING.value, SubagentStatus.FAILED.value):
        biz = SubAgentBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
        result = biz.wake(agent_id, subagent_id)
        woke_up = result.success and result.status == "awaking"
    
    # 4. 只有唤醒成功才创建 Saga
    if not woke_up:
        # CAS 失败，说明被其他消息抢先了
        return {
            "success": True,
            "message_id": message_id,
            "action": "skipped",
            "message": "Another message already triggered wake up",
        }
    
    # 5. 创建 RuntimeStart Saga
    if saga_client:
        initial_context = [
            {"role": "user", "content": content}
        ]
        
        saga_id = saga_client.start(
            saga_type="runtime_start",
            context={
                "agent_id": agent_id,
                "subagent_id": subagent_id,
                "trigger_id": message_id,
                "initial_context": initial_context,
            },
            idempotency_key=f"runtime-start-{message_id}",
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "action": "runtime_start",
            "saga_id": saga_id,
        }
    
    return {
        "success": True,
        "message_id": message_id,
        "action": "wake_only",
        "subagent_status": "awaking",
    }


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
    判断消息路由（v2）
    
    用于 MessageProcess Saga 判断是否需要启动 Runtime。
    使用 SubAgentBusiness 进行状态检查和 CAS 唤醒。
    
    Payload:
        agent_id: str
        subagent_id: str
        message_id: str
    
    Returns:
        action: "start_runtime" | "skip_awaking" | "skip_awake"
    """
    biz = SubAgentBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    
    agent_id = payload["agent_id"]
    subagent_id = payload["subagent_id"]
    message_id = payload["message_id"]
    
    # 获取当前状态
    status = biz.get_status(agent_id, subagent_id)
    
    if status is None:
        return {
            "success": False,
            "error": "SubAgent not found",
            "message_id": message_id,
        }
    
    # awaking: 正在启动中，跳过
    if status == "awaking":
        return {
            "success": True,
            "action": "skip_awaking",
            "message_id": message_id,
            "message": "Runtime is starting, please wait",
        }
    
    # awake: 检查是否有 active runtime
    if status == SubagentStatus.AWAKE.value:
        # 检查是否真的有 active runtime
        active_runtime = client.get_subagent_runtime(agent_id, subagent_id)
        if active_runtime:
            return {
                "success": True,
                "action": "skip_awake",
                "message_id": message_id,
                "message": "Message will be consumed by agent loop",
            }
        else:
            # awake 但没有 active runtime，重置为 sleeping
            client.set_subagent_sleeping(agent_id, subagent_id)
            status = SubagentStatus.SLEEPING.value  # 继续走唤醒流程
    
    # sleeping/failed: 尝试 CAS 唤醒
    if status in (SubagentStatus.SLEEPING.value, SubagentStatus.FAILED.value):
        result = biz.wake(agent_id, subagent_id)
        
        if result.success and result.status == "awaking":
            return {
                "success": True,
                "action": "start_runtime",
                "message_id": message_id,
            }
        elif result.success:
            # 已经是 awaking 或 awake（被其他消息抢先）
            return {
                "success": True,
                "action": f"skip_{result.status}",
                "message_id": message_id,
                "message": result.message,
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "message_id": message_id,
            }
    
    # 其他状态
    return {
        "success": False,
        "error": f"Unknown SubAgent status: {status}",
        "message_id": message_id,
    }
