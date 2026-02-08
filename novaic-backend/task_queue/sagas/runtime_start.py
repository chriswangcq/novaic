"""
RuntimeStart Saga - Runtime 启动流程

流程：
1. 创建 Runtime 记录
2. 创建 MCP Server
3. 设置 SubAgent 为 awake
4. 触发 ReactThink Saga
"""

from ..saga import SagaDefinition
from . import register_saga_definition
from ..topics import TaskTopics, SagaTopics


def _build_runtime_create_payload(ctx):
    """构建 runtime.create payload"""
    payload = {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "idempotency_key": f"runtime-{ctx['subagent_id']}-{ctx.get('trigger_id', '')}",
    }
    
    # Sub-subagent 需要 initial_context（包含任务描述）
    # Main subagent 从历史摘要构建 context
    if "initial_context" in ctx and ctx["initial_context"]:
        payload["initial_context"] = ctx["initial_context"]
    
    return payload


def _build_mcp_create_payload(ctx, prev_result):
    """构建 mcp.create payload"""
    return {
        "runtime_id": prev_result["runtime_id"],
        "agent_id": ctx["agent_id"],
    }


def _build_set_awake_payload(ctx, prev_result):
    """构建 subagent.set_awake payload"""
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "runtime_id": ctx.get("runtime_id") or prev_result.get("runtime_id"),
    }


def _build_trigger_think_payload(ctx, prev_result):
    """构建 saga.trigger payload - 触发 ReactThink"""
    # 从之前步骤结果中获取 runtime_id
    runtime_id = ctx.get("runtime_id")
    if not runtime_id:
        # 从 create_runtime 结果获取
        create_result = prev_result if isinstance(prev_result, dict) else {}
        runtime_id = create_result.get("runtime_id")
    
    return {
        "saga_type": "react_think",
        "context": {
            "runtime_id": runtime_id,
            "agent_id": ctx["agent_id"],
            "subagent_id": ctx["subagent_id"],
            "round_num": 1,
            # 移除 messages - 所有消息由 ReactThink 的 context.read 统一读取
            "model": ctx.get("model", "gpt-4o"),
            "tools": ctx.get("tools", []),
        },
        "idempotency_key": f"react-think-{runtime_id}-round1",
    }


# RuntimeStart Saga 定义
RUNTIME_START_SAGA = SagaDefinition("runtime_start")

RUNTIME_START_SAGA.add_task_step(
    name="create_runtime",
    topic=TaskTopics.RUNTIME_CREATE,
    build_payload=_build_runtime_create_payload,
)

RUNTIME_START_SAGA.add_task_step(
    name="create_mcp",
    topic=TaskTopics.MCP_CREATE,
    build_payload=_build_mcp_create_payload,
)

RUNTIME_START_SAGA.add_task_step(
    name="set_subagent_awake",
    topic=TaskTopics.SUBAGENT_SET_AWAKE,
    build_payload=_build_set_awake_payload,
)

RUNTIME_START_SAGA.add_task_step(
    name="trigger_think",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_think_payload,
)

# 自动注册
RUNTIME_START_SAGA = register_saga_definition(RUNTIME_START_SAGA)
