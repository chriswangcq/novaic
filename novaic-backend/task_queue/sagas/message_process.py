"""
MessageProcess Saga - 消息处理入口 (v2)

流程：
1. claim 消息 (sending → sent)
2. 判断 SubAgent 状态，决定路由
3. 根据路由触发 RuntimeStart 或跳过
"""

from ..saga import SagaDefinition


def _build_claim_payload(ctx):
    """Step 1: claim 消息"""
    return {"message_id": ctx["message_id"]}


def _build_route_payload(ctx):
    """Step 2: 判断路由"""
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
    }


def _build_trigger_runtime_start(ctx, decision):
    """触发 RuntimeStart Saga"""
    return {
        "saga_type": "runtime_start",
        "context": {
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
            "trigger_id": ctx["message_id"],
            "initial_context": ctx.get("initial_context", []),
        },
        "idempotency_key": f"runtime-start-{ctx['message_id']}",
    }


# MessageProcess Saga 定义
MESSAGE_PROCESS_SAGA = SagaDefinition("message_process")

MESSAGE_PROCESS_SAGA.add_task_step(
    name="claim_message",
    topic="message.claim",
    build_payload=_build_claim_payload,
)

MESSAGE_PROCESS_SAGA.add_task_step(
    name="route_message",
    topic="message.route",
    build_payload=_build_route_payload,
)

MESSAGE_PROCESS_SAGA.add_decision_step(
    name="decide_action",
    decide=_decide_action,
)

MESSAGE_PROCESS_SAGA.add_task_step(
    name="trigger_runtime_start",
    topic="saga.trigger",
    build_payload=_build_trigger_runtime_start,
    condition=lambda d: d.get("action") == "start_runtime",
)
