"""
Context Handlers - Context 管理

Topics:
- context.append: 追加消息到 runtime context
- context.get: 获取 runtime context
- context.read: 读取最新 context（用于 ReactThink）

使用 task_queue.business.MessageBusiness 业务逻辑层。
"""

from typing import Dict, Any
from . import register_handler
from ..business import MessageBusiness


@register_handler("context.read")
async def handle_context_read(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    读取最新 runtime context（用于 ReactThink）
    
    与 context.get 的区别：
    - context.read 用于 ReactThink，会过滤 sending 状态的消息
    - context.get 用于普通查询，不过滤
    
    Payload:
        runtime_id: str
        filter_sending: bool (可选，默认 True)
    """
    runtime_id = payload["runtime_id"]
    filter_sending = payload.get("filter_sending", True)

    from ..client import GatewayInternalClient
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    runtime = await client.get_runtime(runtime_id)
    if not runtime:
        return {"success": False, "error": "Runtime not found"}

    context = runtime.get("context") or []
    agent_id = runtime.get("agent_id")
    
    # 过滤 sending 状态的消息（可选）
    # 注：context 里的消息已经是 sent 的，这里主要是获取新的 user messages
    if filter_sending:
        # 获取新的 sent 消息（未被读取的）
        new_messages = await client.get_unread_sent_messages(agent_id)

        if new_messages:
            await client.mark_messages_read([msg["id"] for msg in new_messages])
            for msg in new_messages:
                await client.append_context(
                    runtime_id=runtime_id,
                    message={"role": "user", "content": msg["content"]},
                    message_type="user",
                    round_id=None,
                    idempotency_key=f"user-msg-{msg['id']}",
                )
                context.append({
                    "role": "user",
                    "content": msg["content"],
                })
    
    return {
        "success": True,
        "runtime_id": runtime_id,
        "context": context,
        "length": len(context),
    }


@register_handler("context.append")
async def handle_context_append(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    追加消息到 runtime context
    
    幂等性：通过 idempotency_key 或 round_id + message_type 检查
    
    Payload:
        runtime_id: str
        message: dict
        message_type: str (llm_response / tool_result / user / etc.)
        round_id: str
        idempotency_key: str (可选)
    """
    biz = MessageBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = await biz.append_to_context(
        runtime_id=payload["runtime_id"],
        message=payload["message"],
        message_type=payload.get("message_type", "unknown"),
        round_id=payload.get("round_id"),
        idempotency_key=payload.get("idempotency_key"),
    )
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
        "appended": result.appended,
        "context_length": result.context_length,
    }
    
    if result.message:
        response["message"] = result.message
    if result.error:
        response["error"] = result.error
    
    return response


@register_handler("context.get")
async def handle_context_get(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    获取 runtime context
    
    Payload:
        runtime_id: str
    """
    biz = MessageBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    context = await biz.get_context(payload["runtime_id"])
    
    if context is None:
        return {"success": False, "error": "Runtime not found"}
    
    return {
        "success": True,
        "runtime_id": payload["runtime_id"],
        "context": context,
        "length": len(context),
    }
