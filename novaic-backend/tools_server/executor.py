"""
Tool Executor - 执行工具调用

负责执行内置工具和外部工具的调用。

内置工具：直接调用 Gateway API（使用 httpx.AsyncClient）
外部工具：通过 MCPServerConnection 调用

工具路由规则：
- memory_* 工具: POST/GET /internal/rt/{runtime_id}/memory/*
- runtime_* 工具: GET/POST /internal/runtimes/* 或 /internal/rt/{runtime_id}/*
- chat_* 工具: POST/GET /internal/rt/{runtime_id}/chat/*
- web_* 工具: POST /internal/web/*
- qemu_* 工具: POST/GET /internal/rt/{runtime_id}/qemu/*
- task_* 工具: POST/GET /internal/rt/{runtime_id}/tasks/* 或 /internal/tasks/*

特殊工具：
- goal_set, goal_progress, goal_complete: 通过 memory_save/memory_recall 间接实现
- session_state: 调用两个 API 并合并结果
- runtime_rest: 只有 Main Runtime 可以调用
"""

import os
import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union

import httpx

if TYPE_CHECKING:
    from mcp_client.mcp_client import MCPServerConnection
    from tools_server.runtime_manager import RuntimeContext, RuntimeManager

logger = logging.getLogger(__name__)

# Gateway API 基础 URL
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:19999")

# 内置工具名称集合（这些工具直接调用 Gateway API 或 vmuse_adapter）
# 注意：这是工具名称集合，不同于 tools.py 中的 BUILTIN_TOOLS（工具定义字典）
BUILTIN_TOOL_NAMES = {
    # Memory 工具
    "memory_save",
    "memory_recall",
    "memory_delete",
    "memory_list_namespaces",
    "memory_log_task",
    "memory_get_task_history",
    
    # Goal 工具（通过 memory 实现）
    "goal_set",
    "goal_progress",
    "goal_complete",
    
    # Runtime 工具
    "runtime_list",
    "runtime_history",
    "runtime_send",
    "runtime_rest",
    
    # Chat 工具
    "chat_event",
    "chat_reply",
    "chat_ask",
    "chat_notify",
    "chat_show_image",
    "chat_history",
    "chat_get_message",
    
    # SubAgent 工具
    "subagent_spawn",
    "subagent_query",
    "subagent_cancel",
    
    # Web 工具
    "web_search",
    "web_fetch",
    
    # QEMU 工具
    "qemu_ssh_exec",
    "qemu_status",
    "qemu_start_vm",
    "qemu_restart_vm",
    "qemu_shutdown_vm",
    
    # Task 工具
    "task_spawn",
    "task_async",
    "task_list",
    "task_query",
    "task_cancel",
    "task_result",
    "task_summary",
    
    # Session 工具
    "session_state",
    
    # Task history (memory 分类中定义)
    "task_log",
    "task_history",
    
    # VM 工具（通过 vmuse_adapter 实现）
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_screenshot",
    "browser_content",
    "browser_scroll",
    "browser_eval",
    "browser_get_tabs",
    "browser_switch_tab",
    "browser_close_tab",
    "file_read",
    "file_write",
    "shell_exec",
    "screenshot",
    "mouse",
    "keyboard",
    "list_windows",
    "focus_window",
    "maximize_window",
    "minimize_window",
    "close_window",
    "resize_window",
    "launch_app",
    "system_snapshot",
    "clipboard_get",
    "clipboard_set",
    "environment_info",
}


class ToolExecutor:
    """
    工具执行器
    
    负责路由和执行工具调用。
    - 内置工具直接调用 Gateway API
    - 外部工具通过 MCP 客户端调用
    
    支持两种初始化方式：
    1. 直接传入 runtime_id, agent_id, subagent_id（新 API）
    2. 传入 runtime (RuntimeContext) 和 manager (RuntimeManager)（兼容 api.py）
    """
    
    def __init__(
        self,
        runtime_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        subagent_id: Optional[str] = None,
        external_mcp_client: Optional["MCPServerConnection"] = None,
        # 兼容 api.py 的参数
        runtime: Optional["RuntimeContext"] = None,
        manager: Optional["RuntimeManager"] = None,
    ):
        """
        初始化工具执行器
        
        支持两种初始化方式：
        
        方式 1（新 API）:
            executor = ToolExecutor(
                runtime_id="rt-xxx",
                agent_id="agent-xxx",
                subagent_id="main-xxx",
                external_mcp_client=mcp_client,
            )
        
        方式 2（兼容 api.py）:
            executor = ToolExecutor(runtime=runtime_context, manager=runtime_manager)
        
        Args:
            runtime_id: Runtime ID (rt-xxx)
            agent_id: Agent ID
            subagent_id: SubAgent ID
            external_mcp_client: 可选的外部 MCP 客户端，用于调用外部工具
            runtime: RuntimeContext 实例（兼容 api.py）
            manager: RuntimeManager 实例（兼容 api.py）
        """
        # 兼容 api.py 的初始化方式
        if runtime is not None:
            self.runtime_id = runtime.runtime_id
            self.agent_id = runtime.agent_id
            self.subagent_id = runtime.subagent_id
            self._runtime_context = runtime
            self._manager = manager
        else:
            self.runtime_id = runtime_id or ""
            self.agent_id = agent_id or ""
            self.subagent_id = subagent_id or ""
            self._runtime_context = None
            self._manager = None
        
        self.external_mcp_client = external_mcp_client
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=GATEWAY_URL,
                timeout=httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0),
                transport=httpx.AsyncHTTPTransport(proxy=None),
                trust_env=False,
            )
        return self._http_client
    
    async def close(self):
        """关闭资源"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用
        
        根据工具名称路由到内置工具或外部工具。
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果 dict，包含 success 字段
        """
        try:
            if tool_name in BUILTIN_TOOL_NAMES:
                return await self._execute_builtin(tool_name, arguments)
            else:
                return await self._execute_external(tool_name, arguments)
        except Exception as e:
            logger.error(f"[ToolExecutor] Failed to execute {tool_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_builtin(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行内置工具
        
        内置工具直接调用 Gateway API。
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果
        """
        client = await self._get_http_client()
        
        try:
            # ==================== Memory 工具 ====================
            if tool_name == "memory_save":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/save",
                    json={
                        "key": arguments.get("key"),
                        "value": arguments.get("value"),
                        "namespace": arguments.get("namespace", "default"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "memory_recall":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/recall",
                    json={
                        "key": arguments.get("key"),
                        "namespace": arguments.get("namespace", "default"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "memory_delete":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/delete",
                    json={
                        "key": arguments.get("key"),
                        "namespace": arguments.get("namespace", "default"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "memory_list_namespaces":
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/memory/namespaces"
                )
                return self._handle_response(response)
            
            elif tool_name == "memory_log_task":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/task/log",
                    json={
                        "action": arguments.get("action"),
                        "details": arguments.get("details"),
                        "status": arguments.get("status", "completed"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "memory_get_task_history":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/task/history",
                    json={
                        "limit": arguments.get("limit", 20),
                        "status_filter": arguments.get("status_filter"),
                    }
                )
                return self._handle_response(response)
            
            # ==================== Goal 工具（通过 Memory 实现）====================
            elif tool_name == "goal_set":
                # 保存 goal 到 memory 的 goals namespace
                goal_data = {
                    "description": arguments.get("description"),
                    "status": "active",
                    "progress": 0,
                    "steps": arguments.get("steps", []),
                    "metadata": arguments.get("metadata", {}),
                }
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/save",
                    json={
                        "key": arguments.get("goal_id", "current_goal"),
                        "value": goal_data,
                        "namespace": "goals",
                    }
                )
                result = self._handle_response(response)
                if result.get("success"):
                    result["goal_id"] = arguments.get("goal_id", "current_goal")
                    result["message"] = f"Goal set: {goal_data['description']}"
                return result
            
            elif tool_name == "goal_progress":
                # 读取当前 goal，更新进度，然后保存
                goal_id = arguments.get("goal_id", "current_goal")
                
                # 读取当前 goal
                recall_response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/recall",
                    json={"key": goal_id, "namespace": "goals"}
                )
                recall_result = self._handle_response(recall_response)
                
                if not recall_result.get("success") or not recall_result.get("value"):
                    return {"success": False, "error": f"Goal not found: {goal_id}"}
                
                goal_data = recall_result["value"]
                if isinstance(goal_data, str):
                    import json
                    try:
                        goal_data = json.loads(goal_data)
                    except:
                        goal_data = {"description": goal_data, "status": "active", "progress": 0}
                
                # 更新进度
                goal_data["progress"] = arguments.get("progress", goal_data.get("progress", 0))
                if arguments.get("step_completed"):
                    goal_data.setdefault("completed_steps", []).append(arguments["step_completed"])
                if arguments.get("notes"):
                    goal_data.setdefault("progress_notes", []).append(arguments["notes"])
                
                # 保存更新后的 goal
                save_response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/save",
                    json={"key": goal_id, "value": goal_data, "namespace": "goals"}
                )
                result = self._handle_response(save_response)
                if result.get("success"):
                    result["goal_id"] = goal_id
                    result["progress"] = goal_data["progress"]
                    result["message"] = f"Goal progress updated to {goal_data['progress']}%"
                return result
            
            elif tool_name == "goal_complete":
                # 标记 goal 为完成
                goal_id = arguments.get("goal_id", "current_goal")
                
                # 读取当前 goal
                recall_response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/recall",
                    json={"key": goal_id, "namespace": "goals"}
                )
                recall_result = self._handle_response(recall_response)
                
                if not recall_result.get("success") or not recall_result.get("value"):
                    return {"success": False, "error": f"Goal not found: {goal_id}"}
                
                goal_data = recall_result["value"]
                if isinstance(goal_data, str):
                    import json
                    try:
                        goal_data = json.loads(goal_data)
                    except:
                        goal_data = {"description": goal_data}
                
                # 更新状态
                goal_data["status"] = "completed"
                goal_data["progress"] = 100
                goal_data["completion_result"] = arguments.get("result", "")
                
                # 保存更新后的 goal
                save_response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/save",
                    json={"key": goal_id, "value": goal_data, "namespace": "goals"}
                )
                result = self._handle_response(save_response)
                if result.get("success"):
                    result["goal_id"] = goal_id
                    result["message"] = "Goal marked as completed"
                return result
            
            # ==================== Runtime 工具 ====================
            elif tool_name == "runtime_list":
                response = await client.get("/internal/runtimes/list")
                return self._handle_response(response)
            
            elif tool_name == "runtime_history":
                response = await client.post(
                    f"/internal/runtimes/{self.runtime_id}/history",
                    json={
                        "limit": arguments.get("limit", 50),
                        "offset": arguments.get("offset", 0),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "runtime_send":
                target_runtime_id = arguments.get("runtime_id", self.runtime_id)
                response = await client.post(
                    f"/internal/runtimes/{target_runtime_id}/send",
                    json={"message": arguments.get("message", "")}
                )
                return self._handle_response(response)
            
            elif tool_name == "runtime_rest":
                # 只有 Main Runtime 可以调用
                if not self.subagent_id.startswith("main"):
                    return {
                        "success": False,
                        "error": "runtime_rest can only be called by Main Runtime",
                    }
                
                response = await client.post(
                    f"/internal/runtimes/{self.runtime_id}/rest",
                    json={
                        "reason": arguments.get("reason", "Agent requested rest"),
                        "wake_triggers": arguments.get("wake_triggers", [{"type": "user_response"}]),
                        "handoff_notes": arguments.get("handoff_notes"),
                    }
                )
                return self._handle_response(response)
            
            # ==================== Chat 工具 ====================
            elif tool_name == "chat_event":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/chat/event",
                    json={
                        "type": arguments.get("type", "AGENT_REPLY"),
                        "data": arguments.get("data", {}),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "chat_history":
                limit = arguments.get("limit", 20)
                summary_length = arguments.get("summary_length", 50)
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/chat/history",
                    params={"limit": limit, "summary_length": summary_length},
                )
                return self._handle_response(response)
            
            elif tool_name == "chat_get_message":
                message_id = arguments.get("message_id")
                if not message_id:
                    return {"success": False, "error": "message_id is required"}
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/chat/message/{message_id}"
                )
                return self._handle_response(response)
            
            elif tool_name == "chat_reply":
                # 发送回复消息
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/chat/event",
                    json={
                        "type": "AGENT_REPLY",
                        "data": {
                            "message": arguments.get("message", ""),
                            "attachments": arguments.get("attachments", []),
                        },
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "chat_ask":
                # 向用户提问
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/chat/event",
                    json={
                        "type": "AGENT_ASK",
                        "data": {
                            "question": arguments.get("question", ""),
                            "options": arguments.get("options"),
                            "timeout_seconds": arguments.get("timeout_seconds", 300),
                        },
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "chat_notify":
                # 发送通知
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/chat/event",
                    json={
                        "type": "AGENT_NOTIFY",
                        "data": {
                            "message": arguments.get("message", ""),
                            "level": arguments.get("level", "info"),
                        },
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "chat_show_image":
                # 显示图片
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/chat/event",
                    json={
                        "type": "AGENT_IMAGE",
                        "data": {
                            "image_url": arguments.get("image_path", ""),
                            "caption": arguments.get("caption", ""),
                        },
                    }
                )
                return self._handle_response(response)
            
            # ==================== SubAgent 工具 ====================
            elif tool_name == "subagent_spawn":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/subagent/spawn",
                    json={
                        "task": arguments.get("task", ""),
                        "share_context": arguments.get("share_context", False),
                        "timeout_minutes": arguments.get("timeout_minutes", 30),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "subagent_query":
                target_subagent_id = arguments.get("subagent_id")
                if not target_subagent_id:
                    return {"success": False, "error": "subagent_id is required"}
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/subagent/{target_subagent_id}/status"
                )
                return self._handle_response(response)
            
            elif tool_name == "subagent_cancel":
                target_subagent_id = arguments.get("subagent_id")
                if not target_subagent_id:
                    return {"success": False, "error": "subagent_id is required"}
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/subagent/{target_subagent_id}/cancel"
                )
                return self._handle_response(response)
            
            # ==================== Web 工具 ====================
            elif tool_name == "web_search":
                response = await client.post(
                    "/internal/web/search",
                    json={
                        "query": arguments.get("query", ""),
                        "count": arguments.get("count", 10),
                        "freshness": arguments.get("freshness"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "web_fetch":
                response = await client.post(
                    "/internal/web/fetch",
                    json={
                        "url": arguments.get("url", ""),
                        "extract_main_content": arguments.get("extract_main_content", True),
                        "max_length": arguments.get("max_length", 50000),
                    }
                )
                return self._handle_response(response)
            
            # ==================== QEMU 工具 ====================
            elif tool_name == "qemu_ssh_exec":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/qemu/ssh-exec",
                    json={
                        "command": arguments.get("command", ""),
                        "timeout": arguments.get("timeout", 30),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "qemu_status":
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/qemu/status"
                )
                return self._handle_response(response)
            
            elif tool_name == "qemu_start_vm":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/qemu/start",
                    json={
                        "memory": arguments.get("memory", "4096"),
                        "cpus": arguments.get("cpus", 4),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "qemu_restart_vm":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/qemu/restart",
                    json={
                        "graceful": arguments.get("graceful", True),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "qemu_shutdown_vm":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/qemu/shutdown",
                    json={
                        "graceful": arguments.get("graceful", True),
                        "quick": arguments.get("quick", False),
                    }
                )
                return self._handle_response(response)
            
            
            # ==================== Task 工具 ====================
            elif tool_name == "task_spawn":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/tasks/spawn",
                    json={
                        "task_type": arguments.get("task_type", "tool"),
                        "config": arguments.get("config", {}),
                        "label": arguments.get("label"),
                        "timeout_seconds": arguments.get("timeout_seconds", 0),
                        "notify_on": arguments.get("notify_on"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "task_list":
                status = arguments.get("status")
                params = {}
                if status:
                    params["status"] = status
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/tasks",
                    params=params,
                )
                return self._handle_response(response)
            
            elif tool_name == "task_query":
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                params = {
                    "include_outputs": arguments.get("include_outputs", False),
                }
                if arguments.get("start_line") is not None:
                    params["start_line"] = arguments["start_line"]
                if arguments.get("end_line") is not None:
                    params["end_line"] = arguments["end_line"]
                if arguments.get("tail_lines") is not None:
                    params["tail_lines"] = arguments["tail_lines"]
                response = await client.get(
                    f"/internal/tasks/{task_id}",
                    params=params,
                )
                return self._handle_response(response)
            
            elif tool_name == "task_cancel":
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                reason = arguments.get("reason")
                params = {}
                if reason:
                    params["reason"] = reason
                response = await client.post(
                    f"/internal/tasks/{task_id}/cancel",
                    params=params,
                )
                return self._handle_response(response)
            
            elif tool_name == "task_result":
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                response = await client.get(
                    f"/internal/tasks/{task_id}/result",
                    params={"format": arguments.get("format", "summary")},
                )
                return self._handle_response(response)
            
            elif tool_name == "task_async":
                # 异步执行任何工具
                tool = arguments.get("tool")
                if not tool:
                    return {"success": False, "error": "tool is required"}
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/tasks/spawn",
                    json={
                        "task_type": "tool",
                        "config": {
                            "tool": tool,
                            "args": arguments.get("args", {}),
                        },
                        "label": arguments.get("label"),
                        "timeout_seconds": 0,  # No timeout for async tasks
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "task_summary":
                # 获取任务的 AI 摘要
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                response = await client.get(
                    f"/internal/tasks/{task_id}/result",
                    params={"format": "summary"},
                )
                return self._handle_response(response)
            
            elif tool_name == "task_log":
                # 记录任务日志（使用 memory_log_task）
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/task/log",
                    json={
                        "action": arguments.get("action"),
                        "details": arguments.get("details"),
                        "status": arguments.get("status", "completed"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "task_history":
                # 获取任务历史（使用 memory_get_task_history）
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/memory/task/history",
                    json={
                        "limit": arguments.get("limit", 20),
                        "status_filter": arguments.get("status_filter"),
                    }
                )
                return self._handle_response(response)
            
            # ==================== Session 工具 ====================
            elif tool_name == "session_state":
                # 调用两个 API 并合并结果
                # 1. 获取 runtime 信息
                runtime_response = await client.get(
                    f"/internal/runtimes/{self.runtime_id}"
                )
                runtime_result = self._handle_response(runtime_response)
                
                # 2. 获取 subagent 信息
                subagent_response = await client.get(
                    f"/internal/subagents/{self.agent_id}/{self.subagent_id}"
                )
                subagent_result = self._handle_response(subagent_response)
                
                # 合并结果
                return {
                    "success": True,
                    "runtime": runtime_result if runtime_result.get("success", True) else None,
                    "subagent": subagent_result if subagent_result.get("success", True) else None,
                    "runtime_id": self.runtime_id,
                    "agent_id": self.agent_id,
                    "subagent_id": self.subagent_id,
                }
            
            # ==================== VM 工具（通过 vmuse_adapter）====================
            elif tool_name in [
                "browser_navigate", "browser_click", "browser_type", 
                "browser_screenshot", "browser_content", "browser_scroll",
                "browser_eval", "browser_get_tabs", "browser_switch_tab", "browser_close_tab",
                "file_read", "file_write", "shell_exec", "screenshot",
                "mouse", "keyboard",
                "list_windows", "focus_window", "maximize_window", "minimize_window",
                "close_window", "resize_window", "launch_app",
                "system_snapshot", "clipboard_get", "clipboard_set", "environment_info",
            ]:
                # 使用 vmuse_adapter 调用 VM 工具
                from gateway.clients.vmuse_adapter import get_vmuse_adapter
                
                adapter = get_vmuse_adapter()
                
                # 直接使用 agent_id 作为 vm_id（vmcontrol 使用 agent_id 识别 VM）
                result = await adapter.call_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    vm_id=self.agent_id
                )
                
                return result
            
            else:
                return {"success": False, "error": f"Unknown builtin tool: {tool_name}"}
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[ToolExecutor] HTTP error for {tool_name}: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            }
        except httpx.RequestError as e:
            logger.error(f"[ToolExecutor] Request error for {tool_name}: {e}")
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    async def _execute_external(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行外部工具（通过 MCP 客户端）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果
        """
        if self.external_mcp_client is None:
            return {
                "success": False,
                "error": f"External tool '{tool_name}' requires MCP client, but none is configured",
            }
        
        try:
            result = await self.external_mcp_client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"[ToolExecutor] MCP call failed for {tool_name}: {e}")
            return {"success": False, "error": f"MCP call failed: {str(e)}"}
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        处理 HTTP 响应
        
        Args:
            response: httpx Response 对象
        
        Returns:
            解析后的 JSON 响应，或错误 dict
        """
        try:
            response.raise_for_status()
            result = response.json()
            # 确保结果包含 success 字段
            if "success" not in result:
                result["success"] = True
            return result
        except httpx.HTTPStatusError as e:
            error_text = ""
            try:
                error_data = e.response.json()
                error_text = error_data.get("detail", str(error_data))
            except:
                error_text = e.response.text[:200]
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {error_text}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_builtin_tool(self, tool_name: str) -> bool:
        """检查是否是内置工具"""
        return tool_name in BUILTIN_TOOL_NAMES
    
    @staticmethod
    def get_builtin_tool_names() -> List[str]:
        """获取所有内置工具名称列表"""
        return list(BUILTIN_TOOL_NAMES)
