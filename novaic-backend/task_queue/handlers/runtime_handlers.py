"""
Runtime Handlers - Runtime 生命周期管理

Topics:
- runtime.create: 创建 Runtime 记录（包含历史 Context 构建）
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
from ..client import GatewayInternalClient
from ..utils.context_builder import build_initial_context
from ..topics import TaskTopics


@register_handler(TaskTopics.RUNTIME_CREATE)
def handle_runtime_create(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    创建 Runtime 记录，并从历史构建初始 Context
    
    初始 Context 构建规则：
    1. historical_summary: SubAgent 的合并历史摘要
    2. hrl[:-5] 的 cold_summary: 较早的 runtime
    3. hrl[-5:] 的 hot_summary: 最近的 runtime
    
    幂等性：idempotency_key 唯一约束
    
    Payload:
        agent_id: str
        subagent_id: str
        idempotency_key: str (可选)
        user_message: str (可选) - 用户消息，用于自动匹配技能
        
    Returns:
        success: bool
        runtime_id: str
        created: bool
        message: str
        status: str
        phase: str
        context_parts: int - 初始 context 部分数量
        matched_skills: list - 自动匹配的技能名称列表
    """
    agent_id = payload["agent_id"]
    subagent_id = payload["subagent_id"]
    user_message = payload.get("user_message")  # For auto-matching skills
    
    # 获取或创建 client
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    biz = RuntimeBusiness(ctx["gateway_url"], client=client)
    
    # 构建初始 context
    # 优先使用 payload 中的 initial_context（用于 sub-subagent，包含任务描述）
    # 否则从历史摘要构建（用于 main subagent）
    initial_context = []
    context_parts = 0
    matched_skills = []
    
    if "initial_context" in payload and payload["initial_context"]:
        # Sub-subagent: 使用传入的 initial_context
        initial_context = payload["initial_context"]
        context_parts = len(initial_context)
        print(f"[runtime.create] Using provided initial context with {context_parts} parts for {subagent_id}")
    else:
        # Main subagent: 从历史摘要构建
        try:
            initial_context = build_initial_context(agent_id, subagent_id, client)
            context_parts = len(initial_context)
            if context_parts > 0:
                print(f"[runtime.create] Built initial context with {context_parts} parts for {subagent_id}")
        except Exception as e:
            # Context 构建失败不阻塞 runtime 创建
            print(f"[runtime.create] Failed to build initial context for {subagent_id}: {e}")
    
    # Base System Prompt: 为所有 session 注入 Agent 身份 (Phase 4)
    # Now with auto-matching skills based on user_message
    try:
        from ..utils.system_prompt import build_system_prompt
        sys_prompt = build_system_prompt(
            agent_id, 
            client,
            task=user_message,  # Pass user message for auto-matching
            auto_match_skills=True,
        )
        if sys_prompt:
            initial_context.insert(0, {
                "role": "system",
                "content": sys_prompt,
            })
            context_parts += 1
            print(f"[runtime.create] Injected system prompt for {subagent_id}")
            
            # Try to get matched skills for logging
            if user_message:
                try:
                    match_resp = client.match_skills_for_task(user_message)
                    matched_skills = [s.get("name") for s in match_resp.get("matched_skills", [])]
                    if matched_skills:
                        print(f"[runtime.create] Auto-matched skills: {matched_skills}")
                except Exception:
                    pass
    except Exception as e:
        print(f"[runtime.create] Failed to build system prompt for {subagent_id}: {e}")
    
    # Drive Prompt: 定时唤醒时注入自驱力 Prompt (Phase 3)
    trigger_type = payload.get("trigger_type", "user_message")
    if trigger_type == "scheduled_wake":
        try:
            from ..utils.drive_prompt import build_drive_prompt
            drive_prompt = build_drive_prompt(agent_id, client)
            initial_context.append({
                "role": "system",
                "content": drive_prompt,
            })
            context_parts += 1
            print(f"[runtime.create] Injected drive prompt for scheduled wake ({subagent_id})")
        except Exception as e:
            print(f"[runtime.create] Failed to build drive prompt for {subagent_id}: {e}")
    
    # 创建 runtime
    result = biz.create(
        agent_id=agent_id,
        subagent_id=subagent_id,
        idempotency_key=payload.get("idempotency_key"),
        initial_context=initial_context,
    )
    
    return {
        "success": result.success,
        "runtime_id": result.runtime_id,
        "created": result.created,
        "message": result.message,
        "status": result.status,
        "phase": result.phase,
        "context_parts": context_parts,
        "matched_skills": matched_skills,
    }


@register_handler(TaskTopics.RUNTIME_UPDATE_PHASE)
def handle_runtime_update_phase(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
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
    
    result = biz.update_phase(
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


@register_handler(TaskTopics.RUNTIME_SET_STATUS)
def handle_runtime_set_status(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime status
    
    幂等性：CAS - 检查 expected_status
    
    Payload:
        runtime_id: str
        expected_status: str
        new_status: str
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = biz.set_status(
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


@register_handler(TaskTopics.RUNTIME_INCREMENT_ROUND)
def handle_runtime_increment_round(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    增加 Runtime round 计数
    
    Payload:
        runtime_id: str
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    return biz.increment_round(payload["runtime_id"])


@register_handler(TaskTopics.RUNTIME_SET_SUMMARIZED)
def handle_runtime_set_summarized(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime 已生成摘要
    
    幂等性：如果已经是 summarized=1，返回成功
    
    Payload:
        runtime_id: str
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = biz.set_summarized(payload["runtime_id"])
    
    response = {
        "success": result.success,
        "runtime_id": result.runtime_id,
    }
    
    if result.message:
        response["message"] = result.message
    
    return response


@register_handler(TaskTopics.RUNTIME_SET_NEED_REST)
def handle_runtime_set_need_rest(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime need_rest 标志
    
    幂等性：如果已经是目标值，返回成功
    
    Payload:
        runtime_id: str
        value: bool (可选，默认 True)
    """
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    
    result = biz.set_need_rest(
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


@register_handler(TaskTopics.RUNTIME_CHECK_NEW_MESSAGES)
def handle_check_new_messages(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    检查是否有新的 sent 消息 + need_rest 状态
    
    用于 ReactActions 判断是否继续循环
    
    重要：如果有新消息且 need_rest=1，自动重置 need_rest=0
    这确保用户发送新消息时，Agent 不会意外结束。
    
    Payload:
        runtime_id: str
        agent_id: str
    
    Returns:
        has_new_messages: bool - 是否有新消息
        need_rest: bool - 是否需要休息（重置后的值）
        need_rest_reset: bool - 是否进行了重置
    """
    runtime_id = payload["runtime_id"]
    agent_id = payload["agent_id"]
    biz = RuntimeBusiness(ctx["gateway_url"], client=ctx.get("gateway_client"))
    runtime = biz.get(runtime_id)
    need_rest = bool(runtime.get("need_rest")) if runtime else False

    from ..client import GatewayInternalClient
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    msg_resp = client.has_new_messages(agent_id)
    has_new = bool(msg_resp.get("has_new_messages"))
    
    # 关键逻辑：如果有新消息且 need_rest=1，重置 need_rest=0
    # 这样 Agent 会继续处理新消息，而不是意外结束
    need_rest_reset = False
    if has_new and need_rest:
        print(f"[runtime.check_new_messages] {runtime_id}: has_new_messages=True, need_rest=True -> resetting need_rest to 0")
        try:
            reset_result = biz.set_need_rest(runtime_id, value=False)
            if reset_result.success:
                need_rest = False
                need_rest_reset = True
                print(f"[runtime.check_new_messages] {runtime_id}: need_rest reset successfully")
            else:
                print(f"[runtime.check_new_messages] {runtime_id}: need_rest reset failed: {reset_result.message}")
        except Exception as e:
            print(f"[runtime.check_new_messages] {runtime_id}: need_rest reset error: {e}")
            # 重置失败不影响主流程，继续返回原始状态
    
    return {
        "success": True,
        "runtime_id": runtime_id,
        "has_new_messages": has_new,
        "need_rest": need_rest,
        "need_rest_reset": need_rest_reset,
    }


@register_handler(TaskTopics.RUNTIME_GENERATE_SIMPLE_SUMMARY)
def handle_generate_simple_summary(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    生成并保存 Simple Summary
    
    在 RuntimeComplete 流程中同步调用。
    从 runtime context 生成纯文本摘要：
    - 除最后3轮外：保留 think + tools + [task_result:xxx_id]
    - 最后3轮：保留 think + tools + full_result
    
    Payload:
        runtime_id: str
    
    Returns:
        success: bool
        runtime_id: str
        summary_length: int - summary 字符长度
        rounds_count: int - 识别的轮次数
    """
    from ..utils.simple_summary import generate_simple_summary
    from ..client import GatewayInternalClient
    
    runtime_id = payload["runtime_id"]
    
    # 获取 GatewayInternalClient
    client = ctx.get("gateway_client") or GatewayInternalClient(ctx["gateway_url"])
    
    # 1. 获取 runtime context
    runtime = client.get_runtime(runtime_id)
    if not runtime:
        return {
            "success": False,
            "runtime_id": runtime_id,
            "error": "Runtime not found",
        }
    
    context = runtime.get("context") or []
    
    # 2. 生成 simple summary
    try:
        simple_summary = generate_simple_summary(context)
    except Exception as e:
        return {
            "success": False,
            "runtime_id": runtime_id,
            "error": f"Failed to generate summary: {e}",
        }
    
    # 3. 保存到 runtime
    try:
        client.update_runtime(runtime_id, {"simple_summary": simple_summary})
    except Exception as e:
        return {
            "success": False,
            "runtime_id": runtime_id,
            "error": f"Failed to save summary: {e}",
        }
    
    # 计算轮次数（用于日志）
    from ..utils.simple_summary import split_into_rounds
    rounds_count = len(split_into_rounds(context))
    
    print(f"[runtime.generate_simple_summary] {runtime_id}: generated {len(simple_summary)} chars, {rounds_count} rounds")
    
    return {
        "success": True,
        "runtime_id": runtime_id,
        "summary_length": len(simple_summary),
        "rounds_count": rounds_count,
    }
