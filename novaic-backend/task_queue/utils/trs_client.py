"""
TRS Client - 薄封装层，委托给 TRS SDK

推荐直接使用 task_queue.utils.trs_sdk 的 TRSClient。
"""

import logging
from typing import Any, Dict, List, Optional

from .trs_sdk import get_trs_client

logger = logging.getLogger(__name__)


def push_raw_result_to_trs(
    raw_result: Any,
    agent_id: str,
    tool_name: str = "unknown",
    tool_call_id: Optional[str] = None,
    trs_url: Optional[str] = None,
) -> Optional[str]:
    """
    [委托 TRS SDK] 将 raw tool result 推入 TRS，返回 result_id。
    推荐使用 get_trs_client().create_from_raw()。
    """
    client = get_trs_client(trs_url) if trs_url else get_trs_client()
    return client.create_from_raw(raw_result, agent_id, tool_name, tool_call_id)


def expand_result_id_to_content(
    result_id: str,
    provider: str = "openai",
    trs_url: Optional[str] = None,
) -> str:
    """[委托 TRS SDK] 转为 process_multimodal_messages 期望的 JSON 字符串。"""
    client = get_trs_client(trs_url) if trs_url else get_trs_client()
    return client.to_llm_content(result_id, provider)


def fetch_result_for_llm(
    result_id: str,
    provider: str = "openai",
    trs_url: Optional[str] = None,
) -> str:
    """[委托 TRS SDK] 用于 LLM 的完整 content。"""
    return expand_result_id_to_content(result_id, provider=provider, trs_url=trs_url)


def fetch_result_preview(
    result_id: str,
    max_text_len: int = 500,
    trs_url: Optional[str] = None,
) -> str:
    """[委托 TRS SDK] 用于摘要的文本预览。"""
    client = get_trs_client(trs_url) if trs_url else get_trs_client()
    return client.get_preview(result_id, max_text_len)


def expand_messages_for_llm(
    messages: List[Dict[str, Any]],
    provider: str = "openai",
    trs_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    按需展开：仅对将要发给 LLM 的 tool 消息展开 result_id → 完整 content。
    用于 LLM 调用前。
    """
    out = []
    for msg in messages:
        role = msg.get("role")
        result_id = msg.get("result_id")
        if role in ("tool", "tool_result"):
            # tool 消息必须有 result_id
            if not result_id:
                raise ValueError(f"Tool message missing result_id: {msg}")
            content = fetch_result_for_llm(result_id, provider, trs_url)
            new_msg = {k: v for k, v in msg.items() if k not in ("result_id", "_round_id", "_message_type", "_idempotency_key")}
            new_msg["content"] = content
            out.append(new_msg)
        else:
            out.append(msg)
    return out


def expand_messages_for_summary(
    messages: List[Dict[str, Any]],
    trs_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    按需展开：仅对 tool 消息展开 result_id → 文本预览（用于摘要，不含图片）。
    调用 TRS /preview，比 /for-llm 轻量。
    """
    out = []
    for msg in messages:
        role = msg.get("role")
        result_id = msg.get("result_id")
        if role in ("tool", "tool_result"):
            # tool 消息必须有 result_id
            if not result_id:
                raise ValueError(f"Tool message missing result_id: {msg}")
            content = fetch_result_preview(result_id, trs_url=trs_url)
            new_msg = {k: v for k, v in msg.items() if k not in ("result_id", "_round_id", "_message_type", "_idempotency_key")}
            new_msg["content"] = content
            out.append(new_msg)
        else:
            out.append(msg)
    return out


def expand_context_result_ids(
    context: List[Dict[str, Any]],
    trs_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    [已废弃] 统一展开所有 result_id，建议改用：
    - expand_messages_for_llm：LLM 调用时
    - expand_messages_for_summary：摘要生成时
    """
    return expand_messages_for_llm(context, provider="openai", trs_url=trs_url)
