"""
Runtime Handlers - Runtime 生命周期管理

Topics:
- runtime.create: 创建 Runtime 记录（包含历史 Context 构建）
- runtime.set_status: 设置 status (CAS)
- runtime.set_summarized: 设置 summarized 标志
- runtime.set_need_rest: 设置 need_rest 标志
- runtime.increment_round: 增加 round 计数
- runtime.check_new_messages: 检查是否有新消息 + need_rest

DEPRECATED:
- runtime.update_phase: 已删除，Saga 步骤替代 phase 状态

使用 task_queue.business.RuntimeBusiness 业务逻辑层。
"""

from typing import Dict, Any
from . import register_handler
from ..business import RuntimeBusiness
from ..utils.context_builder import build_initial_context
from ..topics import TaskTopics
from common.exceptions import ValidationError, NotFoundError


@register_handler(TaskTopics.RUNTIME_CREATE)
def handle_runtime_create(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    创建或初始化 Runtime 记录，并从历史构建初始 Context
    
    v3 变更：
    - 支持传入 runtime_id（初始化已有 runtime）
    - 如果没有 runtime_id，则创建新的（兼容旧逻辑）
    
    初始 Context 构建规则：
    1. historical_summary: SubAgent 的合并历史摘要
    2. hrl[:-5] 的 cold_summary: 较早的 runtime
    3. hrl[-5:] 的 hot_summary: 最近的 runtime
    
    幂等性：idempotency_key 唯一约束
    
    Payload:
        agent_id: str
        subagent_id: str
        runtime_id: str (可选，v3 新增) - 已创建的 runtime_id
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
    runtime_id = payload.get("runtime_id")  # v3: 可能已经创建
    user_message = payload.get("user_message")  # For auto-matching skills
    
    gateway_client = ctx.get("gateway_client")
    ro_client = ctx.get("ro_client")
    if not gateway_client or not ro_client:
        raise ValidationError(
            "Missing required clients in ctx: gateway_client and ro_client "
            "(fallback creation is disabled)"
        )
    biz = RuntimeBusiness(ctx["gateway_url"], ro_client=ro_client)
    
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
            initial_context = build_initial_context(agent_id, subagent_id, ro_client=ro_client)
            context_parts = len(initial_context)
            if context_parts > 0:
                print(f"[runtime.create] Built initial context with {context_parts} parts for {subagent_id}")
        except Exception as e:
            # Context 构建失败不阻塞 runtime 创建
            print(f"[runtime.create] Failed to build initial context for {subagent_id}: {e}")
    
    # System Prompt: 统一的，不区分场景
    # 用户消息和定时唤醒的区别只在于消息内容，由 ReactThink 从 DB 统一读取
    try:
        from ..utils.system_prompt import build_system_prompt
        sys_prompt = build_system_prompt(
            agent_id,
            gateway_client=gateway_client,
            ro_client=ro_client,
            task=user_message,  # Pass user message for auto-matching
            auto_match_skills=True,
            subagent_id=subagent_id,  # Pass subagent_id for Sub SubAgent specific prompts
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
                    match_resp = gateway_client.match_skills_for_task(user_message)
                    matched_skills = [s.get("name") for s in match_resp.get("matched_skills", [])]
                    if matched_skills:
                        print(f"[runtime.create] Auto-matched skills: {matched_skills}")
                except Exception:
                    pass
    except Exception as e:
        print(f"[runtime.create] Failed to build system prompt for {subagent_id}: {e}")
    
    # v3: 如果已有 runtime_id，更新其 context；否则创建新的
    if runtime_id:
        # 初始化已有 runtime：更新 context
        try:
            ro_client.update_runtime(runtime_id, {"context": initial_context})
            print(f"[runtime.create] Initialized existing runtime {runtime_id} with {context_parts} context parts")
            return {
                "success": True,
                "runtime_id": runtime_id,
                "created": False,
                "message": "Runtime initialized",
                "status": "active",
                "phase": "",
                "context_parts": context_parts,
                "matched_skills": matched_skills,
            }
        except Exception as e:
            print(f"[runtime.create] Failed to initialize runtime {runtime_id}: {e}")
            # 继续尝试创建新的
    
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


# DEPRECATED: handle_runtime_update_phase 已删除，Saga 步骤替代 phase 状态


@register_handler(TaskTopics.RUNTIME_SET_STATUS)
def handle_runtime_set_status(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime status
    
    幂等性：CAS - 检查 expected_status
    
    Payload:
        runtime_id: str
        expected_status: str
        new_status: str
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    # 验证必填字段
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    if not payload.get("expected_status"):
        raise ValidationError("Missing required field: expected_status")
    if not payload.get("new_status"):
        raise ValidationError("Missing required field: new_status")
    
    biz = RuntimeBusiness(ctx["gateway_url"], ro_client=ctx.get("ro_client"))
    
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
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    biz = RuntimeBusiness(ctx["gateway_url"], ro_client=ctx.get("ro_client"))
    return biz.increment_round(payload["runtime_id"])


@register_handler(TaskTopics.RUNTIME_SET_SUMMARIZED)
def handle_runtime_set_summarized(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    设置 Runtime 已生成摘要
    
    幂等性：如果已经是 summarized=1，返回成功
    
    Payload:
        runtime_id: str
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    biz = RuntimeBusiness(ctx["gateway_url"], ro_client=ctx.get("ro_client"))
    
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
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    biz = RuntimeBusiness(ctx["gateway_url"], ro_client=ctx.get("ro_client"))
    
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
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    if not payload.get("agent_id"):
        raise ValidationError("Missing required field: agent_id")
    
    runtime_id = payload["runtime_id"]
    agent_id = payload["agent_id"]
    biz = RuntimeBusiness(ctx["gateway_url"], ro_client=ctx.get("ro_client"))
    runtime = biz.get(runtime_id)
    need_rest = bool(runtime.get("need_rest")) if runtime else False

    gateway_client = ctx.get("gateway_client")
    if not gateway_client:
        raise ValidationError(
            "Missing required client in ctx: gateway_client "
            "(fallback creation is disabled)"
        )
    msg_resp = gateway_client.has_new_messages(agent_id)
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
        
    Raises:
        ValidationError: 当必填字段缺失时
        NotFoundError: 当 Runtime 不存在时
    """
    from ..utils.simple_summary import generate_simple_summary
    
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    runtime_id = payload["runtime_id"]
    ro_client = ctx.get("ro_client")
    if not ro_client:
        raise ValidationError(
            "Missing required client in ctx: ro_client "
            "(fallback creation is disabled)"
        )
    
    # 1. 获取 runtime context
    runtime = ro_client.get_runtime(runtime_id)
    if not runtime:
        raise NotFoundError(f"Runtime not found: {runtime_id}")
    
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
        ro_client.update_runtime(runtime_id, {"simple_summary": simple_summary})
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
        "simple_summary": simple_summary,  # 返回 summary 内容，用于 SubAgent result
        "summary_length": len(simple_summary),
        "rounds_count": rounds_count,
    }
