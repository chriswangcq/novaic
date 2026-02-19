"""
Gateway-local message context helpers.

These utilities intentionally avoid imports from task_queue so gateway can run
as an independent service boundary.
"""

from typing import Any, Dict, List


def sanitize_context(context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize LLM message list and keep tool ordering valid."""
    if not context:
        return []

    cleaned: List[Dict[str, Any]] = []
    for msg in context:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "")
        if not role:
            if msg.get("_round_id") or msg.get("_message_type") or msg.get("_idempotency_key"):
                continue
            continue

        if role not in ("tool", "tool_result"):
            content = msg.get("content")
            tool_calls = msg.get("tool_calls")
            if role == "assistant" and tool_calls:
                pass
            elif content is None:
                continue

        kept: Dict[str, Any] = {}
        for key in ("role", "content", "tool_calls", "tool_call_id", "name", "reasoning_content"):
            if key in msg:
                kept[key] = msg[key]

        if kept.get("role") == "assistant" and kept.get("tool_calls"):
            kept.setdefault("reasoning_content", "")

        cleaned.append(kept)

    assistant_tool_calls: Dict[str, Dict[str, Any]] = {}
    tool_results: Dict[str, Dict[str, Any]] = {}
    others: List[tuple[int, Dict[str, Any]]] = []
    assistants_with_tools: Dict[int, Dict[str, Any]] = {}

    for idx, msg in enumerate(cleaned):
        role = msg.get("role")
        if role == "assistant" and msg.get("tool_calls"):
            assistants_with_tools[idx] = msg
            for tc in msg["tool_calls"]:
                tc_id = tc.get("id")
                if not tc_id:
                    continue
                fn = tc.get("function", {})
                assistant_tool_calls[tc_id] = {"assistant_idx": idx, "name": fn.get("name", "unknown")}
        elif role in ("tool_result", "tool"):
            tc_id = msg.get("tool_call_id")
            if tc_id and tc_id in assistant_tool_calls:
                tool_results[tc_id] = msg
            elif not tc_id:
                others.append((idx, msg))
        else:
            others.append((idx, msg))

    result: List[Dict[str, Any]] = []
    done_assistant_idx = set()

    for orig_idx, msg in others:
        for asst_idx in sorted(assistants_with_tools.keys()):
            if asst_idx >= orig_idx or asst_idx in done_assistant_idx:
                continue
            asst_msg = assistants_with_tools[asst_idx]
            result.append(asst_msg)
            done_assistant_idx.add(asst_idx)

            for tc in asst_msg.get("tool_calls", []):
                tc_id = tc.get("id")
                if not tc_id:
                    continue
                if tc_id in tool_results:
                    result.append(tool_results[tc_id])
                else:
                    fn = tc.get("function", {})
                    result.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "name": fn.get("name", "unknown"),
                            "content": "[Execution was interrupted. Please retry if needed.]",
                        }
                    )
        result.append(msg)

    for asst_idx in sorted(assistants_with_tools.keys()):
        if asst_idx in done_assistant_idx:
            continue
        asst_msg = assistants_with_tools[asst_idx]
        result.append(asst_msg)
        for tc in asst_msg.get("tool_calls", []):
            tc_id = tc.get("id")
            if not tc_id:
                continue
            if tc_id in tool_results:
                result.append(tool_results[tc_id])
            else:
                fn = tc.get("function", {})
                result.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "name": fn.get("name", "unknown"),
                        "content": "[Execution was interrupted. Please retry if needed.]",
                    }
                )

    return result


def process_multimodal_messages(
    messages: List[Dict[str, Any]],
    provider: str = "openai",
) -> List[Dict[str, Any]]:
    """
    Lightweight gateway-side preprocessing.

    For gateway debug endpoints we only normalize user dict payloads and keep
    the original sequence untouched.
    """
    _ = provider
    processed: List[Dict[str, Any]] = []
    for msg in messages:
        if msg.get("role") == "user" and isinstance(msg.get("content"), dict):
            content = msg["content"]
            if "text" in content:
                processed.append({"role": "user", "content": content.get("text", "")})
            else:
                processed.append(msg)
        else:
            processed.append(msg)
    return processed
