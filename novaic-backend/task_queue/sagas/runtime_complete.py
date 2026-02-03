"""
RuntimeComplete Saga - Runtime 完成流程 (v2)

流程：
1. 设置 Runtime 状态为 completed
2. 设置 SubAgent 状态为 sleeping
3. 销毁 MCP Server
4. 异步触发 Summarize Saga
"""

from ..saga import SagaDefinition


def _build_set_completed_payload(ctx):
    """构建 runtime.set_status payload"""
    return {
        "runtime_id": ctx["runtime_id"],
        "expected_status": "active",  # v2: status 只有 active/completed
        "new_status": "completed",
    }


def _build_set_sleeping_payload(ctx):
    """构建 subagent.set_sleeping payload"""
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
    }


def _build_destroy_mcp_payload(ctx):
    """构建 mcp.destroy payload"""
    return {
        "runtime_id": ctx["runtime_id"],
    }


def _build_trigger_summarize_payload(ctx):
    """异步触发 Summarize Saga"""
    return {
        "saga_type": "summarize",
        "context": {
            "runtime_id": ctx["runtime_id"],
            "agent_id": ctx["agent_id"],
        },
        "idempotency_key": f"summarize-{ctx['runtime_id']}",
    }


# RuntimeComplete Saga 定义 (v2)
RUNTIME_COMPLETE_SAGA = SagaDefinition("runtime_complete")

# Step 1: 设置 Runtime 状态为 completed
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="set_runtime_completed",
    topic="runtime.set_status",
    build_payload=_build_set_completed_payload,
)

# Step 2: 设置 SubAgent 状态为 sleeping
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="set_subagent_sleeping",
    topic="subagent.set_sleeping",
    build_payload=_build_set_sleeping_payload,
)

# Step 3: 销毁 MCP Server
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="destroy_mcp",
    topic="mcp.destroy",
    build_payload=_build_destroy_mcp_payload,
)

# Step 4: 异步触发 Summarize Saga
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="trigger_summarize",
    topic="saga.trigger",
    build_payload=_build_trigger_summarize_payload,
)
