"""
Task Queue Utils - 通用工具模块

可复用的工具函数，独立于业务逻辑：
- context: Context 清理和处理
- broadcast: 事件广播
- result: 结果摘要和处理
- multimodal: 多模态内容处理（图片等）
"""

from .context import (
    sanitize_context,
    process_multimodal_messages,
)
from .broadcast import (
    broadcast_log,
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

__all__ = [
    # context
    "sanitize_context",
    "process_multimodal_messages",
    # broadcast
    "broadcast_log",
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
]
