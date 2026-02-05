"""
Summarize Saga - 异步生成摘要 (v25)

流程：
1. 调用 LLM 生成 Hot Summary 和 Cold Summary
2. 设置 summarized = true
3. 添加 runtime_id 到 HRL
4. 条件执行 History Merge（当 HRL 长度 > 15 且 lock == 0）

Hot Summary:
- 除最后3轮外：LLM 总结成一段话
- 最后3轮：保留 think + tools + full_result

Cold Summary:
- 所有轮次：LLM 总结成一段话

History Merge:
- 当 HRL 长度 > 15 时触发
- 合并 hrl[:-5] 的 cold_summaries 到 historical_summary
"""

from ..saga import SagaDefinition
from . import register_saga_definition
from ..topics import TaskTopics


def _build_hot_cold_summary_payload(ctx):
    """构建 llm.call_hot_cold_summary payload"""
    payload = {
        "runtime_id": ctx["runtime_id"],
    }
    # 只有显式指定了 summary_model 才传入，否则使用 agent 的默认模型
    if ctx.get("summary_model"):
        payload["model"] = ctx["summary_model"]
    return payload


def _build_set_summarized_payload(ctx):
    """构建 runtime.set_summarized payload"""
    return {
        "runtime_id": ctx["runtime_id"],
    }


def _build_add_to_hrl_payload(ctx):
    """构建 summary.add_to_hrl payload
    
    将当前 runtime_id 加入 HRL。
    """
    return {
        "runtime_id": ctx["runtime_id"],
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx.get("subagent_id", "main"),  # 默认为 main
    }


def _build_merge_history_payload(ctx):
    """构建 summary.merge_history_if_needed payload
    
    条件执行 History Merge：检查 HRL 长度 > 15 且 lock == 0。
    """
    return {
        "agent_id": ctx["agent_id"],
        "subagent_id": ctx.get("subagent_id", "main"),  # 默认为 main
    }


# Summarize Saga 定义 (v25)
SUMMARIZE_SAGA = SagaDefinition("summarize")

# Step 1: 生成 Hot/Cold Summary
SUMMARIZE_SAGA.add_task_step(
    name="generate_hot_cold_summary",
    topic=TaskTopics.LLM_CALL_HOT_COLD_SUMMARY,
    build_payload=_build_hot_cold_summary_payload,
    optional=True,  # 摘要生成失败不影响整体
)

# Step 2: 设置 summarized 标志
SUMMARIZE_SAGA.add_task_step(
    name="set_summarized",
    topic=TaskTopics.RUNTIME_SET_SUMMARIZED,
    build_payload=_build_set_summarized_payload,
)

# Step 3: 添加到 HRL
SUMMARIZE_SAGA.add_task_step(
    name="add_to_hrl",
    topic=TaskTopics.SUMMARY_ADD_TO_HRL,
    build_payload=_build_add_to_hrl_payload,
)

# Step 4: 条件执行 History Merge（optional）
SUMMARIZE_SAGA.add_task_step(
    name="merge_history_if_needed",
    topic=TaskTopics.SUMMARY_MERGE_HISTORY_IF_NEEDED,
    build_payload=_build_merge_history_payload,
    optional=True,  # 失败或跳过不影响 Saga
)

# 自动注册
SUMMARIZE_SAGA = register_saga_definition(SUMMARIZE_SAGA)
