"""
RuntimeMCP - Runtime 管理 MCP Server

v2.8: 重命名自 SingleAgentRuntimeMCPServer

管理 Agent 内部的多个 Runtime（main, subagent 等）。
提供 runtime_* 工具。
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


class RuntimeMCP(BaseMCPServer):
    """
    RuntimeMCP - Runtime 管理 MCP Server。
    
    管理 Agent 内部的多个 Runtime（执行环境）：
    - main-xxx: 主 Agent Runtime（处理用户消息）
    - sub-xxx: SubAgent Runtime（处理子任务）
    
    提供工具：
    - runtime_list: 列出所有活跃 Runtime
    - runtime_history: 获取 Runtime 消息历史
    - runtime_send: 向 Runtime 发消息
    - runtime_rest: 进入休息状态 (仅 Main Runtime)
    - runtime_spawn: 同步创建子代理
    """
    
    name = "runtime"
    description = "Runtime 管理，管理 Agent 内部多个执行环境"
    
    def __init__(
        self, 
        agent_id: Optional[str] = None, 
        agent_index: int = 0,
        subagent_id: Optional[str] = None,
    ):
        """
        初始化 RuntimeMCP Server。
        
        Args:
            agent_id: Agent ID，用于标识当前 agent (必填)
            agent_index: Agent index，用于端口分配
            subagent_id: Current runtime's subagent_id
        """
        if not agent_id:
            raise ValueError("[RuntimeMCP] agent_id is required")
        self._agent_id = agent_id
        self._subagent_id = subagent_id
        super().__init__(agent_id=agent_id, agent_index=agent_index)
        logger.info(f"[RuntimeMCP] Initialized for agent: {self._agent_id}, subagent: {self._subagent_id}")
    
    def _build_instructions(self) -> str:
        return """RuntimeMCP - Runtime 管理和调度

## 概念

Agent 内部可以有多个 Runtime（执行环境）：
- `main-xxx`: 主 Agent Runtime（处理用户消息）
- `sub-xxx`: SubAgent Runtime（处理子任务）

## 工具列表

| 工具 | 用途 | 可用者 |
|------|------|--------|
| runtime_list | 列出所有活跃 Runtime | Main + SubAgent |
| runtime_history | 获取 Runtime 消息历史 | Main + SubAgent |
| runtime_send | 向 Runtime 发送消息 | Main + SubAgent |
| runtime_rest | 进入休息状态 | **仅 Main Runtime** |
| runtime_spawn | 同步创建子代理 | Main + SubAgent |

## 使用场景

- **runtime_rest**: 等待用户输入时进入休息状态（仅 Main 可用）
- **runtime_spawn**: 同步委托复杂任务给子代理，阻塞等待结果
- **异步执行**: 使用 task_async(tool="runtime_spawn", ...) 进行异步执行

## 注意

- inbox 消息会在每轮思考前自动注入到 context，无需手动检查
- SubAgent 完成任务后会自动销毁，不能调用 runtime_rest
"""
    
    def _register_tools(self) -> None:
        """注册所有 Runtime 工具。"""
        server = self  # Capture for closures
        
        @self.mcp.tool()
        async def runtime_list() -> Dict[str, Any]:
            """
            List all active runtimes in this agent.
            
            Runtimes represent independent execution environments:
            - main-xxx: Primary runtime (handles user messages)
            - sub-xxx: SubAgent runtimes (handles delegated tasks)
            
            Returns:
                Dictionary with:
                - runtimes: List of runtime info with:
                    - runtime_id: Identifier (e.g., "main-xxx", "sub-xxx")
                    - type: Runtime type (main, subagent)
                    - status: Current status (active, idle, completed)
                    - message_count: Number of messages in history
                    - parent: Parent runtime ID (for sub-agents)
                    - created_at: Creation timestamp
                    - last_activity: Last activity timestamp
            
            Examples:
                runtime_list()
            """
            try:
                result = await _call_gateway("/sessions")
                if "sessions" in result:
                    result["runtimes"] = result.pop("sessions")
                    for rt in result.get("runtimes", []):
                        if "session_key" in rt:
                            rt["runtime_id"] = rt.pop("session_key")
                return result
            except httpx.HTTPError as e:
                return {"error": str(e), "runtimes": []}
        
        @self.mcp.tool()
        async def runtime_history(
            runtime_id: str,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0
        ) -> Dict[str, Any]:
            """
            Get message history for a specific runtime.
            
            Use this to see what a sub-agent has been thinking and doing,
            or to review the main conversation history.
            
            Args:
                runtime_id: The runtime to get history for (e.g., "main-xxx", "sub-xxx")
                limit: Maximum number of messages to return (default: 50)
                offset: Number of messages to skip from the start (default: 0)
            
            Returns:
                Dictionary with:
                - runtime_id: The queried runtime
                - messages: List of messages with role, content, timestamp, tool_calls
                - total: Total message count
            """
            try:
                result = await _call_gateway(
                    f"/sessions/{runtime_id}/history",
                    method="POST",
                    data={"limit": limit, "offset": offset}
                )
                result["runtime_id"] = runtime_id
                return result
            except httpx.HTTPError as e:
                return {"error": str(e), "runtime_id": runtime_id, "messages": []}
        
        @self.mcp.tool()
        async def runtime_send(
            runtime_id: str,
            message: str,
            wait_response: Optional[bool] = False,
            timeout: Optional[int] = 60
        ) -> Dict[str, Any]:
            """
            Send a message to another runtime.
            
            Use this to communicate between runtimes or inject messages.
            
            Args:
                runtime_id: Target runtime ID
                message: Message content to send
                wait_response: If True, wait for the runtime to process and respond
                timeout: Timeout in seconds when wait_response is True (default: 60)
            
            Returns:
                Dictionary with success, runtime_id, response (if wait_response), queued
            """
            try:
                result = await _call_gateway(
                    f"/sessions/{runtime_id}/send",
                    method="POST",
                    data={
                        "message": message,
                        "wait_response": wait_response,
                        "timeout": timeout
                    }
                )
                result["runtime_id"] = runtime_id
                return result
            except httpx.HTTPError as e:
                return {"error": str(e), "success": False, "runtime_id": runtime_id}
        
        @self.mcp.tool()
        async def runtime_rest(
            reason: str,
            wake_triggers: Optional[List[Dict[str, Any]]] = None,
            handoff_notes: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Voluntarily enter rest state and set wake-up conditions.
            
            **IMPORTANT: Only Main Runtime can call this. SubAgents should
            complete their task and return, not rest.**
            
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
                # Check if this is a SubAgent (not allowed to rest)
                # v14: Use subagent_id to check type, runtime_id for API
                subagent_id = server._subagent_id  # This is actually the runtime_id in v14
                if subagent_id and subagent_id.startswith("sub-"):
                    return {
                        "success": False,
                        "error": "SubAgents cannot rest. Complete your task and return the result instead."
                    }
                
                # v14: Use runtime_id for the API call
                # The internal API now handles updating both Runtime and SubAgent state
                runtime_id = subagent_id  # In v14, this is the runtime_id (rt-xxx)
                async with httpx.AsyncClient(timeout=30.0, trust_env=False) as client:
                    response = await client.post(
                        f"{GATEWAY_URL}/internal/runtimes/{runtime_id}/rest",
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
        async def runtime_spawn(
            task: str,
            share_context: bool = False,
            timeout_minutes: int = 30,
        ) -> Dict[str, Any]:
            """
            Spawn a SubAgent to execute a task synchronously.
            
            This creates a new SubAgent Runtime, waits for it to complete,
            and returns the result. The SubAgent is automatically destroyed
            after completion.
            
            Use this for tasks requiring multi-step reasoning or research.
            For async execution, use task_async(tool="runtime_spawn", args={...})
            
            Args:
                task: Task description for the SubAgent (be specific and clear)
                share_context: If True, copy current context to SubAgent
                timeout_minutes: Maximum execution time (default: 30)
            
            Returns:
                Dictionary with:
                - success: Whether task completed successfully
                - result: SubAgent's final response
                - duration_seconds: Execution time
                - error: Error message (if failed)
            
            Examples:
                runtime_spawn(task="研究 React 和 Vue 的性能差异，写一份对比报告")
                runtime_spawn(task="分析登录页面卡死的 bug", share_context=True)
            """
            try:
                # Get Master instance
                from master import get_master
                master = get_master()
                if not master:
                    return {"success": False, "error": "Master not available"}
                
                # Check if we have parent subagent_id
                parent_subagent_id = server._subagent_id
                if not parent_subagent_id:
                    # Try to get main runtime
                    main_runtime = await master.runtime_repo.get_main_runtime(server._agent_id)
                    if main_runtime:
                        parent_subagent_id = main_runtime.subagent_id
                    else:
                        return {"success": False, "error": "No active runtime found"}
                
                logger.info(f"[runtime_spawn] Creating SubAgent for task: {task[:50]}...")
                
                # Create SubAgent Runtime via Master
                runtime = await master.create_sub_runtime(
                    agent_id=server._agent_id,
                    parent_subagent_id=parent_subagent_id,
                    initial_task=task,
                    share_context=share_context,
                )
                
                # Wait for SubAgent to complete (Master drives the ReACT loop)
                result = await master.wait_runtime_complete(
                    subagent_id=runtime.subagent_id,
                    timeout_seconds=timeout_minutes * 60,
                )
                
                logger.info(f"[runtime_spawn] SubAgent {runtime.subagent_id} completed: success={result.get('success')}")
                return result
                
            except Exception as e:
                logger.error(f"[RuntimeMCP] runtime_spawn failed: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "error": str(e)}
        
        logger.info(f"[{self.name}] Registered 5 tools for agent: {server._agent_id}")
