"""
Runtime Handlers - Runtime 生命周期管理

Topics:
- runtime.create: 创建 Runtime 记录
- runtime.update_phase: 更新 phase (CAS)
- runtime.set_status: 设置 status (CAS)
- runtime.set_summarized: 设置 summarized 标志
- runtime.set_need_rest: 设置 need_rest 标志
- runtime.increment_round: 增加 round 计数
- runtime.check_new_messages: 检查是否有新消息 + need_rest

使用 task_queue.business.RuntimeBusiness 业务逻辑层。
"""

from typing import Dict, Any
from . import register_handler
from ..business import RuntimeBusiness


@register_handler("runtime.create")
async def handle_runtime_create(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    创建 Runtime 记录
    
    幂等性：idempotency_key 唯一约束
    
    Payload:
        agent_id: str
        subagent_id: str
        idempotency_key: str (可选)
        initial_context: list (可选)
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = await biz.create(
        agent_id=payload["agent_id"],
        subagent_id=payload["subagent_id"],
        idempotency_key=payload.get("idempotency_key"),
        initial_context=payload.get("initial_context", []),
    )
    
    return {
        "success": result.success,
        "runtime_id": result.runtime_id,
        "created": result.created,
        "message": result.message,
        "status": result.status,
        "phase": result.phase,
    }


@register_handler("runtime.update_phase")
async def handle_runtime_update_phase(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    更新 Runtime phase
    
    幂等性：CAS - 检查 expected_phase
    
    Payload:
        runtime_id: str
        expected_phase: str
        new_phase: str
        round_id: str (可选)
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = await biz.update_phase(
        runtime_id=payload["runtime_id"],
        expected_phase=payload["expected_phase"],
        new_phase=payload["new_phase"],
        round_id=payload.get("round_id"),
    )
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
    }
    
    if result.previous_value:
        response["previous_phase"] = result.previous_value
    if result.new_value:
        response["new_phase"] = result.new_value
    if result.current_value:
        response["current_phase"] = result.current_value
        response["expected_phase"] = payload["expected_phase"]
    if result.message:
        response["message"] = result.message
    
    return response


@register_handler("runtime.set_status")
async def handle_runtime_set_status(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime status
    
    幂等性：CAS - 检查 expected_status
    
    Payload:
        runtime_id: str
        expected_status: str
        new_status: str
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = await biz.set_status(
        runtime_id=payload["runtime_id"],
        expected_status=payload["expected_status"],
        new_status=payload["new_status"],
    )
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
    }
    
    if result.previous_value:
        response["previous_status"] = result.previous_value
    if result.new_value:
        response["new_status"] = result.new_value
    if result.current_value:
        response["current_status"] = result.current_value
    if result.message:
        response["message"] = result.message
    
    return response


@register_handler("runtime.increment_round")
async def handle_runtime_increment_round(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    增加 Runtime round 计数
    
    Payload:
        runtime_id: str
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    return await biz.increment_round(payload["runtime_id"])


@register_handler("runtime.set_summarized")
async def handle_runtime_set_summarized(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime 已生成摘要
    
    幂等性：如果已经是 summarized=1，返回成功
    
    Payload:
        runtime_id: str
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = await biz.set_summarized(payload["runtime_id"])
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
    }
    
    if result.message:
        response["message"] = result.message
    
    return response


@register_handler("runtime.set_need_rest")
async def handle_runtime_set_need_rest(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime need_rest 标志
    
    幂等性：如果已经是目标值，返回成功
    
    Payload:
        runtime_id: str
        value: bool (可选，默认 True)
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = await biz.set_need_rest(
        payload["runtime_id"],
        payload.get("value", True),
    )
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
    }
    
    if result.message:
        response["message"] = result.message
    
    return response


@register_handler("runtime.check_new_messages")
async def handle_check_new_messages(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    检查是否有新的 sent 消息 + need_rest 状态
    
    用于 ReactActions 判断是否继续循环
    
    Payload:
        runtime_id: str
        agent_id: str
    
    Returns:
        has_new_messages: bool - 是否有新消息
        need_rest: bool - 是否需要休息
    """
    runtime_id = payload["runtime_id"]
    agent_id = payload["agent_id"]
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    runtime = await biz.get(runtime_id)
    need_rest = bool(runtime.get("need_rest")) if runtime else False

    from ..client import GatewayInternalClient
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    msg_resp = await client.has_new_messages(agent_id)
    has_new = bool(msg_resp.get("has_new_messages"))
    
    return {
        "success": True,
        "runtime_id": runtime_id,
        "has_new_messages": has_new,
        "need_rest": need_rest,
    }
