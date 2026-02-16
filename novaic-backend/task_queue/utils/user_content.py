"""
User message content 转 LLM 格式

将 {text, attachments} 转为纯文本 + 附件描述。
附件不直接塞 base64，而是告知 Agent 有哪些文件可用，Agent 需要时调用 display 工具查看。
这样统一走 TRS 的 display_files 机制。
"""

from typing import Any, Dict, List


def user_content_to_llm(
    content: Dict[str, Any],
    provider: str = "openai",
) -> List[Dict[str, Any]]:
    """
    将 user message 的 {text, attachments} 转为 LLM content 数组。

    不再拉取图片 base64，只返回文本 + 附件描述。
    Agent 需要查看附件时调用 display(file_url) 工具。

    Args:
        content: {"text": "...", "attachments": [{url, filename, mime_type}]}
        provider: "openai" | "anthropic" (目前不影响输出)

    Returns:
        content 数组，如 [{"type":"text","text":"用户消息...\n\n[附件: xxx.png (url)]"}]
    """
    if not isinstance(content, dict):
        return [{"type": "text", "text": str(content) or ""}]

    text = content.get("text") or ""
    attachments = content.get("attachments") or []

    # 构建附件描述
    att_lines = []
    for att in attachments:
        if not isinstance(att, dict):
            continue
        url = att.get("url") or ""
        filename = att.get("filename") or "file"
        mime = att.get("mime_type") or ""
        if not url:
            continue
        # 告知 Agent 有附件，需要时调用 display 查看
        if mime.startswith("image/"):
            att_lines.append(f"[用户上传图片: {filename}，如需查看请调用 display(file_url=\"{url}\")]")
        else:
            att_lines.append(f"[用户上传文件: {filename}，URL: {url}]")

    # 组合文本和附件描述
    parts = []
    if text:
        parts.append(text)
    if att_lines:
        parts.append("\n".join(att_lines))

    final_text = "\n\n".join(parts) if parts else ""
    return [{"type": "text", "text": final_text}]
