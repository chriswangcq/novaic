"""
Executor Handler

Handles task execution for the Worker acting as an Executor.
Implements idempotent MCP tool calls and reply sending.

v11: Worker 直接和 MCP Server 通信，不经过 Gateway API
- MCP Server 地址从 agent 配置获取
- 幂等性通过 Gateway API 检查
- 结果通过 Gateway API 提交

v2.9: 使用 MCPServerConnection 管理 MCP session
- 复用 executor/mcp_client.py 的 session 管理逻辑
- 自动 initialize 和 session 恢复
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

import aiohttp

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MCPServerConnection for session management
from executor.mcp_client import MCPServerConnection

# ==================== Constants ====================

MCP_CALL_TIMEOUT = 300.0  # 5 minutes for MCP tool execution

# ==================== MCP Connection Pool ====================
# Cache MCP connections by URL for session reuse
_mcp_connections: Dict[str, MCPServerConnection] = {}


def _get_mcp_connection(url: str) -> MCPServerConnection:
    """Get or create an MCP connection for a URL."""
    if url not in _mcp_connections:
        # Parse name from URL for logging
        name = url.split("/")[-1] or "mcp"
        _mcp_connections[url] = MCPServerConnection(name=name, url=url)
    return _mcp_connections[url]


# ==================== MCP Direct Communication ====================

async def get_mcp_server_url(
    gateway_url: str,
    session: aiohttp.ClientSession,
    agent_id: str,
) -> Optional[str]:
    """
    Get MCP server URL for an agent from Gateway.
    
    Args:
        gateway_url: Gateway URL
        session: HTTP session
        agent_id: Agent ID
    
    Returns:
        MCP server URL (e.g., http://localhost:19900)
    """
    try:
        async with session.get(f"{gateway_url}/api/agents/{agent_id}") as response:
            if response.status == 200:
                agent = await response.json()
                # Get port configuration
                ports = agent.get("ports", {})
                # vm.ports.mcp is the MCP port
                if isinstance(ports, dict):
                    mcp_port = ports.get("mcp")
                    if mcp_port:
                        return f"http://localhost:{mcp_port}"
                
                # Try vm.ports format
                vm = agent.get("vm", {})
                if isinstance(vm, dict):
                    vm_ports = vm.get("ports", {})
                    if isinstance(vm_ports, dict):
                        mcp_port = vm_ports.get("mcp")
                        if mcp_port:
                            return f"http://localhost:{mcp_port}"
                
                # Fallback: use agent index to calculate port
                agent_index = vm.get("agent_index", 0) if isinstance(vm, dict) else 0
                # Default MCP port base is 19900
                return f"http://localhost:{19900 + agent_index}"
                
    except Exception as e:
        print(f"[Executor] Get MCP URL error: {e}")
    
    return None


async def call_mcp_server_direct(
    mcp_url: str,
    session: aiohttp.ClientSession,  # Kept for API compatibility, not used
    tool_name: str,
    args: Dict[str, Any],
    mcp_session_id: Optional[str] = None,  # Reuse existing session from LLMCaller
) -> Dict[str, Any]:
    """
    Call MCP tool directly on MCP server via JSON-RPC.
    
    v2.9: Uses MCPServerConnection for proper session management.
    Automatically handles:
    - MCP initialize handshake
    - mcp-session-id header management
    - Session recovery on errors
    - SSE response parsing
    
    Args:
        mcp_url: Full MCP server URL (e.g., http://127.0.0.1:19999/mcp/aggregate/main-xxx)
        session: HTTP session (not used, kept for API compatibility)
        tool_name: Tool name
        args: Tool arguments
        mcp_session_id: Existing MCP session ID to reuse (from LLMCaller)
    
    Returns:
        {"success": bool, "result": Any, "error": str}
    """
    try:
        # Get or create MCP connection with session management
        conn = _get_mcp_connection(mcp_url)
        
        # If we have an existing session ID from LLMCaller, use it
        if mcp_session_id and not conn._session_id:
            conn._session_id = mcp_session_id
            print(f"[Executor] Reusing MCP session from LLMCaller: {mcp_session_id[:20]}...")
        
        # Call tool using MCPServerConnection (handles session, retries, etc.)
        result = await conn.call_tool(tool_name, args, max_retries=3)
        
        return result
        
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "MCP call timed out",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"MCP call error: {str(e)}",
        }


# ==================== Idempotency (via Gateway) ====================

async def check_idempotency(
    gateway_url: str,
    session: aiohttp.ClientSession,
    idempotency_key: str,
) -> Optional[Dict[str, Any]]:
    """
    Check if this execution has already completed.
    
    Args:
        gateway_url: Gateway URL
        session: HTTP session
        idempotency_key: The idempotency key to check
    
    Returns:
        Existing result if found, None if should proceed
    """
    if not idempotency_key:
        return None
    
    try:
        async with session.get(
            f"{gateway_url}/api/mcp/execution/{idempotency_key}",
        ) as response:
            if response.status == 200:
                result = await response.json()
                status = result.get("status")
                
                if status == "done":
                    print(f"[Executor] Idempotency hit: {idempotency_key} already done")
                    return result.get("result")
                
                if status == "failed":
                    print(f"[Executor] Previous execution failed, retrying")
                    return None
                
                if status == "executing":
                    print(f"[Executor] Another executor is running {idempotency_key}")
                    await asyncio.sleep(1.0)
                    return await check_idempotency(gateway_url, session, idempotency_key)
            
            return None
            
    except Exception as e:
        print(f"[Executor] Idempotency check error: {e}")
        return None


async def register_execution(
    gateway_url: str,
    session: aiohttp.ClientSession,
    task: Dict[str, Any],
):
    """Register this execution for idempotency tracking."""
    idempotency_key = task.get("idempotency_key")
    if not idempotency_key:
        return
    
    try:
        await session.post(
            f"{gateway_url}/api/mcp/execution",
            json={
                "idempotency_key": idempotency_key,
                "agent_id": task.get("agent_id", "unknown"),
                "subagent_id": task.get("subagent_id", "unknown"),
                "round_id": task.get("round_id", "unknown"),
                "mcpcall_id": task.get("mcpcall_id", "unknown"),
                "tool_name": task.get("action") or task.get("type", "unknown"),
                "args": task.get("args", {}),
            },
        )
    except Exception as e:
        print(f"[Executor] Register execution error: {e}")


async def complete_execution(
    gateway_url: str,
    session: aiohttp.ClientSession,
    idempotency_key: str,
    result: Any,
):
    """Mark execution as complete."""
    if not idempotency_key:
        return
    
    try:
        await session.post(
            f"{gateway_url}/api/mcp/execution/{idempotency_key}/complete",
            json=result if isinstance(result, dict) else {"result": result},
        )
    except Exception as e:
        print(f"[Executor] Complete execution error: {e}")


async def fail_execution(
    gateway_url: str,
    session: aiohttp.ClientSession,
    idempotency_key: str,
    error: str,
):
    """Mark execution as failed."""
    if not idempotency_key:
        return
    
    try:
        await session.post(
            f"{gateway_url}/api/mcp/execution/{idempotency_key}/fail",
            params={"error": error},
        )
    except Exception as e:
        print(f"[Executor] Fail execution error: {e}")

# ==================== Task Handlers ====================
# v2.8: 所有操作都走 MCP 工具，不再有特殊的 reply 处理

def _get_mcp_url_for_tool(
    tool_name: str,
    agent_id: str,
    subagent_id: str,
    mcp_gateway_url: str,
) -> str:
    """
    Get the MCP server URL for a specific tool.
    
    v3.0: All tools go through Aggregate MCP for unified parameter handling.
    The Aggregate MCP wraps all tools with `args: Dict` parameter format,
    so we must use it consistently instead of routing to underlying MCPs directly.
    
    Args:
        tool_name: Tool name (unused, kept for API compatibility)
        agent_id: Agent ID (unused, kept for API compatibility)
        subagent_id: Runtime ID for aggregate MCP
        mcp_gateway_url: MCP Gateway base URL
    
    Returns:
        None - let caller use task_mcp_url (aggregate MCP) from scheduler
    """
    # v3.0: Always return None to use aggregate MCP from task_mcp_url
    # This ensures parameter format consistency:
    # - LLMCaller loads tools from aggregate MCP (with args: Dict wrapper)
    # - LLM generates calls with {"args": {...}} format
    # - Executor calls aggregate MCP which unwraps and forwards to underlying MCP
    return None


async def handle_tool_call(
    task: Dict[str, Any],
    gateway_url: str = "http://localhost:9527",
    mcp_gateway_url: str = None,
) -> Any:
    """
    Handle a tool_call task (Executor role).
    
    v2.6: Routes to different MCP servers based on tool type:
    - runtime_* → /mcp/runtime/{subagent_id}/ (Runtime layer)
    - memory_*, local_*, chat_* → /mcp/{server}/ (Shared layer)
    - Others → VM MCP server or fallback
    
    Args:
        task: Task data with tool name and arguments
        gateway_url: Backend URL (for idempotency, API calls)
        mcp_gateway_url: MCP Gateway URL when MCP runs in separate process (default gateway_url)
    
    Returns:
        Tool execution result
    """
    if mcp_gateway_url is None:
        mcp_gateway_url = gateway_url
    task_id = task.get("id")
    agent_id = task.get("agent_id")
    subagent_id = task.get("subagent_id", "")
    tool_name = task.get("action")
    task_args = task.get("args", {})
    idempotency_key = task.get("idempotency_key")
    
    # Parse task args (may be JSON string)
    if isinstance(task_args, str):
        task_args = json.loads(task_args)
    
    # Get tool arguments, MCP URL and session ID from task args
    tool_args = task_args.get("tool_args", task_args)  # Fallback for legacy format
    task_mcp_url = task_args.get("mcp_url")  # MCP URL from runtime record
    mcp_session_id = task_args.get("mcp_session_id")  # Session ID from LLMCaller
    
    print(f"[Executor] Executing tool_call: {tool_name} (task: {task_id}, runtime: {subagent_id})")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Check idempotency
            cached = await check_idempotency(gateway_url, session, idempotency_key)
            if cached is not None:
                print(f"[Executor] Returning cached result for {idempotency_key}")
                return cached
            
            # 2. Register this execution
            await register_execution(gateway_url, session, task)
            
            # 3. v2.9: Get MCP server URL
            # First check if tool belongs to shared layer (chat, memory, local, etc.)
            shared_url = _get_mcp_url_for_tool(tool_name, agent_id, subagent_id, mcp_gateway_url)
            
            if shared_url:
                mcp_url = shared_url
            elif task_mcp_url:
                # task_mcp_url may be full URL (from MCP Gateway) or path (legacy)
                if task_mcp_url.startswith("http://") or task_mcp_url.startswith("https://"):
                    mcp_url = task_mcp_url
                else:
                    mcp_url = f"{mcp_gateway_url.rstrip('/')}{task_mcp_url}" if task_mcp_url.startswith("/") else f"{mcp_gateway_url.rstrip('/')}/{task_mcp_url}"
            else:
                mcp_url = None
            
            if not mcp_url:
                # Final fallback to VM MCP server (or agent's MCP port)
                mcp_url = await get_mcp_server_url(gateway_url, session, agent_id)
            
            if not mcp_url:
                error = f"Cannot get MCP server URL for tool {tool_name}"
                await fail_execution(gateway_url, session, idempotency_key, error)
                return {"success": False, "error": error}
            
            print(f"[Executor] Calling MCP server at {mcp_url} for {tool_name}")
            
            # 4. Call MCP server directly (with session ID from LLMCaller if available)
            result = await call_mcp_server_direct(mcp_url, session, tool_name, tool_args, mcp_session_id)
            
            # 5. Update execution record
            if result.get("success"):
                await complete_execution(gateway_url, session, idempotency_key, result)
            else:
                await fail_execution(gateway_url, session, idempotency_key, result.get("error", "Unknown error"))
            
            # 6. Broadcast tool completion log
            await _broadcast_log(gateway_url, session, agent_id, {
                "type": "tool_end",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "result": _summarize_result(result),
                },
            })
            
            print(f"[Executor] Tool {tool_name} completed: success={result.get('success')}")
            return result
            
        except Exception as e:
            error = str(e)
            print(f"[Executor] Tool call error: {error}")
            import traceback
            traceback.print_exc()
            
            # Broadcast error log
            await _broadcast_log(gateway_url, session, agent_id, {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "tool": tool_name,
                    "error": error[:200],
                },
            })
            
            await fail_execution(gateway_url, session, idempotency_key, error)
            return {"success": False, "error": error}


# v2.8: handle_reply 已移除 - 所有 reply 通过 chat_reply MCP 工具处理
# handle_subagent removed in v2.5
# SubAgents are now created via runtime_spawn MCP tool, which uses Master API
# See mcp_servers/runtime.py runtime_spawn()


# ==================== Logging Helpers ====================

async def _broadcast_log(
    gateway_url: str,
    session: aiohttp.ClientSession,
    agent_id: str,
    log_data: Dict[str, Any],
):
    """Broadcast execution log to Gateway for UI display."""
    try:
        await session.post(
            f"{gateway_url}/api/logs/broadcast",
            json={
                "agent_id": agent_id,
                **log_data,
            },
        )
    except Exception:
        pass  # Non-critical


def _summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize MCP result for display (truncate long content)."""
    summary = {}
    
    if result.get("success") is not None:
        summary["success"] = result["success"]
    
    if result.get("error"):
        summary["error"] = str(result["error"])[:100]
        return summary
    
    # Extract useful info from result
    inner = result.get("result", result)
    
    if isinstance(inner, dict):
        # Common fields to include
        for key in ["message", "url", "output", "content", "status", "id", "success"]:
            if key in inner:
                val = inner[key]
                if isinstance(val, str) and len(val) > 100:
                    summary[key] = val[:100] + "..."
                else:
                    summary[key] = val
        
        # If nothing found, show first few keys
        if not summary:
            for key in list(inner.keys())[:3]:
                val = inner[key]
                if isinstance(val, str) and len(val) > 50:
                    summary[key] = val[:50] + "..."
                elif isinstance(val, (dict, list)):
                    summary[key] = f"({type(val).__name__})"
                else:
                    summary[key] = val
    elif isinstance(inner, str):
        summary["output"] = inner[:100] + "..." if len(inner) > 100 else inner
    
    return summary if summary else {"done": True}


# ==================== Module Exports ====================

__all__ = [
    "handle_tool_call",
]
