"""
Agent Context MCP Server - Agent 上下文和自我管理

提供 Agent 上下文管理、子代理调用、收件箱检查等功能。
"""

import os
import asyncio
import logging
import httpx
from typing import Optional, List, Dict, Any

from .base import BaseMCPServer

logger = logging.getLogger(__name__)

# Gateway URL for internal API calls
GATEWAY_URL = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")


async def _call_gateway(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Call the gateway internal API."""
    async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
        url = f"{GATEWAY_URL}/api/internal{endpoint}"
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=data or {})
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()


class AgentContextMCPServer(BaseMCPServer):
    """
    Agent Context MCP Server。
    
    提供工具：
    - agent_context_list: 列出所有上下文
    - agent_context_history: 获取上下文历史
    - agent_context_send: 发送消息到上下文
    - agent_inbox: 检查收件箱
    - agent_rest: 进入休息状态
    - agent_call: 调用子代理
    """
    
    name = "agent-context"
    description = "Agent 上下文管理和自我调度工具"
    
    def _build_instructions(self) -> str:
        return """Agent Context MCP - 上下文管理和自我调度

## 工具列表

| 工具 | 用途 |
|------|------|
| agent_context_list | 列出所有活跃上下文 |
| agent_context_history | 获取上下文消息历史 |
| agent_context_send | 向上下文发送消息 |
| agent_inbox | 检查待处理事件 |
| agent_rest | 进入休息状态 |
| agent_call | 委托子代理执行任务 |

## 使用场景

- **agent_inbox**: 长时间任务中定期检查是否有紧急事件
- **agent_rest**: 等待用户输入时进入休息状态
- **agent_call**: 委托复杂任务给子代理
"""
    
    def _register_tools(self) -> None:
        """注册所有 Agent Context 工具。"""
        
        @self.mcp.tool()
        async def agent_context_list() -> Dict[str, Any]:
            """
            List all active agent contexts.
            
            Contexts represent independent conversation environments:
            - main: Primary conversation with user
            - subagent:xxx / task:xxx: Sub-agent or task conversations
            
            Returns:
                Dictionary with:
                - contexts: List of context info with:
                    - context_key: Identifier (e.g., "main", "task:abc123")
                    - type: Context type (main, subagent, task)
                    - status: Current status (active, idle, completed)
                    - message_count: Number of messages in history
                    - parent: Parent context key (for sub-agents)
                    - created_at: Creation timestamp
                    - last_activity: Last activity timestamp
            
            Examples:
                agent_context_list()
            """
            try:
                result = await _call_gateway("/sessions")
                if "sessions" in result:
                    result["contexts"] = result.pop("sessions")
                    for ctx in result.get("contexts", []):
                        if "session_key" in ctx:
                            ctx["context_key"] = ctx.pop("session_key")
                return result
            except httpx.HTTPError as e:
                return {"error": str(e), "contexts": []}
        
        @self.mcp.tool()
        async def agent_context_history(
            context_key: str,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0
        ) -> Dict[str, Any]:
            """
            Get message history for a specific context.
            
            Use this to see what a sub-agent has been thinking and doing,
            or to review the main conversation history.
            
            Args:
                context_key: The context to get history for (e.g., "main", "task:abc123")
                limit: Maximum number of messages to return (default: 50)
                offset: Number of messages to skip from the start (default: 0)
            
            Returns:
                Dictionary with:
                - context_key: The queried context
                - messages: List of messages with role, content, timestamp, tool_calls
                - total: Total message count
            """
            try:
                result = await _call_gateway(
                    f"/sessions/{context_key}/history",
                    method="POST",
                    data={"limit": limit, "offset": offset}
                )
                result["context_key"] = context_key
                return result
            except httpx.HTTPError as e:
                return {"error": str(e), "context_key": context_key, "messages": []}
        
        @self.mcp.tool()
        async def agent_context_send(
            context_key: str,
            message: str,
            wait_response: Optional[bool] = False,
            timeout: Optional[int] = 60
        ) -> Dict[str, Any]:
            """
            Send a message to another context.
            
            Use this to communicate between contexts or inject messages.
            
            Args:
                context_key: Target context key
                message: Message content to send
                wait_response: If True, wait for the context to process and respond
                timeout: Timeout in seconds when wait_response is True (default: 60)
            
            Returns:
                Dictionary with success, context_key, response (if wait_response), queued
            """
            try:
                result = await _call_gateway(
                    f"/sessions/{context_key}/send",
                    method="POST",
                    data={
                        "message": message,
                        "wait_response": wait_response,
                        "timeout": timeout
                    }
                )
                result["context_key"] = context_key
                return result
            except httpx.HTTPError as e:
                return {"error": str(e), "success": False, "context_key": context_key}
        
        @self.mcp.tool()
        async def agent_inbox() -> Dict[str, Any]:
            """
            Check the inbox for pending events and messages.
            
            Use this to stay aware of new events during long-running tasks.
            Call periodically (every 3-5 iterations) to check if there are
            urgent matters that need attention.
            
            Returns:
                Dictionary with:
                - pending_count: Number of pending events
                - events: List of pending events with summaries
                - has_urgent: Whether any event is marked urgent
                - oldest_age_seconds: Age of oldest pending event
                - recommendation: Suggested action ("continue", "check_urgent", "process_all")
            """
            try:
                async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                    response = await client.get(f"{GATEWAY_URL}/api/agent/inbox")
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                return {"error": str(e), "pending_count": 0, "events": []}
        
        @self.mcp.tool()
        async def agent_rest(
            reason: str,
            wake_triggers: Optional[List[Dict[str, Any]]] = None,
            handoff_notes: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Voluntarily enter rest state and set wake-up conditions.
            
            Use this when:
            - Waiting for user input or confirmation
            - Waiting for a specific time
            - No more tasks to process
            - Current task requires external action
            
            Args:
                reason: Why you are resting (displayed to user)
                wake_triggers: List of conditions that will wake you up:
                    - {"type": "user_response"} - Wake when user sends any message
                    - {"type": "cron", "expr": "*/10 * * * *"} - Wake on schedule
                    - {"type": "keyword", "pattern": "urgent|紧急"} - Wake on keyword
                    - {"type": "timeout", "minutes": 30} - Wake after timeout
                handoff_notes: Notes about current state for when you wake up
            
            Returns:
                Dictionary with success, state, triggers_set, estimated_wake, handoff_notes
            """
            try:
                async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                    response = await client.post(
                        f"{GATEWAY_URL}/api/agent/rest",
                        json={
                            "reason": reason,
                            "wake_triggers": wake_triggers or [{"type": "user_response"}],
                            "handoff_notes": handoff_notes
                        }
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPError as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def agent_call(
            task: str,
            model: Optional[str] = None,
            context: Optional[str] = None,
            timeout_minutes: int = 30,
        ) -> Dict[str, Any]:
            """
            Synchronously call a sub-agent to execute a complex task.
            
            The sub-agent will run independently and return results when complete.
            Use this for tasks requiring multi-step reasoning or research.
            
            Args:
                task: Task description for the sub-agent (be specific and clear)
                model: LLM model to use (default: inherit from parent agent)
                context: Additional context or background information
                timeout_minutes: Maximum execution time (default: 30)
            
            Returns:
                Dictionary with:
                - success: Whether task completed successfully
                - task_id: Task ID for reference
                - result: Sub-agent's final response
                - duration_seconds: Execution time
                - error: Error message (if failed)
            
            Examples:
                agent_call(task="研究 React 和 Vue 的性能差异，写一份对比报告")
                agent_call(task="分析这个 bug", context="登录页面偶尔卡死", model="claude-sonnet-4")
            """
            try:
                from core.task_manager import get_task_manager
                task_manager = get_task_manager()
                if not task_manager:
                    return {"success": False, "error": "TaskManager not available"}
                
                # Create agent task and wait for completion
                result = await task_manager.spawn(
                    task_type="agent",
                    config={
                        "prompt": task,
                        "model": model,
                        "context": context,
                    },
                    label=task[:50] if task else "Sub-agent task",
                    timeout_seconds=timeout_minutes * 60,
                )
                
                if not result.get("success"):
                    return result
                
                task_id = result.get("task_id")
                
                # Wait for task completion
                max_wait = timeout_minutes * 60
                waited = 0
                poll_interval = 2
                
                while waited < max_wait:
                    status = await task_manager.get_status(task_id=task_id)
                    task_status = status.get("status")
                    
                    if task_status in ("completed", "failed", "cancelled"):
                        return {
                            "success": task_status == "completed",
                            "task_id": task_id,
                            "result": status.get("result"),
                            "error": status.get("error"),
                            "duration_seconds": status.get("duration_seconds"),
                        }
                    
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval
                    # Increase poll interval over time
                    if waited > 60:
                        poll_interval = 5
                    if waited > 300:
                        poll_interval = 10
                
                # Timeout
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": f"Task timed out after {timeout_minutes} minutes",
                }
                
            except Exception as e:
                logger.error(f"[AgentContextMCP] agent_call failed: {e}")
                return {"success": False, "error": str(e)}
        
        logger.info(f"[{self.name}] Registered 6 tools")
