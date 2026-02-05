"""
Task Queue Utils - 通用工具模块

可复用的工具函数，独立于业务逻辑：
- context: Context 清理和处理
- context_builder: 新 Runtime 启动时的 Context 构建
- broadcast: 事件广播
- result: 结果摘要和处理
- multimodal: 多模态内容处理（图片等）
- simple_summary: Runtime 简化摘要生成
"""

from .context import (
    sanitize_context,
    process_multimodal_messages,
)
from .context_builder import (
    build_initial_context,
    build_context_summary,
)
from .broadcast import (
    broadcast_log,
    sync_broadcast_log,
    BroadcastType,
)
from .result import (
    summarize_result,
    has_images,
)
from .multimodal import (
    extract_from_result,
    to_openai_content,
    to_anthropic_content,
    result_to_text_only,
    IMAGE_FIELD_NAMES,
)
from .simple_summary import (
    generate_simple_summary,
    split_into_rounds,
    Round,
    format_round_full,
    format_rounds_for_llm,
    prepare_hot_summary_parts,
    prepare_cold_summary_text,
    HOT_SUMMARY_PROMPT,
    COLD_SUMMARY_PROMPT,
)

__all__ = [
    # context
    "sanitize_context",
    "process_multimodal_messages",
    # context_builder
    "build_initial_context",
    "build_context_summary",
    # broadcast
    "broadcast_log",
    "sync_broadcast_log",
    "BroadcastType",
    # result
    "summarize_result",
    "has_images",
    # multimodal
    "extract_from_result",
    "to_openai_content",
    "to_anthropic_content",
    "result_to_text_only",
    "IMAGE_FIELD_NAMES",
    # simple_summary
    "generate_simple_summary",
    "split_into_rounds",
    "Round",
    "format_round_full",
    "format_rounds_for_llm",
    "prepare_hot_summary_parts",
    "prepare_cold_summary_text",
    "HOT_SUMMARY_PROMPT",
    "COLD_SUMMARY_PROMPT",
]
