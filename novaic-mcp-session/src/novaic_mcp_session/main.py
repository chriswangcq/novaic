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
    instructions="""NovAIC Session Manager - 会话与子代理管理

6 个工具用于管理会话和并行任务。

## 核心概念

- **Session（会话）**: 独立的执行上下文，包含自己的消息历史
- **SubAgent（子代理）**: 在独立会话中执行的并行任务

## 工具一览

| 工具 | 用途 |
|------|------|
| sessions_list | 查看所有活跃会话 |
| sessions_history | 获取会话消息历史 |
| sessions_send | 向指定会话发送消息 |
| sessions_spawn | **启动子代理执行并行任务** |
| sessions_status | 检查子代理状态 |
| sessions_cancel | 取消运行中的子代理 |

## 使用场景

### 1. 并行任务
当有多个独立任务时，使用 sessions_spawn 并行执行：
```
sessions_spawn(task="搜索 Python 教程", context="找到后总结要点")
sessions_spawn(task="查看项目目录结构", context="分析代码组织")
```

### 2. 长时间任务
对于耗时任务，spawn 后不等待（wait=False），继续其他工作：
```
sessions_spawn(task="执行完整测试套件", timeout_minutes=60, wait=False)
```

### 3. 会话间通信
向其他会话发送消息或查询其历史：
```
sessions_send(session_key="main", message="子任务完成")
sessions_history(session_key="subagent:task_123", limit=10)
```

## 最佳实践

- 并行任务数建议 ≤ 3，避免资源竞争
- 长任务设置合理的 timeout_minutes
- 使用 sessions_status 定期检查子代理进度
- announce=True 让子代理完成后自动通知主会话
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
