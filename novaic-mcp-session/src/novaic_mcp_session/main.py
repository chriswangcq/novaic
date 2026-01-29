"""
NovAIC MCP Server for Session Management Tools.

Provides tools for managing agent sessions, including:
- sessions_list: List all active sessions
- sessions_history: Get session message history
- sessions_send: Send message to another session
- sessions_spawn: Spawn a sub-agent task
- sessions_cancel: Cancel a running sub-agent
- sessions_status: Get sub-agent status
"""

import os
import httpx
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP

# Gateway API endpoint (configurable via environment)
GATEWAY_URL = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:8000")

mcp = FastMCP(
    name="novaic-session",
    instructions="""NovAIC Session Manager - 会话、子代理与自主调度

8 个工具用于管理会话、并行任务和 Agent 自主调度。

## 核心概念

- **Session（会话）**: 独立的执行上下文，包含自己的消息历史
- **SubAgent（子代理）**: 在独立会话中执行的并行任务
- **Inbox（收件箱）**: 待处理的事件队列
- **自主调度**: Agent 可以主动休息并设置唤醒条件

## 工具一览

### 自主调度工具 (重要!)
| 工具 | 用途 |
|------|------|
| **inbox_check** | 查看待处理事件，了解是否有新消息/紧急事件 |
| **agent_rest** | 主动休息并设置唤醒条件 |

### 会话管理工具
| 工具 | 用途 |
|------|------|
| sessions_list | 查看所有活跃会话 |
| sessions_history | 获取会话消息历史 |
| sessions_send | 向指定会话发送消息 |
| sessions_spawn | 启动子代理执行并行任务 |
| sessions_status | 检查子代理状态 |
| sessions_cancel | 取消运行中的子代理 |

## 自主调度指南

### 何时检查收件箱
- 长时间任务执行过程中，定期检查是否有紧急事件
- 当前任务遇到等待时（如等待网页加载）
- 每完成一个子任务后

### 何时主动休息
- 当前任务需要等待外部输入（如用户确认）
- 需要等待某个时间点（如等待会议开始）
- 任务已完成，没有更多待办事项

### inbox_check 使用示例
```python
inbox_check()  # 返回待处理事件列表
# 如果有紧急事件，可以选择：
# 1. 中断当前任务处理紧急事件
# 2. 继续当前任务，稍后处理
```

### agent_rest 使用示例
```python
agent_rest(
    reason="等待用户确认方案",
    wake_triggers=[
        {"type": "user_response"},           # 用户回复时唤醒
        {"type": "cron", "expr": "*/10 * * * *"},  # 每10分钟检查
        {"type": "keyword", "pattern": "紧急"}     # 包含"紧急"时唤醒
    ],
    handoff_notes="已提交方案 A/B，等待用户选择"
)
```

## 最佳实践

- 长任务执行中每 3-5 轮调用一次 inbox_check
- 遇到需要等待的情况，主动 agent_rest 而非空转
- rest 前通过 chat_reply 告知用户当前状态
- 设置合理的唤醒条件，避免无限休眠
"""
)


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


@mcp.tool()
async def inbox_check() -> Dict[str, Any]:
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
    
    Examples:
        inbox_check()
        # Returns: {"pending_count": 2, "has_urgent": true, ...}
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
            response = await client.get(f"{GATEWAY_URL}/api/agent/inbox")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e), "pending_count": 0, "events": []}


@mcp.tool()
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
            - {"type": "user_message", "pattern": "..."} - Wake on matching message
            - {"type": "cron", "expr": "*/10 * * * *"} - Wake on schedule
            - {"type": "keyword", "pattern": "urgent|紧急"} - Wake on keyword
            - {"type": "timeout", "minutes": 30} - Wake after timeout
        handoff_notes: Notes about current state for when you wake up
    
    Returns:
        Dictionary with:
        - success: Whether rest was initiated
        - state: New agent state ("resting")
        - triggers_set: Number of wake triggers configured
        - estimated_wake: Estimated next wake time (if deterministic)
    
    Examples:
        # Rest until user responds
        agent_rest(
            reason="等待用户确认",
            wake_triggers=[{"type": "user_response"}],
            handoff_notes="已询问用户是否继续"
        )
        
        # Rest with timeout
        agent_rest(
            reason="等待部署完成",
            wake_triggers=[
                {"type": "timeout", "minutes": 10},
                {"type": "keyword", "pattern": "deployed|完成"}
            ],
            handoff_notes="部署脚本已启动"
        )
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


@mcp.tool()
async def sessions_list() -> Dict[str, Any]:
    """
    List all active sessions.
    
    Returns information about all sessions including:
    - session_id: Unique identifier
    - session_key: Human-readable key (e.g., "main", "subagent:task_123")
    - status: Current status (active, idle, completed)
    - created_at: Creation timestamp
    - message_count: Number of messages in history
    - parent_id: Parent session ID (for sub-agents)
    
    Returns:
        Dictionary with 'sessions' list containing session metadata.
    """
    try:
        result = await _call_gateway("/sessions")
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "sessions": []}


@mcp.tool()
async def sessions_history(
    session_key: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """
    Get message history for a specific session.
    
    Args:
        session_key: The session key to get history for (e.g., "main", "subagent:task_123")
        limit: Maximum number of messages to return (default: 50)
        offset: Number of messages to skip from the start (default: 0)
    
    Returns:
        Dictionary with 'messages' list containing message objects with:
        - role: 'user', 'assistant', or 'system'
        - content: Message content
        - timestamp: Message timestamp
        - tool_calls: Any tool calls made (for assistant messages)
    """
    try:
        result = await _call_gateway(
            f"/sessions/{session_key}/history",
            method="POST",
            data={"limit": limit, "offset": offset}
        )
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "messages": []}


@mcp.tool()
async def sessions_send(
    session_key: str,
    message: str,
    wait_response: Optional[bool] = False,
    timeout: Optional[int] = 60
) -> Dict[str, Any]:
    """
    Send a message to another session.
    
    Use this to communicate between sessions or inject messages into a session.
    
    Args:
        session_key: Target session key
        message: Message content to send
        wait_response: If True, wait for the session to process and respond (default: False)
        timeout: Timeout in seconds when wait_response is True (default: 60)
    
    Returns:
        Dictionary with:
        - success: Whether the message was sent successfully
        - response: The session's response (if wait_response=True)
        - message_id: ID of the sent message
    """
    try:
        result = await _call_gateway(
            f"/sessions/{session_key}/send",
            method="POST",
            data={
                "message": message,
                "wait_response": wait_response,
                "timeout": timeout
            }
        )
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "success": False}


@mcp.tool()
async def sessions_spawn(
    task: str,
    model: Optional[str] = None,
    timeout_minutes: Optional[int] = 30,
    announce: Optional[bool] = True,
    wait: Optional[bool] = False,
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Spawn a sub-agent to execute a task in a separate session.
    
    Sub-agents run independently and can execute long-running tasks in parallel.
    Use this for tasks that:
    - Take a long time to complete
    - Can run independently
    - Don't need immediate results
    
    Args:
        task: Description of the task for the sub-agent to execute
        model: LLM model to use (default: inherit from parent)
        timeout_minutes: Maximum execution time in minutes (default: 30)
        announce: If True, announce results to parent session when done (default: True)
        wait: If True, wait for completion and return result (default: False)
        context: Optional context/background information for the sub-agent
    
    Returns:
        Dictionary with:
        - subagent_id: Unique ID for the sub-agent
        - session_key: Session key for the sub-agent (e.g., "subagent:abc123")
        - status: 'running' or 'completed' (if wait=True)
        - result: Task result (if wait=True and completed)
    """
    try:
        result = await _call_gateway(
            "/sessions/spawn",
            method="POST",
            data={
                "task": task,
                "model": model,
                "timeout_minutes": timeout_minutes,
                "announce": announce,
                "wait": wait,
                "context": context
            }
        )
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "success": False}


@mcp.tool()
async def sessions_cancel(subagent_id: str) -> Dict[str, Any]:
    """
    Cancel a running sub-agent task.
    
    Args:
        subagent_id: The ID of the sub-agent to cancel
    
    Returns:
        Dictionary with:
        - success: Whether the cancellation was successful
        - status: Final status of the sub-agent
    """
    try:
        result = await _call_gateway(
            f"/sessions/subagent/{subagent_id}/cancel",
            method="POST"
        )
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "success": False}


@mcp.tool()
async def sessions_status(subagent_id: str) -> Dict[str, Any]:
    """
    Get the status of a sub-agent task.
    
    Args:
        subagent_id: The ID of the sub-agent to check
    
    Returns:
        Dictionary with:
        - subagent_id: The sub-agent ID
        - status: Current status ('running', 'completed', 'failed', 'cancelled')
        - progress: Optional progress information
        - result: Task result (if completed)
        - error: Error message (if failed)
        - duration_seconds: Execution time so far
    """
    try:
        result = await _call_gateway(
            f"/sessions/subagent/{subagent_id}/status"
        )
        return result
    except httpx.HTTPError as e:
        return {"error": str(e), "status": "unknown"}


def main():
    """Run the MCP server."""
    import sys
    
    # Default to streamable HTTP transport
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8081"))
    
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=host, port=port)
    elif transport == "stdio":
        mcp.run(transport="stdio")
    else:
        print(f"Unknown transport: {transport}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
