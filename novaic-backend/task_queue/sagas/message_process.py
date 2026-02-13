"""
MessageProcess Saga - 消息处理入口 (v3)

流程：
1. claim 消息 (sending → sent)
2. 原子获取或创建 Runtime（替代 awaking 状态）
3. 如果新创建，触发 RuntimeStart Saga

v3 变更：
- 删除 awaking 状态，用 get_or_create_runtime 原子操作替代
- route_message 返回 runtime_id 和 just_created
- 用 runtime_id 作为 Saga 幂等键
"""

from ..saga import SagaDefinition
from . import register_saga_definition
from ..topics import TaskTopics, SagaTopics


def _build_claim_payload(ctx):
    """Step 1: claim 消息"""
    return {"message_id": ctx["message_id"]}


def _build_route_payload(ctx):
    """Step 2: 原子获取或创建 Runtime"""
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "message_id": ctx["message_id"],
    }


def _decide_action(ctx, results):
    """决策下一步"""
    route_result = results.get("route_message", {})
    return {
        "action": route_result.get("action", "skip"),
        "message_id": ctx["message_id"],
        "runtime_id": route_result.get("runtime_id"),
        "just_created": route_result.get("just_created", False),
    }


def _build_trigger_runtime_start(ctx, decision):
    """触发 RuntimeStart Saga
    
    用 runtime_id 作为幂等键，保证同一个 runtime 只启动一次
    
    支持传递：
    - trigger_id: 触发 ID（spawn_subagent 时从 ctx 获取，否则用 message_id）
    - initial_context: sub-subagent 的初始上下文（任务描述等）
    """
    runtime_id = decision.get("runtime_id")
    
    # trigger_id: spawn_subagent 有专门的 trigger_id，其他用 message_id
    trigger_id = ctx.get("trigger_id") or ctx["message_id"]
    
    context = {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "runtime_id": runtime_id,  # 传递已创建的 runtime_id
        "trigger_id": trigger_id,
        "trigger_type": ctx.get("trigger_type", "user_message"),
    }
    
    # 传递 initial_context（sub-subagent spawn 时需要）
    if "initial_context" in ctx and ctx["initial_context"]:
        context["initial_context"] = ctx["initial_context"]
    
    return {
        "saga_type": "runtime_start",
        "context": context,
        # 用 runtime_id 作为幂等键，而不是 message_id
        "idempotency_key": f"runtime-start-{runtime_id}",
    }


# MessageProcess Saga 定义
MESSAGE_PROCESS_SAGA = SagaDefinition("message_process")

MESSAGE_PROCESS_SAGA.add_task_step(
    name="claim_message",
    topic=TaskTopics.MESSAGE_CLAIM,
    build_payload=_build_claim_payload,
)

MESSAGE_PROCESS_SAGA.add_task_step(
    name="route_message",
    topic=TaskTopics.MESSAGE_ROUTE,
    build_payload=_build_route_payload,
)

MESSAGE_PROCESS_SAGA.add_decision_step(
    name="decide_action",
    decide=_decide_action,
)

MESSAGE_PROCESS_SAGA.add_task_step(
    name="trigger_runtime_start",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_runtime_start,
    condition=lambda d: d.get("action") == "start_runtime",
)

# 自动注册
MESSAGE_PROCESS_SAGA = register_saga_definition(MESSAGE_PROCESS_SAGA)
