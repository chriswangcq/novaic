"""
Summarize Saga - 异步生成摘要

流程：
1. 调用 LLM 生成摘要
2. 设置 summarized = true
"""

from ..saga import SagaDefinition


def _build_summary_payload(ctx):
    """构建 llm.call_summary payload"""
    return {
        "runtime_id": ctx["runtime_id"],
        "model": ctx.get("summary_model", "gpt-4o-mini"),
    }


def _build_set_summarized_payload(ctx):
    """构建 runtime.set_summarized payload"""
    return {
        "runtime_id": ctx["runtime_id"],
    }


# Summarize Saga 定义
SUMMARIZE_SAGA = SagaDefinition("summarize")

# Step 1: 生成摘要
SUMMARIZE_SAGA.add_task_step(
    name="generate_summary",
    topic="llm.call_summary",
    build_payload=_build_summary_payload,
    optional=True,  # 摘要生成失败不影响整体
)

# Step 2: 设置 summarized 标志
SUMMARIZE_SAGA.add_task_step(
    name="set_summarized",
    topic="runtime.set_summarized",
    build_payload=_build_set_summarized_payload,
)
