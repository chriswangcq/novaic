"""
RuntimeComplete Saga - Runtime 完成流程 (v2)

流程：
1. 设置 Runtime 状态为 completed
2. 生成 Simple Summary（同步，纯文本）
3. 设置 SubAgent 状态为 sleeping
4. 销毁 MCP Server
5. 异步触发 Summarize Saga
"""

from common.enums import RuntimeStatus
from ..saga import SagaDefinition
from . import register_saga_definition
from ..topics import TaskTopics, SagaTopics


def _build_set_completed_payload(ctx):
    """构建 runtime.set_status payload"""
    return {
        "runtime_id": ctx["runtime_id"],
        "expected_status": "active",  # v3: status 只有 active/completed
        "new_status": RuntimeStatus.COMPLETED.value,
    }


def _build_generate_simple_summary_payload(ctx):
    """构建 runtime.generate_simple_summary payload"""
    return {
        "runtime_id": ctx["runtime_id"],
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
            "subagent_id": ctx["subagent_id"],  # v24: 传递 subagent_id 用于 history merge
        },
        "idempotency_key": f"summarize-{ctx['runtime_id']}",
    }


# RuntimeComplete Saga 定义 (v2)
RUNTIME_COMPLETE_SAGA = SagaDefinition("runtime_complete")

# Step 1: 设置 Runtime 状态为 completed
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="set_runtime_completed",
    topic=TaskTopics.RUNTIME_SET_STATUS,
    build_payload=_build_set_completed_payload,
)

# Step 2: 生成 Simple Summary（同步，纯文本）
# 在 context 还可用时生成，确保不丢失数据
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="generate_simple_summary",
    topic=TaskTopics.RUNTIME_GENERATE_SIMPLE_SUMMARY,
    build_payload=_build_generate_simple_summary_payload,
    optional=True,  # 失败不影响后续流程
)

# Step 3: 设置 SubAgent 状态为 sleeping
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="set_subagent_sleeping",
    topic=TaskTopics.SUBAGENT_SET_SLEEPING,
    build_payload=_build_set_sleeping_payload,
)

# Step 4: 销毁 MCP Server
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="destroy_mcp",
    topic=TaskTopics.MCP_DESTROY,
    build_payload=_build_destroy_mcp_payload,
)

# Step 5: 异步触发 Summarize Saga
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="trigger_summarize",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_summarize_payload,
)

# 自动注册
RUNTIME_COMPLETE_SAGA = register_saga_definition(RUNTIME_COMPLETE_SAGA)
