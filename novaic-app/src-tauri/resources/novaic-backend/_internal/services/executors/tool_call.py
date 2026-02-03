"""
ToolCallExecutor

Executes 'tool_call' tasks by calling MCP tools.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

import aiohttp

from ..executor_worker import BaseExecutor, ExecutorWorker
from executor.mcp_client import MCPServerConnection

if TYPE_CHECKING:
    from ..gateway_client import GatewayClient


# ==================== MCP Connection Pool ====================
_mcp_connections: Dict[str, MCPServerConnection] = {}


def _get_mcp_connection(url: str) -> MCPServerConnection:
    """Get or create an MCP connection for a URL."""
    if url not in _mcp_connections:
        name = url.split("/")[-1] or "mcp"
        _mcp_connections[url] = MCPServerConnection(name=name, url=url)
    return _mcp_connections[url]


@ExecutorWorker.register("tool_call")
class ToolCallExecutor(BaseExecutor):
    """
    Executor for tool_call tasks - calls MCP tools.
    """
    
    async def execute(
        self,
        task: dict,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: dict,
    ) -> Any:
        """Execute tool_call task."""
        tool_name = args.get("tool_name")
        tool_args = args.get("tool_args", {})
        tool_call_id = args.get("tool_call_id", "")
        mcp_url = args.get("mcp_url")
        mcp_session_id = args.get("mcp_session_id")
        
        if not tool_name:
            return {"error": "No tool_name specified", "success": False}
        
        if not mcp_url:
            return {"error": "No mcp_url specified", "success": False}
        
        # Get runtime info via Gateway API
        runtime = await self.client.get_runtime(runtime_id)
        if not runtime:
            raise ValueError(f"Runtime not found: {runtime_id}")
        
        subagent_id = runtime.get("subagent_id")
        if not subagent_id:
            raise ValueError(f"subagent_id not found in Runtime {runtime_id}")
        
        actual_agent_id = runtime.get("agent_id")
        if not actual_agent_id:
            raise ValueError(f"agent_id not found in Runtime {runtime_id}")
        
        round_id = runtime.get("current_round_id", "round-1")
        idempotency_key = f"{actual_agent_id}-{subagent_id}-{round_id}-{tool_call_id or task.get('id')}"
        
        print(f"[ToolCallExecutor] Calling {tool_name} for runtime {runtime_id}")
        
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Check idempotency
                cached = await _check_idempotency(self.gateway_url, session, idempotency_key)
                if cached is not None:
                    print(f"[ToolCallExecutor] Returning cached result for {idempotency_key}")
                    return cached
                
                # 2. Register this execution
                await _register_execution(self.gateway_url, session, {
                    "idempotency_key": idempotency_key,
                    "agent_id": actual_agent_id,
                    "subagent_id": subagent_id,
                    "round_id": round_id,
                    "mcpcall_id": tool_call_id or task.get("id"),
                    "action": tool_name,
                    "args": tool_args,
                })
                
                # 3. Call MCP server
                result = await _call_mcp_server(mcp_url, tool_name, tool_args, mcp_session_id)
                
                # 4. Update execution record
                if result.get("success"):
                    await _complete_execution(self.gateway_url, session, idempotency_key, result)
                else:
                    await _fail_execution(self.gateway_url, session, idempotency_key, result.get("error", "Unknown error"))
                
                # 5. Broadcast tool completion
                await _broadcast_log(self.gateway_url, session, actual_agent_id, {
                    "type": "tool_end",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "tool": tool_name,
                        "success": result.get("success", False),
                        "result": _summarize_result(result),
                    },
                })
                
                print(f"[ToolCallExecutor] Tool {tool_name} completed: success={result.get('success')}")
                return result
                
            except Exception as e:
                error = str(e)
                print(f"[ToolCallExecutor] Tool call error: {error}")
                import traceback
                traceback.print_exc()
                
                await _broadcast_log(self.gateway_url, session, actual_agent_id, {
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "tool": tool_name,
                        "error": error[:200],
                    },
                })
                
                await _fail_execution(self.gateway_url, session, idempotency_key, error)
                return {"success": False, "error": error}


# ==================== MCP Communication ====================

async def _call_mcp_server(
    mcp_url: str,
    tool_name: str,
    args: Dict[str, Any],
    mcp_session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Call MCP tool directly on MCP server."""
    try:
        conn = _get_mcp_connection(mcp_url)
        
        if mcp_session_id and not conn._session_id:
            conn._session_id = mcp_session_id
            print(f"[ToolCallExecutor] Reusing MCP session: {mcp_session_id[:20]}...")
        
        result = await conn.call_tool(tool_name, args, max_retries=3)
        return result
        
    except asyncio.TimeoutError:
        return {"success": False, "error": "MCP call timed out"}
    except Exception as e:
        return {"success": False, "error": f"MCP call error: {str(e)}"}


async def _get_mcp_server_url(
    gateway_url: str,
    session: aiohttp.ClientSession,
    agent_id: str,
) -> Optional[str]:
    """Get MCP server URL for an agent from Gateway."""
    try:
        async with session.get(f"{gateway_url}/api/agents/{agent_id}") as response:
            if response.status == 200:
                agent = await response.json()
                ports = agent.get("ports", {})
                if isinstance(ports, dict):
                    mcp_port = ports.get("mcp")
                    if mcp_port:
                        return f"http://localhost:{mcp_port}"
                
                vm = agent.get("vm", {})
                if isinstance(vm, dict):
                    vm_ports = vm.get("ports", {})
                    if isinstance(vm_ports, dict):
                        mcp_port = vm_ports.get("mcp")
                        if mcp_port:
                            return f"http://localhost:{mcp_port}"
                    
                    agent_index = vm.get("agent_index", 0)
                    return f"http://localhost:{19900 + agent_index}"
                    
    except Exception as e:
        print(f"[ToolCallExecutor] Get MCP URL error: {e}")
    
    return None


# ==================== Idempotency ====================

async def _check_idempotency(
    gateway_url: str,
    session: aiohttp.ClientSession,
    idempotency_key: str,
) -> Optional[Dict[str, Any]]:
    """Check if this execution has already completed."""
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
                    return result.get("result")
                
                if status == "executing":
                    await asyncio.sleep(1.0)
                    return await _check_idempotency(gateway_url, session, idempotency_key)
            
            return None
            
    except Exception as e:
        print(f"[ToolCallExecutor] Idempotency check error: {e}")
        return None


async def _register_execution(
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
                "tool_name": task.get("action", "unknown"),
                "args": task.get("args", {}),
            },
        )
    except Exception as e:
        print(f"[ToolCallExecutor] Register execution error: {e}")


async def _complete_execution(
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
        print(f"[ToolCallExecutor] Complete execution error: {e}")


async def _fail_execution(
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
        print(f"[ToolCallExecutor] Fail execution error: {e}")


# ==================== Logging ====================

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
        pass


def _summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize MCP result for display."""
    summary = {}
    
    if result.get("success") is not None:
        summary["success"] = result["success"]
    
    if result.get("error"):
        summary["error"] = str(result["error"])[:100]
        return summary
    
    inner = result.get("result", result)
    
    if isinstance(inner, dict):
        for key in ["message", "url", "output", "content", "status", "id", "success"]:
            if key in inner:
                val = inner[key]
                if isinstance(val, str) and len(val) > 100:
                    summary[key] = val[:100] + "..."
                else:
                    summary[key] = val
        
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
