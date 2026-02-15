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

特殊工具：
- goal_set, goal_progress, goal_complete: 通过 memory_save/memory_recall 间接实现
- session_state: 调用两个 API 并合并结果
- runtime_rest: 只有 Main Runtime 可以调用
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union

import httpx

if TYPE_CHECKING:
    from mcp_client.mcp_client import MCPServerConnection
    from tools_server.runtime_manager import RuntimeContext, RuntimeManager

logger = logging.getLogger(__name__)

# Gateway API 基础 URL
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:19999")

# vmcontrol API 基础 URL
VMCONTROL_URL = os.environ.get("VMCONTROL_URL", "http://127.0.0.1:19996")

# Mobile 工具映射表：工具名 -> (endpoint, None)
# 这些工具会被路由到 vmcontrol 的 /api/android/:serial/:endpoint
# 格式与 VM_TOOL_MAPPING 保持一致：(endpoint, operation)，operation 为 None 表示直接使用 endpoint
MOBILE_TOOL_MAPPING = {
    # Phase 1 tools (existing)
    "mobile_screenshot": ("screenshot", None),
    "mobile_touch": ("touch", None),
    "mobile_input": ("input", None),
    "mobile_shell": ("shell", None),
    # Phase 2 - App Management
    "mobile_app_install": ("app/install", None),
    "mobile_app_uninstall": ("app/uninstall", None),
    "mobile_app_launch": ("app/launch", None),
    "mobile_app_list": ("app/list", None),
    "mobile_app_stop": ("app/stop", None),
    # Phase 2 - Browser
    "mobile_browser_open": ("browser/open", None),
    "mobile_browser_get_url": ("browser/get_url", None),
    "mobile_browser_back": ("browser/back", None),
    "mobile_browser_refresh": ("browser/refresh", None),
    # Phase 3 - UI Automation
    "mobile_ui_dump": ("ui/dump", None),
    "mobile_ui_find": ("ui/find", None),
    "mobile_ui_wait": ("ui/wait", None),
    "mobile_ui_scroll": ("ui/scroll", None),
    "mobile_ui_click_element": ("ui/click_element", None),
    # Phase 3 - File Management
    "mobile_file_push": ("file/push", None),
    "mobile_file_pull": ("file/pull", None),
    "mobile_file_list": ("file/list", None),
    "mobile_file_delete": ("file/delete", None),
    "mobile_file_mkdir": ("file/mkdir", None),
    "mobile_file_read": ("file/read", None),
}

# VM 工具映射表：工具名 -> (tool, operation)
# 这些工具会被路由到 vmcontrol 的 /api/vmuse/:agent_id/:tool/:operation
VM_TOOL_MAPPING = {
    # Browser tools
    "browser_navigate": ("browser", "navigate"),
    "browser_click": ("browser", "click"),
    "browser_type": ("browser", "type"),
    "browser_screenshot": ("browser", "screenshot"),
    "browser_content": ("browser", "content"),
    "browser_scroll": ("browser", "scroll"),
    "browser_evaluate": ("browser", "evaluate"),
    "browser_get_tabs": ("browser", "get_tabs"),
    "browser_switch_tab": ("browser", "switch_tab"),
    "browser_close_tab": ("browser", "close_tab"),
    # Desktop tools
    "screenshot": ("desktop", "screenshot"),
    "mouse": ("desktop", "mouse"),
    "keyboard": ("desktop", "keyboard"),
    # Shell tools
    "shell_exec": ("shell", "command"),
    # File tools
    "file_read": ("file", "read"),
    "file_write": ("file", "write"),
    "file_list": ("file", "list"),
    "file_info": ("file", "info"),
    # Window tools
    "list_windows": ("window", "list"),
    "focus_window": ("window", "focus"),
    "maximize_window": ("window", "maximize"),
    "minimize_window": ("window", "minimize"),
    "close_window": ("window", "close"),
    "resize_window": ("window", "resize"),
    "launch_app": ("window", "launch_app"),
    # Context tools
    "system_snapshot": ("context", "system_snapshot"),
    "directory_snapshot": ("context", "directory_snapshot"),
    "app_state": ("context", "app_state"),
    "clipboard_get": ("context", "clipboard_get"),
    "clipboard_set": ("context", "clipboard_set"),
    "recent_files": ("context", "recent_files"),
    "environment_info": ("context", "environment_info"),
}

# 内置工具名称集合（这些工具直接调用 Gateway API 或 vmcontrol）
# 注意：这是工具名称集合，不同于 tools.py 中的 BUILTIN_TOOLS（工具定义字典）
BUILTIN_TOOL_NAMES = {
    # Memory 工具
    "memory_save",
    "memory_recall",
    "memory_delete",
    "memory_list_namespaces",
    "memory_log_task",
    "memory_get_task_history",
    
    # Notebook 工具
    "notebook_write",
    "notebook_list",
    "notebook_read",
    "notebook_update",
    
    # Drive 工具
    "drive_update_profile",
    "drive_update_relationship",
    "memory_update",
    
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
    "subagent_report",
    
    # Web 工具
    "web_search",
    "web_fetch",
    
    # QEMU 工具
    "qemu_ssh_exec",
    "qemu_status",
    "qemu_start_vm",
    "qemu_restart_vm",
    "qemu_shutdown_vm",
    
    # Session 工具
    "session_state",
    
    # Task history (memory 分类中定义)
    "task_log",
    "task_history",
    
    # 四象限任务管理工具
    "task_create",
    "task_start",
    "task_progress",
    "task_complete",
    "task_update",
    "task_board_list",
    "task_delete",
    "drive_log_growth",
    
    # VM 工具（直接调用 vmcontrol）
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_screenshot",
    "browser_content",
    "browser_scroll",
    "browser_evaluate",
    "file_read",
    "file_write",
    "file_list",
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
    
    # Mobile 工具（通过 vmcontrol 访问 Android 设备）
    "mobile_screenshot",
    "mobile_touch",
    "mobile_input",
    "mobile_shell",
    # Phase 2 - App Management
    "mobile_app_install",
    "mobile_app_uninstall",
    "mobile_app_launch",
    "mobile_app_list",
    "mobile_app_stop",
    # Phase 2 - Browser
    "mobile_browser_open",
    "mobile_browser_get_url",
    "mobile_browser_back",
    "mobile_browser_refresh",
    # Phase 3 - UI Automation
    "mobile_ui_dump",
    "mobile_ui_find",
    "mobile_ui_wait",
    "mobile_ui_scroll",
    "mobile_ui_click_element",
    # Phase 3 - File Management
    "mobile_file_push",
    "mobile_file_pull",
    "mobile_file_list",
    "mobile_file_delete",
    "mobile_file_mkdir",
    "mobile_file_read",
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
                # 工具执行超时由心跳机制管理，HTTP 层不做限制
                # read=None 表示无超时限制，只要 Worker 还在发心跳，工具就可以一直执行
                timeout=httpx.Timeout(connect=10.0, read=None, write=30.0, pool=10.0),
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
            # 执行工具
            if tool_name in BUILTIN_TOOL_NAMES:
                result = await self._execute_builtin(tool_name, arguments)
            else:
                result = await self._execute_external(tool_name, arguments)
            
            return result
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
            
            # ==================== Notebook 工具 ====================
            elif tool_name == "notebook_write":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/notebook/write",
                    json={
                        "entry_type": arguments.get("entry_type"),
                        "title": arguments.get("title"),
                        "content": arguments.get("content"),
                        "related_topics": arguments.get("related_topics", []),
                        "relevance_score": arguments.get("relevance_score", 0.5),
                        "expires_at": arguments.get("expires_at"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "notebook_list":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/notebook/list",
                    json={
                        "entry_type": arguments.get("entry_type"),
                        "status": arguments.get("status"),
                        "limit": arguments.get("limit", 20),
                        "include_expired": arguments.get("include_expired", False),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "notebook_read":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/notebook/read",
                    json={"entry_id": arguments.get("entry_id")}
                )
                return self._handle_response(response)
            
            elif tool_name == "notebook_update":
                payload = {"entry_id": arguments.get("entry_id")}
                for key in ("status", "content", "title", "relevance_score", "expires_at"):
                    val = arguments.get(key)
                    if val is not None:
                        payload[key] = val
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/notebook/update",
                    json=payload
                )
                return self._handle_response(response)
            
            # ==================== Drive 工具 ====================
            elif tool_name == "drive_update_profile":
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/drive/update-profile",
                    json={
                        "key": arguments.get("key"),
                        "value": arguments.get("value"),
                        "reason": arguments.get("reason"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "drive_update_relationship":
                payload = {"reason": arguments.get("reason", "")}
                if arguments.get("relationship_delta") is not None:
                    payload["relationship_delta"] = arguments["relationship_delta"]
                if arguments.get("proactiveness_delta") is not None:
                    payload["proactiveness_delta"] = arguments["proactiveness_delta"]
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/drive/update",
                    json=payload
                )
                return self._handle_response(response)
            
            elif tool_name == "memory_update":
                target = arguments.get("target", "memory")
                content = arguments.get("content")
                append_content = arguments.get("append")
                reason = arguments.get("reason", "")
                
                # 确定要更新的字段
                field = "memory_md" if target == "memory" else "user_md"
                
                # 如果是 append 模式，先获取现有内容
                final_content = content
                if append_content and not content:
                    # 获取现有内容
                    try:
                        drive_resp = await client.get(
                            f"/api/agents/{self.agent_id}/bootstrap-files"
                        )
                        if drive_resp.status_code == 200:
                            drive_data = drive_resp.json()
                            current = drive_data.get(field, "")
                            final_content = (current + "\n\n" + append_content) if current else append_content
                        else:
                            final_content = append_content
                    except Exception as e:
                        logger.warning(f"[ToolExecutor] Failed to get current {field}: {e}")
                        final_content = append_content
                
                if not final_content:
                    return {"success": False, "error": "Either 'content' or 'append' must be provided"}
                
                # 调用 API 更新
                response = await client.post(
                    f"/api/agents/{self.agent_id}/bootstrap-files",
                    json={field: final_content}
                )
                
                result = self._handle_response(response)
                if result.get("success"):
                    result["target"] = target
                    result["field"] = field
                    result["reason"] = reason
                    result["content_length"] = len(final_content)
                    logger.info(f"[ToolExecutor] memory_update: updated {field} for agent {self.agent_id}, length={len(final_content)}, reason={reason}")
                
                return result
            
            # ==================== 四象限任务管理工具 ====================
            elif tool_name == "task_create":
                # 创建四象限任务
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/quadrant-tasks",
                    json={
                        "title": arguments.get("title"),
                        "quadrant": arguments.get("quadrant"),
                        "source": arguments.get("source"),
                        "description": arguments.get("description"),
                        "reasoning": arguments.get("reasoning"),
                        "due_date": arguments.get("due_date"),
                        "context": arguments.get("context"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "task_complete":
                # 完成任务
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/quadrant-tasks/{task_id}/complete",
                    json={
                        "notes": arguments.get("notes"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "task_update":
                # 更新任务
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                payload = {}
                for key in ("status", "quadrant", "title", "due_date"):
                    val = arguments.get(key)
                    if val is not None:
                        payload[key] = val
                response = await client.patch(
                    f"/internal/rt/{self.runtime_id}/quadrant-tasks/{task_id}",
                    json=payload
                )
                return self._handle_response(response)
            
            elif tool_name == "task_board_list":
                # 列出任务板上的任务
                params = {}
                if arguments.get("quadrant"):
                    params["quadrant"] = arguments["quadrant"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("limit"):
                    params["limit"] = arguments["limit"]
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/quadrant-tasks",
                    params=params,
                )
                return self._handle_response(response)
            
            elif tool_name == "task_delete":
                # 删除任务
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                response = await client.delete(
                    f"/internal/rt/{self.runtime_id}/quadrant-tasks/{task_id}"
                )
                return self._handle_response(response)
            
            elif tool_name == "task_start":
                # 开始执行任务
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/quadrant-tasks/{task_id}/start"
                )
                return self._handle_response(response)
            
            elif tool_name == "task_progress":
                # 记录任务进展
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                # 兼容 LLM 可能使用的不同参数名
                note = arguments.get("note") or arguments.get("progress_notes") or arguments.get("progress") or ""
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/quadrant-tasks/{task_id}/progress",
                    json={
                        "note": note,
                        "set_ongoing": arguments.get("set_ongoing", False),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "drive_log_growth":
                # 记录成长日志
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/growth-logs",
                    json={
                        "content": arguments.get("content"),
                        "category": arguments.get("category", "learning"),
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
                # 兼容 target_runtime_id（schema 定义）和 runtime_id（旧用法）
                target_runtime_id = arguments.get("target_runtime_id") or arguments.get("runtime_id") or self.runtime_id
                response = await client.post(
                    f"/internal/runtimes/{target_runtime_id}/history",
                    json={
                        "limit": arguments.get("limit", 50),
                        "offset": arguments.get("offset", 0),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "runtime_send":
                # 兼容 target_runtime_id（schema 定义）和 runtime_id（旧用法）
                target_runtime_id = arguments.get("target_runtime_id") or arguments.get("runtime_id") or self.runtime_id
                response = await client.post(
                    f"/internal/runtimes/{target_runtime_id}/send",
                    json={"message": arguments.get("message", "")}
                )
                return self._handle_response(response)
            
            elif tool_name == "runtime_rest":
                # Both Main Runtime and SubAgent can call rest
                # Main Runtime: enters rest state and waits for user response
                # SubAgent: completes its task and reports back to parent
                response = await client.post(
                    f"/internal/runtimes/{self.runtime_id}/rest",
                    json={
                        "reason": arguments.get("reason", "Agent requested rest"),
                        "wake_triggers": arguments.get("wake_triggers", [{"type": "user_response"}]),
                        "handoff_notes": arguments.get("handoff_notes"),
                        "rest_duration_minutes": arguments.get("rest_duration_minutes", 30),
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
                # 兼容 message 和 content 两种参数名（有些 LLM 会用 content）
                message = (arguments.get("message") or arguments.get("content") or "").strip()
                
                # HEARTBEAT_OK 协议：如果消息是 HEARTBEAT_OK，静默完成不发送给用户
                if message == "HEARTBEAT_OK" or message.startswith("HEARTBEAT_OK"):
                    logger.info(f"[ToolExecutor] HEARTBEAT_OK received for runtime {self.runtime_id}, silent completion")
                    return {
                        "success": True,
                        "silent": True,
                        "message": "Heartbeat acknowledged. No message sent to user."
                    }
                
                # 空消息校验：拒绝发送空消息
                if not message:
                    logger.warning(f"[ToolExecutor] chat_reply called with empty message for runtime {self.runtime_id}")
                    return {
                        "success": False,
                        "error": "message 不能为空。请提供要回复给用户的内容。"
                    }
                
                # 正常发送回复消息
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/chat/event",
                    json={
                        "type": "AGENT_REPLY",
                        "data": {
                            "message": message,
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
                # 兼容 task 和 prompt 参数（部分 LLM 可能使用 prompt）
                task_desc = arguments.get("task") or arguments.get("prompt", "")
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/subagent/spawn",
                    json={
                        "task": task_desc,
                        "share_context": arguments.get("share_context", False),
                        "timeout_minutes": arguments.get("timeout_minutes", 30),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "subagent_query":
                # 兼容 target_subagent_id（schema 定义）和 subagent_id（旧用法）
                target_subagent_id = arguments.get("target_subagent_id") or arguments.get("subagent_id")
                if not target_subagent_id:
                    return {"success": False, "error": "target_subagent_id is required"}
                response = await client.get(
                    f"/internal/rt/{self.runtime_id}/subagent/{target_subagent_id}/status"
                )
                return self._handle_response(response)
            
            elif tool_name == "subagent_cancel":
                # 兼容 target_subagent_id（schema 定义）和 subagent_id（旧用法）
                target_subagent_id = arguments.get("target_subagent_id") or arguments.get("subagent_id")
                if not target_subagent_id:
                    return {"success": False, "error": "target_subagent_id is required"}
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/subagent/{target_subagent_id}/cancel"
                )
                return self._handle_response(response)
            
            elif tool_name == "subagent_report":
                # 校验是 Sub SubAgent
                if not self.subagent_id or not self.subagent_id.startswith("sub-"):
                    return {
                        "success": False,
                        "error": "subagent_report is only available for Sub SubAgents"
                    }
                
                result = arguments.get("result")
                if not result:
                    return {"success": False, "error": "result is required"}
                
                response = await client.post(
                    f"/internal/rt/{self.runtime_id}/subagent/report",
                    json={"result": result}
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
                result = self._handle_response(response)
                
                # 转换为新格式
                if not result.get("success"):
                    # 错误情况
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown error"),
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False)
                            }
                        ]
                    }
                
                # 成功情况 - 转换为新格式
                # web_fetch 返回的内容可能很大
                return {
                    "success": True,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False)
                        }
                    ]
                }
            
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
            
            # ==================== Mobile 工具（通过 vmcontrol 访问 Android 设备）====================
            elif tool_name in MOBILE_TOOL_MAPPING:
                # 获取 agent 的 Android 设备 serial
                try:
                    agent_response = await client.get(f"{GATEWAY_URL}/internal/agents/{self.agent_id}")
                    agent_data = agent_response.json()
                    device_serial = agent_data.get("android", {}).get("device_serial")
                    if not device_serial:
                        return {"success": False, "error": "No Android device configured for this agent"}
                except Exception as e:
                    logger.warning(f"[ToolExecutor] Could not get agent Android config: {e}")
                    return {"success": False, "error": f"Failed to get Android config: {e}"}
                
                # 调用 vmcontrol Mobile API
                # MOBILE_TOOL_MAPPING 格式: (endpoint, None)
                endpoint, _ = MOBILE_TOOL_MAPPING[tool_name]
                url = f"{VMCONTROL_URL}/api/android/{device_serial}/{endpoint}"
                
                logger.info(f"[ToolExecutor] Calling Mobile API: {url}")
                
                try:
                    # Mobile 工具也使用无超时限制，由心跳机制管理
                    async with httpx.AsyncClient(timeout=None, trust_env=False) as mobile_client:
                        # mobile_app_list 和 mobile_file_list 使用 GET 方法，其他使用 POST
                        if tool_name in ("mobile_app_list", "mobile_file_list"):
                            response = await mobile_client.get(url, params=arguments)
                        else:
                            response = await mobile_client.post(url, json=arguments)
                        response.raise_for_status()
                        mobile_result = response.json()
                    
                    # 检查是否成功
                    is_success = (
                        mobile_result.get("success") is True or
                        mobile_result.get("status") == "success"
                    )
                    
                    if not is_success:
                        error_msg = mobile_result.get("error", "Unknown Mobile API error")
                        logger.error(f"[ToolExecutor] Mobile API error for {tool_name}: {error_msg}")
                        return {
                            "success": False,
                            "error": error_msg,
                        }
                    
                    # 统一 success 字段
                    mobile_result["success"] = True
                    mobile_result.pop("status", None)
                    
                    return mobile_result
                
                except httpx.HTTPStatusError as e:
                    error_text = e.response.text if e.response else str(e)
                    logger.error(f"[ToolExecutor] Mobile API HTTP error for {tool_name}: {e.response.status_code} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Mobile API error: {e.response.status_code}",
                    }
                except Exception as e:
                    logger.error(f"[ToolExecutor] Mobile API request failed for {tool_name}: {e}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"Mobile API request failed: {str(e)}",
                    }
            
            # ==================== VM 工具（通过 vmcontrol 代理访问）====================
            elif tool_name in VM_TOOL_MAPPING:
                # 从映射表获取 tool 和 operation
                tool, operation = VM_TOOL_MAPPING[tool_name]
                
                # 通过 vmcontrol 代理访问 VM 的 VMUSE 服务
                # vmcontrol 会自动从 Gateway 获取端口并转发
                url = f"{VMCONTROL_URL}/api/vmuse/{self.agent_id}/{tool}/{operation}"
                
                logger.info(f"[ToolExecutor] Calling VMUSE via vmcontrol: {url}")
                
                try:
                    # VMUSE 工具也使用无超时限制，由心跳机制管理
                    async with httpx.AsyncClient(timeout=None, trust_env=False) as vmuse_client:
                        response = await vmuse_client.post(url, json=arguments)
                        response.raise_for_status()
                        vm_result = response.json()
                    
                    # VMUSE 返回格式转换为 MCP 标准格式
                    # 可能的格式：
                    # 1. {"status": "success", "data": "base64..."} (旧格式)
                    # 2. {"success": true, "screenshot": "base64...", ...} (新格式)
                    
                    # 检查是否成功
                    is_success = (
                        vm_result.get("success") is True or
                        vm_result.get("status") == "success"
                    )
                    
                    if not is_success:
                        error_msg = vm_result.get("error", "Unknown VMUSE error")
                        logger.error(f"[ToolExecutor] VMUSE error for {tool_name}: {error_msg}")
                        return {
                            "success": False,
                            "error": error_msg,
                        }
                    
                    # 转换旧格式 {"data": "..."} -> {"screenshot": "..."}
                    if "data" in vm_result and "screenshot" not in vm_result:
                        # 检测是否是图片数据（base64）
                        data_value = vm_result.get("data", "")
                        if isinstance(data_value, str) and len(data_value) > 100:
                            vm_result["screenshot"] = data_value
                            # 移除旧字段
                            vm_result.pop("data", None)
                    
                    # 统一 success 字段
                    vm_result["success"] = True
                    vm_result.pop("status", None)
                    
                    return vm_result
                
                except httpx.HTTPStatusError as e:
                    error_text = e.response.text if e.response else str(e)
                    logger.error(f"[ToolExecutor] VMUSE HTTP error for {tool_name}: {e.response.status_code} - {error_text}")
                    # 502 = vmcontrol 无法连接 VM 内 VMUSE（服务未部署/未就绪）
                    if e.response.status_code == 502:
                        err_msg = "VMUSE 服务未就绪，正在部署中，请稍后重试"
                    else:
                        err_msg = f"VMUSE HTTP error: {e.response.status_code}"
                    return {
                        "success": False,
                        "error": err_msg,
                        "content": []
                    }
                except Exception as e:
                    logger.error(f"[ToolExecutor] VMUSE request failed for {tool_name}: {e}", exc_info=True)
                    return {
                        "success": False,
                        "error": f"VMUSE request failed: {str(e)}",
                        "content": []
                    }
            
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
