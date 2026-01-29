"""
NovAIC MCP Server for Agent-User Chat.

Provides tools for the Agent to communicate with users:
- chat_reply: Send a reply to the user
- chat_ask: Ask user a question and wait for response
- chat_notify: Send a notification (no response expected)
- chat_show_image: Show an image to the user

This separates "agent work" (logs) from "user interaction" (chat).
"""

import os
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP

# Gateway API endpoint
GATEWAY_URL = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:9000")

mcp = FastMCP(
    name="novaic-chat",
    instructions="""This MCP server provides tools for communicating with users.

Use these tools when you want to:
- Reply to the user with a message (chat_reply)
- Ask the user a question and wait for their answer (chat_ask)
- Show a notification without expecting a reply (chat_notify)
- Show an image to the user (chat_show_image)
- Review previous conversation history (chat_history)

IMPORTANT: Your thinking and tool execution are shown in a separate "Agent Log" panel.
Use these chat tools ONLY when you want to directly communicate with the user.

Example workflow:
1. User sends: "帮我打开浏览器访问 google.com"
2. Agent thinks: [shown in Agent Log]
3. Agent calls: browser_navigate(...) [shown in Agent Log]
4. Agent calls: chat_reply("已经打开 Google 首页") [shown in Chat]

Use chat_history when you need to recall what was discussed earlier in the conversation.
"""
)


async def _send_chat_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a chat event to the Gateway EventBus."""
    try:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            response = await client.post(
                f"{GATEWAY_URL}/api/chat/event",
                json={
                    "type": event_type,
                    "data": data
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def chat_reply(
    message: str,
    attachments: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send a reply message to the user.
    
    Use this when you want to communicate results, confirmations, or
    information to the user. This appears in the Chat panel, not the Agent Log.
    
    Args:
        message: The message to send to the user
        attachments: Optional list of file paths or URLs to attach (images, files)
    
    Returns:
        Dictionary with success status and message_id
    
    Examples:
        - chat_reply("任务已完成！")
        - chat_reply("这是搜索结果：...", attachments=["screenshot.png"])
        - chat_reply("已经帮你打开了 Google")
    """
    result = await _send_chat_event("AGENT_REPLY", {
        "message": message,
        "attachments": attachments or [],
        "reply_type": "message"
    })
    return result


@mcp.tool()
async def chat_ask(
    question: str,
    options: Optional[List[str]] = None,
    timeout_seconds: Optional[int] = 300
) -> Dict[str, Any]:
    """
    Ask the user a question and wait for their response.
    
    Use this when you need user input to continue. The execution will
    pause until the user responds or timeout is reached.
    
    Args:
        question: The question to ask the user
        options: Optional list of suggested options for the user to choose from
        timeout_seconds: How long to wait for user response (default: 300s = 5min)
    
    Returns:
        Dictionary with:
        - success: Whether a response was received
        - response: The user's response text
        - selected_option: Index of selected option (if options were provided)
        - timed_out: True if the request timed out
    
    Examples:
        - chat_ask("你想用哪个浏览器？", options=["Chrome", "Firefox", "Safari"])
        - chat_ask("请输入你的搜索关键词")
        - chat_ask("确定要删除这些文件吗？", options=["是", "否"])
    """
    # Send the question event
    event_result = await _send_chat_event("AGENT_ASK", {
        "question": question,
        "options": options,
        "timeout_seconds": timeout_seconds,
        "reply_type": "question"
    })
    
    if not event_result.get("success"):
        return event_result
    
    request_id = event_result.get("request_id")
    if not request_id:
        return {"success": False, "error": "No request_id returned"}
    
    # Poll for user response
    start_time = asyncio.get_event_loop().time()
    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout_seconds:
            return {
                "success": False,
                "timed_out": True,
                "error": f"User did not respond within {timeout_seconds} seconds"
            }
        
        try:
            async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
                response = await client.get(
                    f"{GATEWAY_URL}/api/chat/response/{request_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("has_response"):
                        return {
                            "success": True,
                            "response": data.get("response"),
                            "selected_option": data.get("selected_option"),
                            "timed_out": False
                        }
                # Not ready yet, wait and retry
                await asyncio.sleep(1)
        except httpx.HTTPError:
            await asyncio.sleep(1)


@mcp.tool()
async def chat_notify(
    message: str,
    level: Optional[str] = "info"
) -> Dict[str, Any]:
    """
    Send a notification to the user (no response expected).
    
    Use this for status updates, warnings, or informational messages
    that don't require user acknowledgment.
    
    Args:
        message: The notification message
        level: Notification level - "info", "success", "warning", or "error"
    
    Returns:
        Dictionary with success status
    
    Examples:
        - chat_notify("正在处理，请稍候...", level="info")
        - chat_notify("操作成功！", level="success")
        - chat_notify("检测到潜在问题", level="warning")
        - chat_notify("发生错误，请重试", level="error")
    """
    result = await _send_chat_event("AGENT_NOTIFY", {
        "message": message,
        "level": level,
        "reply_type": "notification"
    })
    return result


@mcp.tool()
async def chat_show_image(
    image_path: str,
    caption: Optional[str] = None
) -> Dict[str, Any]:
    """
    Show an image to the user in the chat.
    
    Use this to display screenshots, diagrams, or other visual content.
    
    Args:
        image_path: Path to the image file or base64 encoded image data
        caption: Optional caption to display with the image
    
    Returns:
        Dictionary with success status
    
    Examples:
        - chat_show_image("/tmp/screenshot.png", caption="当前屏幕截图")
        - chat_show_image("data:image/png;base64,...", caption="生成的图表")
    """
    result = await _send_chat_event("AGENT_IMAGE", {
        "image_path": image_path,
        "caption": caption,
        "reply_type": "image"
    })
    return result


@mcp.tool()
async def chat_history(
    limit: Optional[int] = 20,
    before_id: Optional[str] = None,
    message_type: Optional[str] = None,
    summary_length: Optional[int] = 50
) -> Dict[str, Any]:
    """
    Get recent chat history between agent and user (summarized).
    
    Messages are truncated to summary_length characters. Use chat_get_message
    to get full content of a specific message.
    
    Args:
        limit: Maximum number of messages to return (default: 20, max: 100)
        before_id: Get messages before this message ID (for pagination)
        message_type: Filter by type: "user", "agent", "notification", or None for all
        summary_length: Max characters per message (default: 50, 0 for full content)
    
    Returns:
        Dictionary with:
        - messages: List with id, type, timestamp, summary, is_truncated
        - has_more: Whether there are more messages before these
    
    Examples:
        - chat_history() - Get last 20 messages with 50-char summaries
        - chat_history(limit=50, summary_length=100) - 50 messages, 100-char summaries
        - chat_history(message_type="user") - Only user messages
    """
    try:
        params = {"limit": min(limit, 100), "summary_length": summary_length}
        if before_id:
            params["before_id"] = before_id
        if message_type:
            params["message_type"] = message_type
        
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/chat/history",
                params=params
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"success": False, "error": str(e), "messages": []}


@mcp.tool()
async def chat_get_message(message_id: str) -> Dict[str, Any]:
    """
    Get full content of a specific chat message by ID.
    
    Use this after chat_history to get complete message content.
    
    Args:
        message_id: The message ID from chat_history
    
    Returns:
        Dictionary with full message content including:
        - id, type, timestamp
        - message/question (full content)
        - attachments, options, etc.
    
    Examples:
        - chat_get_message("abc123") - Get full message with ID abc123
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            response = await client.get(
                f"{GATEWAY_URL}/api/chat/message/{message_id}"
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"success": False, "error": str(e)}


def main():
    """Run the MCP server."""
    import sys
    
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8085"))
    
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=host, port=port)
    elif transport == "stdio":
        mcp.run(transport="stdio")
    else:
        print(f"Unknown transport: {transport}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
