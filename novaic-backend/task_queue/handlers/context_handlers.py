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
from ..topics import TaskTopics
from common.exceptions import ValidationError, NotFoundError


@register_handler(TaskTopics.CONTEXT_READ)
def handle_context_read(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    读取最新 runtime context（用于 ReactThink）
    
    与 context.get 的区别：
    - context.read 用于 ReactThink，会过滤 sending 状态的消息
    - context.get 用于普通查询，不过滤
    
    Payload:
        runtime_id: str
        filter_sending: bool (可选，默认 True)
        
    Raises:
        ValidationError: 当必填字段缺失时
        NotFoundError: 当 Runtime 不存在时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    runtime_id = payload["runtime_id"]
    filter_sending = payload.get("filter_sending", True)

    gateway_client = ctx.get("gateway_client")
    ro_client = ctx.get("ro_client")
    if not gateway_client or not ro_client:
        raise ValidationError(
            "Missing required clients in ctx: gateway_client and ro_client "
            "(fallback creation is disabled)"
        )
    runtime = ro_client.get_runtime(runtime_id)
    if not runtime:
        raise NotFoundError(f"Runtime not found: {runtime_id}")

    context = runtime.get("context") or []
    agent_id = runtime.get("agent_id")
    
    # 记录本次读取到的新消息
    new_messages_list = []
    
    # 过滤 sending 状态的消息（可选）
    # 注：context 里的消息已经是 sent 的，这里主要是获取新的 user messages
    if filter_sending:
        # 获取新的 sent 消息（未被读取的）
        new_messages = gateway_client.get_unread_sent_messages(agent_id)

        if new_messages:
            # 逐个处理消息：append 成功后再标记为已读（原子性）
            for msg in new_messages:
                try:
                    # 先 append 到 context
                    append_result = ro_client.append_context(
                        runtime_id=runtime_id,
                        message={"role": "user", "content": msg["content"]},
                        message_type="user",
                        round_id=None,
                        idempotency_key=f"user-msg-{msg['id']}",
                    )
                    
                    # append 成功后，才标记为已读
                    if append_result.get("success"):
                        gateway_client.mark_messages_read([msg["id"]])
                        context.append({
                            "role": "user",
                            "content": msg["content"],
                        })
                        # 记录成功处理的新消息
                        new_messages_list.append(msg)
                except Exception as e:
                    # 如果 append 失败，不标记为已读，下次还能读到
                    print(f"[context.read] Failed to append message {msg['id']}: {e}")
                    continue
    
    # 不在此展开 result_id，由使用方按需展开：
    # - LLM 调用前：expand_messages_for_llm
    # - 摘要生成：expand_messages_for_summary

    return {
        "success": True,
        "runtime_id": runtime_id,
        "context": context,
        "length": len(context),
        "new_messages": new_messages_list,  # 返回本次读取的新消息
    }


@register_handler(TaskTopics.CONTEXT_APPEND)
def handle_context_append(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    追加消息到 runtime context
    
    tool_result：由 Tools Server 推 TRS，此处仅存储 result_id。
    
    幂等性：通过 idempotency_key 或 round_id + message_type 检查
    
    Payload:
        runtime_id: str
        message: dict
        message_type: str (llm_response / tool_result / user / etc.)
        round_id: str
        idempotency_key: str (可选)
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    if not payload.get("message"):
        raise ValidationError("Missing required field: message")

    message = dict(payload["message"])
    message_type = payload.get("message_type", "unknown")

    # tool_result：不再在此推送 TRS，由 Tools Server 在 call_tool 时推送。
    # message 必须包含 result_id（工具执行成功时）。

    biz = MessageBusiness(
        ctx["gateway_url"],
        gateway_client=ctx.get("gateway_client"),
        ro_client=ctx.get("ro_client"),
    )

    result = biz.append_to_context(
        runtime_id=payload["runtime_id"],
        message=message,
        message_type=message_type,
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


@register_handler(TaskTopics.CONTEXT_GET)
def handle_context_get(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    获取 runtime context
    
    Payload:
        runtime_id: str
        
    Raises:
        ValidationError: 当必填字段缺失时
        NotFoundError: 当 Runtime 不存在时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    biz = MessageBusiness(
        ctx["gateway_url"],
        gateway_client=ctx.get("gateway_client"),
        ro_client=ctx.get("ro_client"),
    )
    
    context = biz.get_context(payload["runtime_id"])

    if context is None:
        raise NotFoundError(f"Runtime not found: {payload['runtime_id']}")

    # 不在此展开，由使用方按需展开

    return {
        "success": True,
        "runtime_id": payload["runtime_id"],
        "context": context,
        "length": len(context),
    }
