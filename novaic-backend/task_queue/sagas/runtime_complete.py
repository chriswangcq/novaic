"""
RuntimeComplete Saga - Runtime 完成流程 (v4)

流程：
1. 设置 Runtime 状态为 completed
2. 生成 Simple Summary（同步，纯文本）
3. 设置 SubAgent 状态：
   - Main SubAgent (main-*): set_sleeping
   - Sub SubAgent (sub-*): set_completed（带 result）
4. 通知 Parent SubAgent（仅 Sub SubAgent）
5. 销毁 MCP Server
6. 异步触发 Summarize Saga
"""

from common.enums import RuntimeStatus
from ..saga import SagaDefinition
from . import register_saga_definition
from ..topics import TaskTopics, SagaTopics


def _is_sub_subagent(subagent_id: str) -> bool:
    """判断是否为 Sub SubAgent（subagent_id 以 'sub-' 开头）"""
    return subagent_id.startswith("sub-")


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
    """构建 subagent.set_sleeping payload（用于 Main SubAgent）"""
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
    }


def _build_set_subagent_completed_payload(ctx):
    """构建 subagent.set_completed payload（用于 Sub SubAgent）
    
    result 优先从 step 2 的 simple_summary 获取，
    如果没有则从 runtime context 的最后一条 assistant 消息获取。
    """
    # 尝试从 step_results 获取 simple_summary
    result = None
    step_results = ctx.get("step_results", {})
    
    # Step 2 的结果包含 simple_summary
    generate_summary_result = step_results.get("generate_simple_summary", {})
    if generate_summary_result:
        result = generate_summary_result.get("simple_summary")
    
    # 如果没有 simple_summary，尝试从 context 获取最后一条 assistant 消息
    if not result:
        runtime_context = ctx.get("runtime_context", [])
        for msg in reversed(runtime_context):
            if msg.get("role") == "assistant":
                result = msg.get("content", "")
                break
    
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "result": result,
    }


def _should_set_sleeping(ctx) -> bool:
    """条件：Main SubAgent 使用 set_sleeping"""
    return not _is_sub_subagent(ctx.get("subagent_id", "main"))


def _should_set_completed(ctx) -> bool:
    """条件：Sub SubAgent 使用 set_completed"""
    return _is_sub_subagent(ctx.get("subagent_id", "main"))


def _build_notify_parent_payload(ctx):
    """构建 message.notify_parent payload（用于 Sub SubAgent 通知 Parent）
    
    result 优先从 step_results 获取，与 set_completed 保持一致。
    """
    # 尝试从 step_results 获取 simple_summary
    result = None
    step_results = ctx.get("step_results", {})
    
    # Step 2 的结果包含 simple_summary
    generate_summary_result = step_results.get("generate_simple_summary", {})
    if generate_summary_result:
        result = generate_summary_result.get("simple_summary")
    
    # 如果没有 simple_summary，尝试从 context 获取最后一条 assistant 消息
    if not result:
        runtime_context = ctx.get("runtime_context", [])
        for msg in reversed(runtime_context):
            if msg.get("role") == "assistant":
                result = msg.get("content", "")
                break
    
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx["subagent_id"],
        "parent_subagent_id": ctx.get("parent_subagent_id"),  # 可能为空，handler 会处理
        "result": result,
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


# RuntimeComplete Saga 定义 (v3)
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

# Step 3a: 设置 Main SubAgent 状态为 sleeping（条件执行）
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="set_subagent_sleeping",
    topic=TaskTopics.SUBAGENT_SET_SLEEPING,
    build_payload=_build_set_sleeping_payload,
    condition=_should_set_sleeping,
)

# Step 3b: 设置 Sub SubAgent 状态为 completed（条件执行，带 result）
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="set_subagent_completed",
    topic=TaskTopics.SUBAGENT_SET_COMPLETED,
    build_payload=_build_set_subagent_completed_payload,
    condition=_should_set_completed,
)

# Step 4: 通知 Parent SubAgent（仅 Sub SubAgent）
# 发送 SUBAGENT_COMPLETED 消息，触发 Watchdog 唤醒或被 ReactThink 读取
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="notify_parent",
    topic=TaskTopics.MESSAGE_NOTIFY_PARENT,
    build_payload=_build_notify_parent_payload,
    condition=_should_set_completed,  # 与 set_completed 相同条件
    optional=True,  # 通知失败不应阻塞整个流程
)

# Step 5: 销毁 MCP Server
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="destroy_mcp",
    topic=TaskTopics.MCP_DESTROY,
    build_payload=_build_destroy_mcp_payload,
)

# Step 6: 异步触发 Summarize Saga
RUNTIME_COMPLETE_SAGA.add_task_step(
    name="trigger_summarize",
    topic=SagaTopics.SAGA_TRIGGER,
    build_payload=_build_trigger_summarize_payload,
)

# 自动注册
RUNTIME_COMPLETE_SAGA = register_saga_definition(RUNTIME_COMPLETE_SAGA)
