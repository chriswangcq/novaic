"""
AggregateMCP - 聚合 MCP Gateway

v3.0: 简化架构 - 直接注册工具调用 Gateway API

Gateway 作为统一 MCP 入口：
1. 内置工具: 直接注册，调用 Gateway API (memory_*, chat_*, runtime_*, qemu_*, web_*)
2. 外部工具: 通过 ToolRegistry 发现 (vmuse 等外部 MCP)
3. task_* 异步任务工具
4. Skills 作为 MCP Resources

Architecture:
    AggregateMCP (FastMCP) - 每个 Runtime 一个
        ├── 内置工具 (调用 Gateway API):
        │   ├── memory_* (10 tools)
        │   ├── runtime_* (7 tools)
        │   ├── chat_* (6 tools)
        │   ├── web_* (2 tools)
        │   └── qemu_* (2 tools, 更多通过外部 vmuse)
        ├── 外部工具 (ToolRegistry 发现):
        │   └── vmuse (VM 内运行的 MCP Server)
        ├── task_* (5 tools)
        └── Skills (MCP Resources)
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from functools import partial
from datetime import datetime
from pydantic import BaseModel

from fastmcp import FastMCP

import httpx

from .registry import ToolRegistry


# Gateway API URL (configured via env or default)
GATEWAY_URL = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")


async def _call_gateway_api(method: str, path: str, **kwargs) -> Dict[str, Any]:
    """Call Gateway API endpoint.
    
    MCP Gateway should not directly import gateway modules.
    All inter-service communication goes through HTTP API.
    
    Args:
        method: HTTP method (GET, POST, DELETE)
        path: API path (e.g., /internal/memory/{agent_id}/save)
        params: Query parameters (for GET and POST)
        json: JSON body (for POST)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{GATEWAY_URL}{path}"
        params = kwargs.get("params")
        json_body = kwargs.get("json")
        
        if method == "GET":
            resp = await client.get(url, params=params)
        elif method == "POST":
            resp = await client.post(url, params=params, json=json_body)
        elif method == "DELETE":
            resp = await client.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        resp.raise_for_status()
        return resp.json()


class PortConfig(BaseModel):
    """Port configuration (passed from caller, not imported from config)."""
    vm: int = 20000
    session: int = 20001
    local: int = 20002
    memory: int = 20003
    chat: int = 20004
    qemudebug: int = 20005
    vnc: int = 20006
    websocket: int = 20007
    ssh: int = 20008


# Discovery intervals (for external MCP only)
DISCOVERY_INTERVAL_FAILED = 5  # seconds for failed servers
DISCOVERY_INTERVAL_SUCCESS = 30  # seconds for successful servers
DISCOVERY_TIMEOUT = 30  # seconds timeout for discovery

# Skills directory (relative to mcp_gateway)
SKILLS_DIR = Path(__file__).parent / "skills"

logger = logging.getLogger(__name__)


class AggregateMCP:
    """
    聚合 MCP Gateway。
    
    v3.0: 简化架构
    - 内置工具直接注册，调用 Gateway API
    - ToolRegistry 只用于发现外部 MCP (vmuse)
    """
    
    def __init__(
        self,
        agent_id: str,
        runtime_id: str,
        subagent_id: str,
        ports: PortConfig,
    ):
        """
        Initialize the MCP Gateway for a Runtime.
        
        Args:
            agent_id: Unique agent identifier (UUID)
            runtime_id: Runtime ID (rt-xxx)
            subagent_id: SubAgent ID (main-xxx or sub-xxx)
            ports: Port configuration (obtained from Gateway API by caller)
        """
        self.agent_id = agent_id
        self.runtime_id = runtime_id
        self.subagent_id = subagent_id
        self.ports = ports
        
        # Create dedicated ToolRegistry for external MCP discovery only
        self.registry = ToolRegistry()
        self._register_external_servers()
        
        # Create FastMCP instance
        self.mcp = FastMCP(
            name=f"novaic-runtime-{subagent_id[:12]}",
            instructions=self._build_instructions(),
        )
        
        # Track registered tools and skills
        self._registered_tools: List[str] = []
        self._registered_skills: List[str] = []
        self._builtin_tools_count = 0
        
        # Track server discovery status (external only)
        self._discovered_servers: Set[str] = set()
        self._discovery_task: Optional[asyncio.Task] = None
        self._discovery_running = False
        
        logger.info(f"[AggregateMCP] Created gateway for runtime {subagent_id} (agent={agent_id})")
    
    @property
    def agent_index(self) -> int:
        """Get agent index (for compatibility)."""
        return 0
    
    def _build_instructions(self) -> str:
        """Build initial MCP server instructions."""
        return f"NovAIC Runtime Gateway ({self.subagent_id}) - 统一 MCP 入口\n\n正在初始化..."
    
    def _build_dynamic_instructions(self) -> str:
        """Build dynamic instructions based on registered tools."""
        lines = [
            f"# NovAIC Runtime Gateway ({self.subagent_id})",
            "",
            "本 Gateway 是当前 Runtime 的统一 MCP 入口。",
            "",
            "## 内置工具 (调用 Gateway API)",
            "",
            "| 类别 | 工具 |",
            "|------|------|",
            "| Memory | memory_save, memory_recall, memory_delete, memory_list_namespaces, task_log, task_history, goal_set, goal_progress, goal_complete, session_state |",
            "| Runtime | runtime_list, runtime_history, runtime_send, runtime_rest, subagent_spawn, subagent_query, subagent_cancel |",
            "| Chat | chat_reply, chat_ask, chat_notify, chat_show_image, chat_history, chat_get_message |",
            "| Web | web_search, web_fetch |",
            "| QEMU | qemu_ssh_exec, qemu_status |",
            "| Task | task_async, task_query, task_list, task_cancel, task_summary |",
            "",
        ]
        
        # External tools from ToolRegistry
        stats = self.registry.get_stats()
        tools_by_server = stats.get("tools_by_server", {})
        
        if tools_by_server:
            lines.append("## 外部工具 (通过 ToolRegistry)")
            lines.append("")
            for server_name, tool_count in tools_by_server.items():
                status = "✅" if tool_count > 0 else "⏳"
                lines.append(f"- {server_name}: {tool_count} tools {status}")
            lines.append("")
        
        if self._registered_skills:
            lines.append("## Skills")
            lines.append("")
            for skill in self._registered_skills:
                lines.append(f"- {skill}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _register_external_servers(self) -> None:
        """Register external MCP servers for discovery (vmuse only).
        
        Internal servers (memory, chat, etc.) are no longer registered here.
        Their functionality is provided by builtin tools calling Gateway API.
        """
        # Only register vmuse (runs inside the virtual machine)
        self.registry.register_server("vmuse", port=self.ports.vm, priority=1, connect_timeout=1.0)
        
        logger.info(f"[AggregateMCP] Registered 1 external server (vmuse) for discovery")
    
    async def setup(self) -> None:
        """Setup the gateway by registering builtin tools, skills, and task tools."""
        # Setup builtin tools (call Gateway API)
        self._setup_builtin_tools()
        
        # Setup skills as MCP resources
        await self._setup_skills()
        
        # Setup task_* tools
        self._setup_task_tools()
        
        # Update instructions
        self._update_instructions()
        
        logger.info(
            f"[AggregateMCP] Setup complete: {self._builtin_tools_count} builtin tools, "
            f"{len(self._registered_skills)} skills"
        )
    
    def _update_instructions(self) -> None:
        """Update MCP instructions to reflect current state."""
        try:
            dynamic_instructions = self._build_dynamic_instructions()
            if hasattr(self.mcp, '_instructions'):
                self.mcp._instructions = dynamic_instructions
            elif hasattr(self.mcp, 'instructions'):
                self.mcp.instructions = dynamic_instructions
        except Exception as e:
            logger.warning(f"[AggregateMCP] Failed to update instructions: {e}")
    
    def _setup_builtin_tools(self) -> None:
        """Register builtin tools that call Gateway API directly."""
        self._setup_memory_tools()
        self._setup_runtime_tools()
        self._setup_chat_tools()
        self._setup_web_tools()
        self._setup_qemu_tools()
        logger.info(f"[AggregateMCP] Registered {self._builtin_tools_count} builtin tools")
    
    # ==================== Memory Tools ====================
    
    def _setup_memory_tools(self) -> None:
        """Register memory_* tools.
        
        v15: Runtime-first API - all calls use /rt/{runtime_id}/ endpoints.
        agent_id is resolved from runtime_id on the server side.
        """
        runtime_id = self.runtime_id
        
        @self.mcp.tool()
        async def memory_save(
            key: str,
            value: Any,
            namespace: Optional[str] = "default",
        ) -> Dict[str, Any]:
            """Save a memory value. Use namespaces to organize related data."""
            try:
                result = await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/memory/save", json={
                    "key": key, "value": value, "namespace": namespace or "default"
                })
                result["persistent"] = True
                return result
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def memory_recall(
            key: Optional[str] = None,
            namespace: Optional[str] = "default",
        ) -> Dict[str, Any]:
            """Recall memory value(s). Omit key to get all in namespace."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/memory/recall", json={
                    "key": key, "namespace": namespace or "default"
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def memory_delete(
            key: str,
            namespace: Optional[str] = "default",
        ) -> Dict[str, Any]:
            """Delete a memory value."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/memory/delete", json={
                    "key": key, "namespace": namespace or "default"
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def memory_list_namespaces() -> Dict[str, Any]:
            """List all memory namespaces."""
            try:
                return await _call_gateway_api("GET", f"/internal/rt/{runtime_id}/memory/namespaces")
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_log(
            action: str,
            details: Optional[str] = None,
            status: Optional[str] = "completed",
        ) -> Dict[str, Any]:
            """Log a task or action for history tracking."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/memory/task/log", json={
                    "action": action, "details": details, "status": status or "completed"
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_history(
            limit: Optional[int] = 20,
            status_filter: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Get task history."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/memory/task/history", json={
                    "limit": limit or 20, "status_filter": status_filter
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Goal tracking (in-memory with persistence)
        _current_goal: Dict[str, Any] = {}
        
        @self.mcp.tool()
        async def goal_set(
            goal: str,
            subtasks: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """Set a goal to track with optional subtasks."""
            nonlocal _current_goal
            _current_goal = {
                "goal": goal,
                "subtasks": subtasks or [],
                "completed_subtasks": [],
                "started_at": datetime.now().isoformat(),
                "status": "in_progress"
            }
            await memory_save("_current_goal", _current_goal, namespace="_system")
            return {"success": True, "goal": goal, "subtasks_count": len(subtasks or [])}
        
        @self.mcp.tool()
        async def goal_progress(
            completed_subtask: Optional[str] = None,
            progress_note: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Update goal progress."""
            nonlocal _current_goal
            if not _current_goal:
                result = await memory_recall("_current_goal", namespace="_system")
                if result.get("found"):
                    _current_goal = result["value"]
                else:
                    return {"success": False, "error": "No goal set"}
            
            if completed_subtask and completed_subtask in _current_goal.get("subtasks", []):
                if completed_subtask not in _current_goal.get("completed_subtasks", []):
                    _current_goal.setdefault("completed_subtasks", []).append(completed_subtask)
            
            if progress_note:
                _current_goal.setdefault("notes", []).append({
                    "note": progress_note, "timestamp": datetime.now().isoformat()
                })
            
            await memory_save("_current_goal", _current_goal, namespace="_system")
            
            total = len(_current_goal.get("subtasks", []))
            completed = len(_current_goal.get("completed_subtasks", []))
            return {
                "success": True,
                "progress_percent": round(completed / total * 100, 1) if total > 0 else 0,
                "completed": completed, "total": total,
            }
        
        @self.mcp.tool()
        async def goal_complete(summary: Optional[str] = None) -> Dict[str, Any]:
            """Mark current goal as complete."""
            nonlocal _current_goal
            if not _current_goal:
                return {"success": False, "error": "No current goal"}
            
            _current_goal["status"] = "completed"
            _current_goal["completed_at"] = datetime.now().isoformat()
            _current_goal["summary"] = summary
            
            import time
            await memory_save(f"goal_{int(time.time())}", _current_goal, namespace="_goal_history")
            await memory_delete("_current_goal", namespace="_system")
            
            result = {"success": True, "goal": _current_goal["goal"]}
            _current_goal = {}
            return result
        
        @self.mcp.tool()
        async def session_state() -> Dict[str, Any]:
            """Get current session state overview."""
            try:
                history_result = await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/memory/task/history", json={"limit": 100})
                ns_result = await _call_gateway_api("GET", f"/internal/rt/{runtime_id}/memory/namespaces")
                
                history = history_result.get("history", [])
                return {
                    "success": True,
                    "runtime_id": runtime_id,
                    "current_goal": _current_goal.get("goal") if _current_goal else None,
                    "recent_actions": [h["action"] for h in history[-5:]] if history else [],
                    "task_stats": {
                        "total": history_result.get("total_count", 0),
                        "completed": len([h for h in history if h.get("status") == "completed"]),
                    },
                    "memory_namespaces": ns_result.get("namespaces", []),
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self._builtin_tools_count += 10
    
    # ==================== Runtime Tools ====================
    
    def _setup_runtime_tools(self) -> None:
        """Register runtime_* tools.
        
        v15: Runtime-first API - most calls use /rt/{runtime_id}/ endpoints.
        agent_id and subagent_id are resolved from runtime_id on the server side.
        """
        runtime_id = self.runtime_id
        subagent_id = self.subagent_id
        
        @self.mcp.tool()
        async def runtime_list() -> Dict[str, Any]:
            """List all active runtimes in this agent."""
            try:
                return await _call_gateway_api("GET", "/internal/runtimes/list")
            except Exception as e:
                return {"error": str(e), "runtimes": []}
        
        @self.mcp.tool()
        async def runtime_history(
            target_runtime_id: str,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0,
        ) -> Dict[str, Any]:
            """Get message history for a specific runtime."""
            try:
                return await _call_gateway_api("POST", f"/internal/runtimes/{target_runtime_id}/history", json={
                    "limit": limit, "offset": offset
                })
            except Exception as e:
                return {"error": str(e), "messages": []}
        
        @self.mcp.tool()
        async def runtime_send(
            target_runtime_id: str,
            message: str,
        ) -> Dict[str, Any]:
            """Send a message to another runtime."""
            try:
                return await _call_gateway_api("POST", f"/internal/runtimes/{target_runtime_id}/send", json={
                    "message": message
                })
            except Exception as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def runtime_rest(
            reason: str,
            wake_triggers: Optional[List[Dict[str, Any]]] = None,
            handoff_notes: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Voluntarily enter rest state. Only Main Runtime can call this."""
            if subagent_id.startswith("sub-"):
                return {"success": False, "error": "SubAgents cannot rest"}
            
            try:
                return await _call_gateway_api("POST", f"/internal/runtimes/{runtime_id}/rest", json={
                    "reason": reason,
                    "wake_triggers": wake_triggers or [{"type": "user_response"}],
                    "handoff_notes": handoff_notes,
                })
            except Exception as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def subagent_spawn(
            task: str,
            share_context: bool = False,
            timeout_minutes: int = 30,
            retry_attempts: int = 3,
            retry_delay_ms: int = 300,
        ) -> Dict[str, Any]:
            """Spawn a SubAgent to execute a task asynchronously (with retries)."""
            last_error = None
            attempts = max(1, retry_attempts)
            for i in range(attempts):
                try:
                    # v15: Runtime-first API - agent_id and parent_subagent_id resolved from runtime_id
                    result = await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/subagent/spawn", json={
                        "task": task,
                        "share_context": share_context,
                        "timeout_minutes": timeout_minutes,
                    })
                    if result.get("subagent_id"):
                        return result
                    last_error = result.get("error") or "spawn failed"
                except Exception as e:
                    last_error = str(e)
                if i < attempts - 1:
                    await asyncio.sleep(retry_delay_ms / 1000.0)
            return {"error": last_error or "spawn failed after retries"}
        
        @self.mcp.tool()
        async def subagent_query(target_subagent_id: str) -> Dict[str, Any]:
            """Query the status of a spawned SubAgent."""
            try:
                # v15: Runtime-first API
                return await _call_gateway_api("GET", f"/internal/rt/{runtime_id}/subagent/{target_subagent_id}/status")
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def subagent_cancel(target_subagent_id: str) -> Dict[str, Any]:
            """Cancel a running SubAgent."""
            try:
                # v15: Runtime-first API
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/subagent/{target_subagent_id}/cancel")
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self._builtin_tools_count += 7
    
    # ==================== Chat Tools ====================
    
    def _setup_chat_tools(self) -> None:
        """Register chat_* tools.
        
        v15: Runtime-first API - all calls use /rt/{runtime_id}/ endpoints.
        agent_id is resolved from runtime_id on the server side.
        """
        runtime_id = self.runtime_id
        
        @self.mcp.tool()
        async def chat_reply(
            message: str,
            attachments: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """Send a reply message to the user."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/chat/event", json={
                    "type": "AGENT_REPLY",
                    "data": {"message": message, "attachments": attachments or []}
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def chat_ask(
            question: str,
            options: Optional[List[str]] = None,
            timeout_seconds: Optional[int] = 300,
        ) -> Dict[str, Any]:
            """Ask the user a question and wait for response."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/chat/event", json={
                    "type": "AGENT_ASK",
                    "data": {"question": question, "options": options}
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def chat_notify(
            message: str,
            level: Optional[str] = "info",
        ) -> Dict[str, Any]:
            """Send a notification (no response expected)."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/chat/event", json={
                    "type": "AGENT_NOTIFY",
                    "data": {"message": message, "level": level}
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def chat_show_image(
            image_path: str,
            caption: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Show an image to the user."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/chat/event", json={
                    "type": "AGENT_IMAGE",
                    "data": {"image_url": image_path, "caption": caption}
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def chat_history(
            limit: Optional[int] = 20,
            summary_length: Optional[int] = 50,
        ) -> Dict[str, Any]:
            """Get recent chat history (summarized)."""
            try:
                return await _call_gateway_api("GET", f"/internal/rt/{runtime_id}/chat/history", params={
                    "limit": limit, "summary_length": summary_length
                })
            except Exception as e:
                return {"success": False, "error": str(e), "messages": []}
        
        @self.mcp.tool()
        async def chat_get_message(message_id: str) -> Dict[str, Any]:
            """Get full content of a chat message."""
            try:
                return await _call_gateway_api("GET", f"/internal/rt/{runtime_id}/chat/message/{message_id}")
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self._builtin_tools_count += 6
    
    # ==================== Web Tools ====================
    
    def _setup_web_tools(self) -> None:
        """Register web_* tools."""
        
        @self.mcp.tool()
        async def web_search(
            query: str,
            count: Optional[int] = 10,
            freshness: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Search the web using Brave Search API."""
            try:
                return await _call_gateway_api("POST", "/internal/web/search", json={
                    "query": query, "count": count, "freshness": freshness
                })
            except Exception as e:
                return {"error": str(e), "results": []}
        
        @self.mcp.tool()
        async def web_fetch(
            url: str,
            extract_main_content: Optional[bool] = True,
            max_length: Optional[int] = 50000,
        ) -> Dict[str, Any]:
            """Fetch a web page and convert to markdown."""
            try:
                return await _call_gateway_api("POST", "/internal/web/fetch", json={
                    "url": url, "extract_main_content": extract_main_content, "max_length": max_length
                })
            except Exception as e:
                return {"url": url, "error": str(e), "success": False}
        
        self._builtin_tools_count += 2
    
    # ==================== QEMU Tools ====================
    
    def _setup_qemu_tools(self) -> None:
        """Register qemu_* tools (basic, more tools come from vmuse).
        
        v15: Runtime-first API - all calls use /rt/{runtime_id}/ endpoints.
        agent_id is resolved from runtime_id on the server side.
        """
        runtime_id = self.runtime_id
        
        @self.mcp.tool()
        async def qemu_ssh_exec(
            command: str,
            timeout: Optional[int] = 30,
        ) -> Dict[str, Any]:
            """Execute command via SSH on VM."""
            try:
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/qemu/ssh-exec", json={
                    "command": command, "timeout": timeout
                })
            except Exception as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def qemu_status() -> Dict[str, Any]:
            """Get QEMU VM status."""
            try:
                return await _call_gateway_api("GET", f"/internal/rt/{runtime_id}/qemu/status")
            except Exception as e:
                return {"error": str(e)}
        
        self._builtin_tools_count += 2
    
    # ==================== Task Tools ====================
    
    def _setup_task_tools(self) -> None:
        """Register task_* async execution tools.
        
        v15: Runtime-first API for task_async and task_list.
        task_query/cancel/summary use task_id directly (no runtime needed).
        """
        runtime_id = self.runtime_id
        
        @self.mcp.tool()
        async def task_async(
            tool: str,
            args: Optional[Dict[str, Any]] = None,
            label: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Execute any tool asynchronously in background."""
            try:
                # v15: Runtime-first API - agent_id resolved from runtime_id
                return await _call_gateway_api("POST", f"/internal/rt/{runtime_id}/tasks/spawn", json={
                    "task_type": "tool",
                    "config": {"tool": tool, "args": args or {}, "registry": "gateway"},
                    "label": label or f"Tool: {tool}",
                })
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_query(
            task_id: str,
            tail_lines: Optional[int] = None,
            start_line: Optional[int] = None,
            end_line: Optional[int] = None,
        ) -> Dict[str, Any]:
            """Query task status and results."""
            try:
                params = {"include_outputs": True}
                if start_line: params["start_line"] = start_line
                if end_line: params["end_line"] = end_line
                if tail_lines: params["tail_lines"] = tail_lines
                # Note: Uses task_id directly, no runtime needed
                return await _call_gateway_api("GET", f"/internal/tasks/{task_id}", params=params)
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_list(status: Optional[str] = None) -> Dict[str, Any]:
            """List all tasks, optionally filtered by status."""
            try:
                # v15: Runtime-first API - filters by agent_id resolved from runtime
                params = {}
                if status: params["status"] = status
                return await _call_gateway_api("GET", f"/internal/rt/{runtime_id}/tasks", params=params)
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_cancel(
            task_id: str,
            reason: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Cancel a running task."""
            try:
                params = {}
                if reason: params["reason"] = reason
                # Note: Uses task_id directly, no runtime needed
                return await _call_gateway_api("POST", f"/internal/tasks/{task_id}/cancel", params=params)
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_summary(task_id: str) -> Dict[str, Any]:
            """Get AI-generated summary of a completed task."""
            try:
                # Note: Uses task_id directly, no runtime needed
                return await _call_gateway_api("GET", f"/internal/tasks/{task_id}/result", params={"format": "summary"})
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self._builtin_tools_count += 5
        logger.info("[AggregateMCP] Registered task_* tools")
    
    # ==================== Skills ====================
    
    async def _setup_skills(self) -> None:
        """Load skills from local files and register as MCP resources."""
        try:
            if not SKILLS_DIR.exists():
                logger.warning(f"[AggregateMCP] Skills directory not found: {SKILLS_DIR}")
                return
            
            for skill_dir in sorted(SKILLS_DIR.iterdir()):
                if not skill_dir.is_dir():
                    continue
                
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue
                
                skill_name = skill_dir.name
                skill_content = skill_file.read_text(encoding="utf-8")
                resource_uri = f"skill://{skill_name}"
                
                @self.mcp.resource(uri=resource_uri)
                def get_skill(content=skill_content):
                    return content
                
                self._registered_skills.append(resource_uri)
                logger.debug(f"[AggregateMCP] Registered skill: {skill_name}")
            
            logger.info(f"[AggregateMCP] Loaded {len(self._registered_skills)} skills")
        except Exception as e:
            logger.error(f"[AggregateMCP] Failed to setup skills: {e}")
    
    # ==================== External Tool Discovery ====================
    
    def start_discovery_task(self) -> None:
        """Start background task to discover external MCP servers (vmuse)."""
        if self._discovery_task is not None:
            return
        
        self._discovery_running = True
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        logger.info(f"[AggregateMCP] Started discovery task for external servers")
    
    def stop_discovery_task(self) -> None:
        """Stop the background discovery task."""
        self._discovery_running = False
        if self._discovery_task is not None:
            self._discovery_task.cancel()
            self._discovery_task = None
    
    async def _discovery_loop(self) -> None:
        """Background task to discover tools from external MCP servers."""
        await asyncio.sleep(0.5)  # Wait for HTTP server
        
        while self._discovery_running:
            try:
                new_tools = await self._discover_external_tools()
                if new_tools > 0:
                    self._update_instructions()
                
                # Check less frequently if all discovered
                if self._discovered_servers:
                    await asyncio.sleep(DISCOVERY_INTERVAL_SUCCESS)
                else:
                    await asyncio.sleep(DISCOVERY_INTERVAL_FAILED)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[AggregateMCP] Discovery error: {e}")
                await asyncio.sleep(DISCOVERY_INTERVAL_FAILED)
    
    async def _discover_external_tools(self) -> int:
        """Discover and register tools from external MCP servers."""
        new_tools_count = 0
        
        try:
            tools = await asyncio.wait_for(
                self.registry.discover_all_tools(use_cache=False),
                timeout=DISCOVERY_TIMEOUT
            )
            
            for tool in tools:
                tool_name = tool.get("name", "")
                if not tool_name or tool_name in self._registered_tools:
                    continue
                
                self._register_proxy_tool(tool)
                self._registered_tools.append(tool_name)
                new_tools_count += 1
            
            # Track discovered servers
            stats = self.registry.get_stats()
            for server_name, count in stats.get("tools_by_server", {}).items():
                if count > 0:
                    self._discovered_servers.add(server_name)
            
            if new_tools_count > 0:
                logger.info(f"[AggregateMCP] Discovered {new_tools_count} external tools")
                
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.debug(f"[AggregateMCP] External discovery failed: {e}")
        
        return new_tools_count
    
    def _register_proxy_tool(self, tool_def: Dict[str, Any]) -> None:
        """Register a proxy tool for external MCP server."""
        tool_name = tool_def.get("name", "")
        description = tool_def.get("description", "")
        input_schema = tool_def.get("inputSchema", {})
        
        proxy_func = self._create_proxy_function(tool_name, input_schema, description)
        self.mcp.tool(name=tool_name)(proxy_func)
    
    def _create_proxy_function(self, tool_name: str, input_schema: Dict[str, Any], description: str):
        """Create proxy function for external tool."""
        async def proxy(**kwargs) -> Dict[str, Any]:
            try:
                result = await self.registry.execute(tool_name, kwargs)
                return await self._auto_truncate_result(result, tool_name)
            except Exception as e:
                return {"error": str(e)}
        
        proxy.__doc__ = description
        proxy.__name__ = tool_name
        return proxy
    
    async def _auto_truncate_result(self, result: Any, tool_name: Optional[str] = None) -> Any:
        """Auto-truncate long results and store full content as task."""
        MAX_LENGTH = 4000
        
        if isinstance(result, str) and len(result) > MAX_LENGTH:
            try:
                resp = await _call_gateway_api("POST", "/internal/tasks/create-completed", json={
                    "tool_name": tool_name or "unknown",
                    "truncated_result": "",
                    "full_output": result,
                    "agent_id": self.agent_id,
                })
                task_id = resp.get("task_id")
                return {
                    "content": result[:1500] + f"\n...[truncated, task_id={task_id}]...\n" + result[-1500:],
                    "task_id": task_id,
                    "truncated": True,
                }
            except Exception:
                return {"content": result[:MAX_LENGTH], "truncated": True}
        
        return result
    
    # ==================== Lifecycle ====================
    
    def get_asgi_app(self):
        """Get the ASGI app for mounting in FastAPI."""
        mcp_app = self.mcp.http_app(path="/")
        
        from starlette.routing import Route
        for route in mcp_app.routes:
            if isinstance(route, Route) and route.path == "/":
                route.methods = {"GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"}
                break
        
        return mcp_app
    
    async def close(self) -> None:
        """Close the gateway and cleanup."""
        self.stop_discovery_task()
        logger.info(f"[AggregateMCP] Closed gateway for {self.subagent_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "agent_id": self.agent_id,
            "runtime_id": self.runtime_id,
            "subagent_id": self.subagent_id,
            "builtin_tools": self._builtin_tools_count,
            "external_tools": len(self._registered_tools) - self._builtin_tools_count,
            "total_tools": len(self._registered_tools),
            "skills": len(self._registered_skills),
            "discovered_servers": list(self._discovered_servers),
        }
