"""
Chat MCP Server - Agent-User 通信

提供 Agent 与用户通过聊天面板通信的工具。
"""

import os
import asyncio
import logging
import httpx
from typing import Optional, List, Dict, Any

from .base import BaseMCPServer

logger = logging.getLogger(__name__)

# Gateway URL
GATEWAY_URL = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")


async def _send_chat_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a chat event to the Gateway."""
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


class ChatMCPServer(BaseMCPServer):
    """
    Chat MCP Server。
    
    每个 Agent 的聊天消息通过 agent_id 隔离。
    
    提供工具：
    - chat_reply: 发送回复消息
    - chat_ask: 询问用户并等待回答
    - chat_notify: 发送通知
    - chat_show_image: 显示图片
    - chat_history: 获取聊天历史
    - chat_get_message: 获取完整消息内容
    """
    
    name = "chat"
    description = "Agent-User 通信工具"
    
    def __init__(self, agent_id: Optional[str] = None, agent_index: int = 0):
        """
        初始化 Chat Server。
        
        Args:
            agent_id: Agent ID，用于隔离聊天消息 (必填)
            agent_index: Agent index，用于端口分配
        """
        if not agent_id:
            raise ValueError("[ChatMCPServer] agent_id is required")
        self._agent_id = agent_id
        super().__init__(agent_id=agent_id, agent_index=agent_index)
        logger.info(f"[ChatMCPServer] Initialized for agent: {self._agent_id}")
    
    def _build_instructions(self) -> str:
        return """Chat MCP - Agent-User 通信

## 工具列表

| 工具 | 用途 |
|------|------|
| chat_reply | 发送回复消息给用户 |
| chat_ask | 询问用户并等待回答 |
| chat_notify | 发送通知（无需回复） |
| chat_show_image | 在聊天中显示图片 |
| chat_history | 获取聊天历史（摘要） |
| chat_get_message | 获取完整消息内容 |

## 使用场景

- **chat_reply**: 告知用户结果、确认
- **chat_ask**: 需要用户输入时
- **chat_notify**: 状态更新、警告
- **chat_show_image**: 展示截图、图表
"""
    
    def _register_tools(self) -> None:
        """注册所有 Chat 工具。"""
        server = self  # Capture for closures
        
        async def _send_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
            """发送聊天事件，自动附加 agent_id。"""
            data["agent_id"] = server._agent_id
            return await _send_chat_event(event_type, data)
        
        @self.mcp.tool()
        async def chat_reply(
            message: str,
            attachments: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Send a reply message to the user.
            
            Use this when you want to communicate results, confirmations, or
            information to the user. This appears in the Chat panel.
            
            Args:
                message: The message to send to the user
                attachments: Optional list of file paths or URLs to attach
            
            Returns:
                Dictionary with success status and message_id
            
            Examples:
                chat_reply("任务已完成！")
                chat_reply("这是搜索结果：...", attachments=["screenshot.png"])
            """
            result = await _send_event("AGENT_REPLY", {
                "message": message,
                "attachments": attachments or [],
                "reply_type": "message"
            })
            return result
        
        @self.mcp.tool()
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
                chat_ask("你想用哪个浏览器？", options=["Chrome", "Firefox", "Safari"])
                chat_ask("请输入你的搜索关键词")
            """
            event_result = await _send_event("AGENT_ASK", {
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
                        await asyncio.sleep(1)
                except httpx.HTTPError:
                    await asyncio.sleep(1)
        
        @self.mcp.tool()
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
                chat_notify("正在处理，请稍候...", level="info")
                chat_notify("操作成功！", level="success")
                chat_notify("检测到潜在问题", level="warning")
            """
            result = await _send_event("AGENT_NOTIFY", {
                "message": message,
                "level": level,
                "reply_type": "notification"
            })
            return result
        
        @self.mcp.tool()
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
                chat_show_image("/tmp/screenshot.png", caption="当前屏幕截图")
            """
            result = await _send_event("AGENT_IMAGE", {
                "image_url": image_path,  # Use image_url for frontend compatibility
                "caption": caption,
                "reply_type": "image"
            })
            return result
        
        @self.mcp.tool()
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
                message_type: Filter by type: "user", "agent", "notification", or None
                summary_length: Max characters per message (default: 50, 0 for full)
            
            Returns:
                Dictionary with messages, has_more
            """
            try:
                params = {
                    "limit": min(limit, 100),
                    "summary_length": summary_length,
                    "agent_id": server._agent_id  # 使用当前 agent 的 ID
                }
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
        
        @self.mcp.tool()
        async def chat_get_message(message_id: str) -> Dict[str, Any]:
            """
            Get full content of a specific chat message by ID.
            
            Use this after chat_history to get complete message content.
            
            Args:
                message_id: The message ID from chat_history
            
            Returns:
                Dictionary with full message content
            """
            try:
                async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                    response = await client.get(
                        f"{GATEWAY_URL}/api/chat/message/{message_id}",
                        params={"agent_id": server._agent_id}  # 使用当前 agent 的 ID
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                return {"success": False, "error": str(e)}
        
        logger.info(f"[{self.name}] Registered 6 tools for agent: {server._agent_id}")
