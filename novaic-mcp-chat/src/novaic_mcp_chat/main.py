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
    instructions="""NovAIC Chat - Agent ↔ User 通信

6 个工具用于与用户进行对话交互。

## ⚠️ 重要架构说明

界面分为两个区域：
- **Agent Log**: 显示思考过程、工具调用 (自动展示)
- **Chat Panel**: 显示与用户的对话 (需要调用本工具)

**只有调用本工具的内容才会出现在 Chat Panel！**

## 工具一览

| 工具 | 用途 |
|------|------|
| chat_reply | 发送消息给用户 |
| chat_ask | 提问并等待用户回复 |
| chat_notify | 发送通知 (无需回复) |
| chat_show_image | 展示图片 |
| chat_history | 查看历史消息 (摘要) |
| chat_get_message | 按 ID 获取完整消息 |

## 使用时机

### ✅ 应该使用 chat_reply 的情况
- 任务完成，需要告知用户结果
- 需要向用户解释某件事
- 主动提供信息或建议

### ✅ 应该使用 chat_ask 的情况
- 需要用户确认 (如删除操作)
- 需要用户提供额外信息
- 有多个选项需要用户选择

### ✅ 应该使用 chat_notify 的情况
- 状态更新 (如 "正在处理...")
- 警告信息
- 非关键性通知

### ❌ 不需要使用的情况
- 正在思考分析 (自动显示在 Agent Log)
- 调用其他工具 (自动显示在 Agent Log)

## 典型工作流

```
用户: "帮我打开 Google"

[Agent Log]
思考: 用户想访问 Google
调用: browser_navigate(url="https://google.com")
结果: 导航成功

[调用 Chat 工具]
chat_reply("已经打开 Google 首页")

[Chat Panel]
Agent: 已经打开 Google 首页
```

## chat_ask 示例

```
result = chat_ask(
    question="你想用哪个浏览器？",
    options=["Chrome", "Firefox", "Safari"],
    timeout_seconds=60
)
# result.response = "Chrome" 或 result.selected_option = 0
```

## chat_notify 级别

| level | 用途 |
|-------|------|
| info | 一般信息 |
| success | 成功提示 |
| warning | 警告信息 |
| error | 错误提示 |

## chat_history 使用

```
# 先看摘要列表
history = chat_history(limit=20, summary_length=50)
# 返回: [{"id": "abc", "summary": "消息摘要...", "is_truncated": true}]

# 需要完整内容时按 ID 查询
detail = chat_get_message("abc")
```
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
