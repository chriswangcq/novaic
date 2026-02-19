"""
Tool Executor - 执行工具调用

负责执行内置工具和外部工具的调用。

内置工具：直接调用 Gateway / RO / vmcontrol API（使用 httpx.AsyncClient）
外部工具：通过 MCPServerConnection 调用

工具路由规则（ migrated from /internal/rt/* ):
- memory_save, memory_delete: POST /internal/agents/{agent_id}/memory/* (Gateway)
- notebook_* 工具: POST /internal/agents/{agent_id}/notebook/* (Gateway)
- runtime_* 工具: GET/POST RO /internal/runtimes/* (Runtime Orchestrator)
- chat_history, chat_reply: POST /internal/messages, GET /internal/chat/history (Gateway)
- subagent_* 工具: RO /internal/subagents/{agent_id}/{subagent_id}/* (Runtime Orchestrator)
- quadrant tasks: Gateway /internal/subagents/{subagent_id}/quadrant-tasks/*
- qemu_ssh_exec, qemu_status: vmcontrol /api/vms/{agent_id}/* (direct vmcontrol)

特殊工具：
- runtime_rest: 只有 Main Runtime 可以调用
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union

import httpx

from common.config import ServiceConfig
from common.http.clients import internal_async_client
from common.tools.definitions import BUILTIN_TOOLS as DEFINITION_BUILTIN_TOOLS
from .tool_result_adapter import adapt_tool_result as _adapt_tool_result, tool_result as _tool_result, filename_from_url as _filename_from_url
from .reliability import ToolsReliabilityPolicy, get_tools_reliability_policy

if TYPE_CHECKING:
    from mcp_client.mcp_client import MCPServerConnection
    from tools_server.runtime_manager import RuntimeContext, RuntimeManager

logger = logging.getLogger(__name__)

# Gateway API 基础 URL
GATEWAY_URL = ServiceConfig.GATEWAY_URL

# Runtime Orchestrator URL (owns /internal/runtimes*, /internal/subagents*)
RO_URL = getattr(ServiceConfig, "RUNTIME_ORCHESTRATOR_URL", None)

# vmcontrol API 基础 URL
VMCONTROL_URL = ServiceConfig.VMCONTROL_URL

# File Service URL（用于 mobile_file_push/pull、截图存储等）
FILE_SERVICE_URL = ServiceConfig.FILE_SERVICE_URL.rstrip("/")


# _tool_result 和 _filename_from_url 从 tool_result_adapter 导入




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
    "mobile_app_launch": ("app/launch", None),
    "mobile_app_list": ("app/list", None),
    # Phase 3 - UI Automation
    "mobile_ui_dump": ("ui/dump", None),
    "mobile_ui_find": ("ui/find", None),
    # Phase 3 - File Management
    "mobile_file_push": ("file/push", None),
    "mobile_file_pull": ("file/pull", None),
    "mobile_file_list": ("file/list", None),
}

# VM 工具映射表：工具名 -> (tool, operation)
# 这些工具会被路由到 vmcontrol 的 /api/vmuse/:agent_id/:tool/:operation
VM_TOOL_MAPPING = {
    # Browser tools
    "browser_navigate": ("browser", "navigate"),
    "browser_click": ("browser", "click"),
    "browser_type": ("browser", "type"),
    "browser_screenshot": ("browser", "screenshot"),
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
    # Window tools
    "list_windows": ("window", "list"),
    "focus_window": ("window", "focus"),
    "launch_app": ("window", "launch_app"),
    # Context tools
    "system_snapshot": ("context", "system_snapshot"),
    "directory_snapshot": ("context", "directory_snapshot"),
    "clipboard_get": ("context", "clipboard_get"),
    "clipboard_set": ("context", "clipboard_set"),
}

def _collect_defined_tool_names() -> set[str]:
    names: set[str] = set()
    for tools in DEFINITION_BUILTIN_TOOLS.values():
        for tool in tools:
            name = tool.get("name")
            if name:
                names.add(name)
    return names


# Single source of truth for public builtin tools.
DEFINED_BUILTIN_TOOL_NAMES = _collect_defined_tool_names()

# Internal/backward-compatible builtin tools that are intentionally not exposed
# in common.tools.definitions yet.
INTERNAL_ONLY_BUILTIN_TOOL_NAMES = set()
# Intentionally empty after removing all internal-only builtins.

BUILTIN_TOOL_NAMES = DEFINED_BUILTIN_TOOL_NAMES | INTERNAL_ONLY_BUILTIN_TOOL_NAMES


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
        reliability_policy: Optional[ToolsReliabilityPolicy] = None,
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
        self._reliability_policy = reliability_policy or get_tools_reliability_policy()
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端（Gateway）"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = internal_async_client(
                base_url=GATEWAY_URL,
                timeout=httpx.Timeout(connect=10.0, read=None, write=30.0, pool=10.0),
                transport=httpx.AsyncHTTPTransport(proxy=None),
            )
        return self._http_client

    def _get_ro_client(self):
        """Returns RO AsyncClient (context manager). /internal/runtimes* must target RO."""
        if not RO_URL:
            raise RuntimeError("RUNTIME_ORCHESTRATOR_URL is not configured for tools-server")
        return internal_async_client(
            base_url=RO_URL,
            timeout=httpx.Timeout(connect=10.0, read=None, write=30.0, pool=10.0),
            transport=httpx.AsyncHTTPTransport(proxy=None),
        )
    
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
        timeout_seconds = self._reliability_policy.resolve_execution_timeout(tool_name, arguments)
        try:
            if timeout_seconds is not None:
                result = await asyncio.wait_for(
                    self._execute_impl(tool_name, arguments),
                    timeout=timeout_seconds,
                )
            else:
                result = await self._execute_impl(tool_name, arguments)
            return result
        except asyncio.TimeoutError:
            logger.warning(
                "[ToolExecutor] Tool execution timed out: %s (timeout=%ss)",
                tool_name,
                timeout_seconds,
            )
            # Ensure client connections are not leaked after cancellation.
            await self.close()
            return {
                "success": False,
                "error": f"Tool execution timeout after {timeout_seconds:.1f}s",
            }
        except Exception as e:
            logger.error(f"[ToolExecutor] Failed to execute {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_impl(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name in BUILTIN_TOOL_NAMES:
            return await self._execute_builtin(tool_name, arguments)

        result = await self._execute_external(tool_name, arguments)
        # MCP/外部工具：尝试将 content/_mcp_content 中的 base64 转为 URL
        if result.get("success"):
            adapted = await _adapt_tool_result(tool_name, result, self.agent_id)
            if adapted is not None:
                result = adapted
        return result
    
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
            # ==================== Memory 工具 (Gateway /internal/agents/{agent_id}/memory/*) ====================
            if tool_name == "memory_save":
                response = await client.post(
                    f"/internal/agents/{self.agent_id}/memory/save",
                    json={
                        "key": arguments.get("key"),
                        "value": arguments.get("value"),
                        "namespace": arguments.get("namespace", "default"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "memory_delete":
                response = await client.post(
                    f"/internal/agents/{self.agent_id}/memory/delete",
                    json={
                        "key": arguments.get("key"),
                        "namespace": arguments.get("namespace", "default"),
                    }
                )
                return self._handle_response(response)
            
            # ==================== Notebook 工具 (Gateway /internal/agents/{agent_id}/notebook/*) ====================
            elif tool_name == "notebook_write":
                response = await client.post(
                    f"/internal/agents/{self.agent_id}/notebook/write",
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
                    f"/internal/agents/{self.agent_id}/notebook/list",
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
                    f"/internal/agents/{self.agent_id}/notebook/read",
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
                    f"/internal/agents/{self.agent_id}/notebook/update",
                    json=payload
                )
                return self._handle_response(response)
            
            # ==================== 四象限任务管理工具 (Gateway /internal/subagents/{subagent_id}/quadrant-tasks/*) ====================
            elif tool_name == "task_create":
                if not self.subagent_id:
                    return {"success": False, "error": "subagent_id is required for quadrant tasks"}
                response = await client.post(
                    f"/internal/subagents/{self.subagent_id}/quadrant-tasks",
                    json={
                        "title": arguments.get("title"),
                        "task_type": arguments.get("task_type", "one_time"),
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
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                if not self.subagent_id:
                    return {"success": False, "error": "subagent_id is required for quadrant tasks"}
                response = await client.post(
                    f"/internal/subagents/{self.subagent_id}/quadrant-tasks/{task_id}/complete",
                    json={"notes": arguments.get("notes")}
                )
                return self._handle_response(response)
            
            elif tool_name == "task_update":
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                if not self.subagent_id:
                    return {"success": False, "error": "subagent_id is required for quadrant tasks"}
                payload = {k: v for k, v in (("status", arguments.get("status")), ("quadrant", arguments.get("quadrant")), ("title", arguments.get("title")), ("due_date", arguments.get("due_date"))) if v is not None}
                response = await client.patch(
                    f"/internal/subagents/{self.subagent_id}/quadrant-tasks/{task_id}",
                    json=payload or {}
                )
                return self._handle_response(response)
            
            elif tool_name == "task_board_list":
                if not self.subagent_id:
                    return {"success": False, "error": "subagent_id is required for quadrant tasks"}
                params = {}
                if arguments.get("quadrant"):
                    params["quadrant"] = arguments["quadrant"]
                if arguments.get("status"):
                    params["status"] = arguments["status"]
                if arguments.get("limit"):
                    params["limit"] = arguments["limit"]
                response = await client.get(
                    f"/internal/subagents/{self.subagent_id}/quadrant-tasks",
                    params=params,
                )
                return self._handle_response(response)
            
            elif tool_name == "task_delete":
                task_id = arguments.get("task_id")
                if not task_id:
                    return {"success": False, "error": "task_id is required"}
                if not self.subagent_id:
                    return {"success": False, "error": "subagent_id is required for quadrant tasks"}
                response = await client.delete(
                    f"/internal/subagents/{self.subagent_id}/quadrant-tasks/{task_id}"
                )
                return self._handle_response(response)
            
            # ==================== Runtime 工具 (RO /internal/runtimes/*) ====================
            elif tool_name == "runtime_list":
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.get("/internal/runtimes/list")
                return self._handle_response(response)
            
            elif tool_name == "runtime_history":
                target_runtime_id = arguments.get("target_runtime_id") or arguments.get("runtime_id") or self.runtime_id
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.post(
                        f"/internal/runtimes/{target_runtime_id}/history",
                        json={
                            "limit": arguments.get("limit", 50),
                            "offset": arguments.get("offset", 0),
                        }
                    )
                return self._handle_response(response)
            
            elif tool_name == "runtime_send":
                target_runtime_id = arguments.get("target_runtime_id") or arguments.get("runtime_id") or self.runtime_id
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.post(
                        f"/internal/runtimes/{target_runtime_id}/send",
                        json={"message": arguments.get("message", "")}
                    )
                return self._handle_response(response)
            
            elif tool_name == "runtime_rest":
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.post(
                        f"/internal/runtimes/{self.runtime_id}/rest",
                        json={
                            "reason": arguments.get("reason", "Agent requested rest"),
                            "wake_triggers": arguments.get("wake_triggers", [{"type": "user_response"}]),
                            "handoff_notes": arguments.get("handoff_notes"),
                            "rest_duration_minutes": arguments.get("rest_duration_minutes", 30),
                        }
                    )
                return self._handle_response(response)
            
            # ==================== Chat 工具 (Gateway /internal/messages, /internal/chat/history) ====================
            elif tool_name == "chat_history":
                limit = arguments.get("limit", 20)
                response = await client.get(
                    "/internal/chat/history",
                    params={"agent_id": self.agent_id, "limit": limit},
                )
                return self._handle_response(response)
            
            elif tool_name == "chat_reply":
                message = (arguments.get("message") or arguments.get("content") or "").strip()
                if message == "HEARTBEAT_OK" or message.startswith("HEARTBEAT_OK"):
                    logger.info(f"[ToolExecutor] HEARTBEAT_OK received for runtime {self.runtime_id}, silent completion")
                    return {"success": True, "silent": True, "message": "Heartbeat acknowledged. No message sent to user."}
                if not message:
                    logger.warning(f"[ToolExecutor] chat_reply called with empty message for runtime {self.runtime_id}")
                    return {"success": False, "error": "message 不能为空。请提供要回复给用户的内容。"}
                response = await client.post(
                    "/internal/messages",
                    json={
                        "agent_id": self.agent_id,
                        "type": "AGENT_REPLY",
                        "content": message,
                        "metadata": {"attachments": arguments.get("attachments", [])},
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "display":
                # Display: 将 File Service 中的文件引用加入 LLM 上下文
                file_url = (arguments.get("file_url") or "").strip()
                if not file_url:
                    return {"success": False, "error": "file_url is required"}
                modality = (arguments.get("modality") or "").lower() or "image"
                # 支持 /api/files/...、api/files/...、完整 http URL
                if file_url.startswith("http://") or file_url.startswith("https://"):
                    fetch_url = file_url
                elif file_url.startswith("/"):
                    fetch_url = f"{FILE_SERVICE_URL}{file_url}"
                else:
                    fetch_url = f"{FILE_SERVICE_URL}/{file_url.lstrip('/')}"
                try:
                    async with internal_async_client(timeout=30.0) as client:
                        # 用 GET 检查文件是否存在（stream=True 避免下载全部内容）
                        async with client.stream("GET", fetch_url) as resp:
                            resp.raise_for_status()
                except Exception as e:
                    logger.warning(f"[ToolExecutor] display: file not found or inaccessible: {e}")
                    return {"success": False, "error": f"File not found or inaccessible: {e}"}
                raw_name = file_url.split("/")[-1] if "/" in file_url else file_url
                filename = raw_name.split("?")[0] if "?" in raw_name else raw_name or "file"
                file_ref = {"url": file_url, "filename": filename, "modality": modality}
                # display: 不创建文件，只展示
                return _tool_result(
                    text=f"Displaying file: {filename}.",
                    files_created=[],
                    display_files=[file_ref],
                )
            # ==================== SubAgent 工具 (RO /internal/subagents/{agent_id}/{subagent_id}/*) ====================
            elif tool_name == "subagent_spawn":
                task_desc = arguments.get("task") or arguments.get("prompt", "")
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.post(
                        f"/internal/subagents/{self.agent_id}/spawn",
                        json={
                            "parent_subagent_id": self.subagent_id or "main",
                            "task": task_desc,
                            "share_context": arguments.get("share_context", False),
                            "timeout_minutes": arguments.get("timeout_minutes", 30),
                        }
                    )
                return self._handle_response(response)
            
            elif tool_name == "subagent_query":
                target_subagent_id = arguments.get("target_subagent_id") or arguments.get("subagent_id")
                if not target_subagent_id:
                    return {"success": False, "error": "target_subagent_id is required"}
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.get(
                        f"/internal/subagents/{self.agent_id}/{target_subagent_id}/status"
                    )
                return self._handle_response(response)
            
            elif tool_name == "subagent_cancel":
                target_subagent_id = arguments.get("target_subagent_id") or arguments.get("subagent_id")
                if not target_subagent_id:
                    return {"success": False, "error": "target_subagent_id is required"}
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.post(
                        f"/internal/subagents/{self.agent_id}/{target_subagent_id}/cancel"
                    )
                return self._handle_response(response)
            
            elif tool_name == "subagent_report":
                if not self.subagent_id or not self.subagent_id.startswith("sub-"):
                    return {"success": False, "error": "subagent_report is only available for Sub SubAgents"}
                result = arguments.get("result")
                if not result:
                    return {"success": False, "error": "result is required"}
                async with self._get_ro_client() as ro_client:
                    response = await ro_client.post(
                        f"/internal/subagents/{self.agent_id}/{self.subagent_id}/completed",
                        json={"result": result}
                    )
                return self._handle_response(response)
            
            # ==================== QEMU 工具 (vmcontrol /api/vms/{agent_id}/*, Gateway /api/vm/*) ====================
            elif tool_name == "qemu_ssh_exec":
                async with internal_async_client(base_url=VMCONTROL_URL, timeout=httpx.Timeout(arguments.get("timeout", 30) + 5)) as vmc:
                    response = await vmc.post(
                        f"/api/vms/{self.agent_id}/guest/exec",
                        json={
                            "path": "/bin/bash",
                            "args": ["-c", arguments.get("command", "")],
                            "wait": True,
                        }
                    )
                data = response.json()
                ok = response.status_code == 200 and data.get("success", "error" not in data)
                out = {
                    "success": ok,
                    "exit_code": data.get("exit_code", -1),
                    "stdout": data.get("stdout", ""),
                    "stderr": data.get("stderr", ""),
                    "command": arguments.get("command", ""),
                }
                if not ok and data.get("error"):
                    out["error"] = data["error"]
                return out
            
            elif tool_name == "qemu_status":
                try:
                    async with internal_async_client(base_url=VMCONTROL_URL, timeout=10.0) as vmc:
                        response = await vmc.get(f"/api/vms/{self.agent_id}")
                    if response.status_code != 200:
                        return {"success": False, "error": f"vmcontrol returned {response.status_code}"}
                    vm_info = response.json()
                    if vm_info.get("success") is False:
                        return {"success": False, "error": vm_info.get("error", "vmcontrol error")}
                    status = (vm_info.get("status") or "").lower()
                    return {
                        "success": True,
                        "qemu_running": status in ("running", "started", "active"),
                        "qemu_pid": vm_info.get("pid"),
                        "agent_id": self.agent_id,
                    }
                except Exception as e:
                    return {"success": False, "error": f"vmcontrol unavailable: {e}"}
            
            # ==================== Task 工具 (Gateway /internal/agents/{agent_id}/memory/task/*) ====================
            elif tool_name == "task_log":
                response = await client.post(
                    f"/internal/agents/{self.agent_id}/memory/task/log",
                    json={
                        "action": arguments.get("action"),
                        "details": arguments.get("details"),
                        "status": arguments.get("status", "completed"),
                    }
                )
                return self._handle_response(response)
            
            elif tool_name == "task_history":
                response = await client.post(
                    f"/internal/agents/{self.agent_id}/memory/task/history",
                    json={
                        "limit": arguments.get("limit", 20),
                        "status_filter": arguments.get("status_filter"),
                    }
                )
                return self._handle_response(response)
            
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
                
                # ===== mobile_file_pull: 拉取到 File Service，返回 file_url 供后续 push 使用 =====
                if tool_name == "mobile_file_pull":
                    remote_path = arguments.get("remote_path")
                    if not remote_path:
                        return {"success": False, "error": "remote_path is required"}
                    try:
                        async with internal_async_client(timeout=None) as mobile_client:
                            response = await mobile_client.post(
                                f"{VMCONTROL_URL}/api/android/{device_serial}/file/pull-content",
                                json={"remote_path": remote_path},
                            )
                            response.raise_for_status()
                            data = response.json()
                        if not data.get("success") or not data.get("content"):
                            return {"success": False, "error": data.get("message", "Pull failed or empty file")}
                        # 直接存入 File Service
                        content = data["content"]
                        mime_type = data.get("mime_type", "application/octet-stream")
                        size = data.get("size", 0)
                        async with internal_async_client(timeout=None) as fs_client:
                            fs_resp = await fs_client.post(
                                f"{FILE_SERVICE_URL}/api/files/from-base64",
                                json={
                                    "data": content,
                                    "agent_id": self.agent_id,
                                    "category": "binaries",
                                    "mime_type": mime_type,
                                },
                            )
                            fs_resp.raise_for_status()
                            fs_result = fs_resp.json()
                        file_url = fs_result.get("url", "")
                        filename = _filename_from_url(file_url)
                        modality = "image" if (mime_type or "").startswith("image/") else "resource"
                        file_ref = {"url": file_url, "filename": filename, "modality": modality}
                        # mobile_file_pull: 创建文件，不展示（仅传输用途）
                        return _tool_result(
                            text=f"File pulled: {filename} ({size} bytes). Use file_url for mobile_file_push.",
                            files_created=[file_ref],
                            display_files=[],
                            extra={"size": size},
                        )
                    except Exception as e:
                        logger.error(f"[ToolExecutor] mobile_file_pull failed: {e}", exc_info=True)
                        return {"success": False, "error": str(e)}
                
                # ===== mobile_app_install: 从 File Service 拉取 APK 后安装 =====
                if tool_name == "mobile_app_install":
                    file_url = arguments.get("file_url")
                    allow_downgrade = arguments.get("allow_downgrade", False)
                    if not file_url:
                        return {"success": False, "error": "file_url is required"}
                    fetch_url = f"{FILE_SERVICE_URL}{file_url}" if file_url.startswith("/") else file_url
                    try:
                        async with internal_async_client(timeout=None) as fs_client:
                            resp = await fs_client.get(fetch_url)
                            resp.raise_for_status()
                            file_bytes = resp.content
                        import base64
                        b64_data = base64.b64encode(file_bytes).decode("utf-8")
                        async with internal_async_client(timeout=None) as mobile_client:
                            response = await mobile_client.post(
                                f"{VMCONTROL_URL}/api/android/{device_serial}/app/install-from-base64",
                                json={"data": b64_data, "allow_downgrade": allow_downgrade},
                            )
                            response.raise_for_status()
                            data = response.json()
                        # mobile_app_install: 不创建文件，不展示
                        return _tool_result(
                            text=data.get("message", "APK installed."),
                            extra={k: v for k, v in data.items() if k not in ("success", "message")},
                        )
                    except Exception as e:
                        logger.error(f"[ToolExecutor] mobile_app_install failed: {e}", exc_info=True)
                        return {"success": False, "error": str(e)}
                
                # ===== mobile_file_push: 从 File Service 拉取后推送 =====
                if tool_name == "mobile_file_push":
                    file_url = arguments.get("file_url")
                    remote_path = arguments.get("remote_path")
                    if not file_url or not remote_path:
                        return {"success": False, "error": "file_url and remote_path are required"}
                    
                    # 解析 file_url：支持 /api/files/xxx 或完整 URL
                    if file_url.startswith("/"):
                        fetch_url = f"{FILE_SERVICE_URL}{file_url}"
                    elif file_url.startswith("http://") or file_url.startswith("https://"):
                        fetch_url = file_url
                    else:
                        # 可能是相对路径或其他格式，尝试作为 File Service 路径
                        fetch_url = f"{FILE_SERVICE_URL}/api/files/{file_url}"
                    
                    logger.info(f"[ToolExecutor] mobile_file_push: fetching file from {fetch_url}")
                    
                    try:
                        # 1. 从 File Service 或 URL 获取文件
                        async with internal_async_client(timeout=httpx.Timeout(600.0)) as fs_client:
                            resp = await fs_client.get(fetch_url)
                            if resp.status_code != 200:
                                logger.error(f"[ToolExecutor] mobile_file_push: failed to fetch file, status={resp.status_code}, body={resp.text[:500]}")
                                return {"success": False, "error": f"Failed to fetch file from {file_url}: HTTP {resp.status_code}"}
                            file_bytes = resp.content
                        
                        file_size_mb = len(file_bytes) / (1024 * 1024)
                        logger.info(f"[ToolExecutor] mobile_file_push: fetched {len(file_bytes)} bytes ({file_size_mb:.2f} MB), pushing to {remote_path}")
                        
                        # 2. 推送到设备
                        import base64
                        b64_data = base64.b64encode(file_bytes).decode("utf-8")
                        b64_size_mb = len(b64_data) / (1024 * 1024)
                        logger.info(f"[ToolExecutor] mobile_file_push: base64 encoded size: {b64_size_mb:.2f} MB, sending to vmcontrol...")
                        
                        async with internal_async_client(timeout=httpx.Timeout(600.0)) as mobile_client:
                            push_url = f"{VMCONTROL_URL}/api/android/{device_serial}/file/push-from-base64"
                            logger.info(f"[ToolExecutor] mobile_file_push: POST to {push_url}")
                            response = await mobile_client.post(
                                push_url,
                                json={"data": b64_data, "remote_path": remote_path},
                            )
                            logger.info(f"[ToolExecutor] mobile_file_push: vmcontrol response status={response.status_code}")
                            if response.status_code != 200:
                                error_body = response.text[:1000] if response.text else "(empty)"
                                logger.error(f"[ToolExecutor] mobile_file_push: push failed, status={response.status_code}, body={error_body}")
                                return {"success": False, "error": f"Push to device failed: HTTP {response.status_code} - {error_body[:200]}"}
                            result = response.json()
                        
                        logger.info(f"[ToolExecutor] mobile_file_push: vmcontrol result={result}")
                        if not result.get("success"):
                            error_msg = result.get("message") or result.get("error") or "Push failed (unknown reason)"
                            logger.error(f"[ToolExecutor] mobile_file_push: vmcontrol returned success=false, error={error_msg}")
                            return {"success": False, "error": error_msg}
                        
                        # mobile_file_push: 不创建文件，不展示
                        return _tool_result(
                            text=result.get("message", f"File pushed to device: {remote_path}"),
                            extra={"bytes_transferred": result.get("bytes_transferred"), "remote_path": remote_path},
                        )
                    except httpx.TimeoutException as e:
                        logger.error(f"[ToolExecutor] mobile_file_push timeout: {e}")
                        return {"success": False, "error": f"Timeout while pushing file: {str(e)}"}
                    except httpx.RequestError as e:
                        logger.error(f"[ToolExecutor] mobile_file_push request error: {e}", exc_info=True)
                        return {"success": False, "error": f"Request error: {str(e)}"}
                    except Exception as e:
                        logger.error(f"[ToolExecutor] mobile_file_push failed: {e}", exc_info=True)
                        return {"success": False, "error": f"Unexpected error: {str(e)}"}
                
                # 调用 vmcontrol Mobile API（通用逻辑）
                # MOBILE_TOOL_MAPPING 格式: (endpoint, None)
                endpoint, _ = MOBILE_TOOL_MAPPING[tool_name]
                url = f"{VMCONTROL_URL}/api/android/{device_serial}/{endpoint}"
                
                logger.info(f"[ToolExecutor] Calling Mobile API: {url}")
                
                try:
                    # Mobile 工具也使用无超时限制，由心跳机制管理
                    async with internal_async_client(timeout=None) as mobile_client:
                        # mobile_app_list 和 mobile_file_list 使用 GET 方法，其他使用 POST
                        if tool_name in ("mobile_app_list", "mobile_file_list"):
                            response = await mobile_client.get(url, params=arguments)
                        else:
                            response = await mobile_client.post(url, json=arguments)
                        response.raise_for_status()
                        mobile_result = response.json()
                    
                    # 检查是否成功
                    # 注意：mobile_shell 的 success 表示 exit_code == 0，但命令本身可能执行成功
                    # 所以对于 mobile_shell，我们总是返回结果，让 Agent 自己判断
                    is_success = (
                        mobile_result.get("success") is True or
                        mobile_result.get("status") == "success"
                    )
                    
                    # mobile_shell 特殊处理：即使 exit_code != 0，也返回结果
                    if tool_name == "mobile_shell":
                        # 总是返回 shell 结果，包含 stdout/stderr/exit_code
                        mobile_result["success"] = True  # 标记工具调用成功
                        return mobile_result
                    
                    if not is_success:
                        error_msg = mobile_result.get("error") or mobile_result.get("message") or "Unknown Mobile API error"
                        logger.error(f"[ToolExecutor] Mobile API error for {tool_name}: {error_msg}")
                        return {
                            "success": False,
                            "error": error_msg,
                        }
                    
                    # 截图类工具：适配层转为 File Service URL
                    adapted = await _adapt_tool_result(tool_name, mobile_result, self.agent_id)
                    if adapted is not None:
                        return adapted
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
            elif tool_name in ("file_pull", "file_push") or tool_name in VM_TOOL_MAPPING:
                # ===== file_pull: VM 路径 → File Service，返回 file_url =====
                if tool_name == "file_pull":
                    path = arguments.get("path")
                    if not path:
                        return {"success": False, "error": "path is required"}
                    try:
                        async with internal_async_client(timeout=None) as vmuse_client:
                            response = await vmuse_client.post(
                                f"{VMCONTROL_URL}/api/vmuse/{self.agent_id}/file/read",
                                json={"path": path},
                            )
                            response.raise_for_status()
                            data = response.json()
                        content_raw = data.get("data") or data.get("content")
                        if content_raw is None and not data.get("success", True):
                            return {"success": False, "error": data.get("error", "Read failed")}
                        if content_raw is None:
                            return {"success": False, "error": "File empty or not found"}
                        import base64
                        content_b64 = base64.b64encode(
                            content_raw.encode("utf-8") if isinstance(content_raw, str) else content_raw
                        ).decode("utf-8")
                        async with internal_async_client(timeout=None) as fs_client:
                            fs_resp = await fs_client.post(
                                f"{FILE_SERVICE_URL}/api/files/from-base64",
                                json={
                                    "data": content_b64,
                                    "agent_id": self.agent_id,
                                    "category": "binaries",
                                    "mime_type": "application/octet-stream",
                                },
                            )
                            fs_resp.raise_for_status()
                            fs_result = fs_resp.json()
                        file_url = fs_result.get("url", "")
                        filename = _filename_from_url(file_url)
                        size = len(content_raw) if isinstance(content_raw, str) else len(content_raw)
                        modality = "image" if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")) else "resource"
                        file_ref = {"url": file_url, "filename": filename, "modality": modality}
                        # file_pull: 创建文件，不展示（仅传输用途）
                        return _tool_result(
                            text=f"File pulled: {filename} ({size} bytes). Use file_url for file_push.",
                            files_created=[file_ref],
                            display_files=[],
                            extra={"size": size},
                        )
                    except Exception as e:
                        logger.error(f"[ToolExecutor] file_pull failed: {e}", exc_info=True)
                        return {"success": False, "error": str(e)}
                
                # ===== file_push: File Service → VM 路径（shell 写入，支持二进制）=====
                if tool_name == "file_push":
                    file_url = arguments.get("file_url")
                    path = arguments.get("path")
                    if not file_url or not path:
                        return {"success": False, "error": "file_url and path are required"}
                    fetch_url = f"{FILE_SERVICE_URL}{file_url}" if file_url.startswith("/") else file_url
                    try:
                        async with internal_async_client(timeout=None) as fs_client:
                            resp = await fs_client.get(fetch_url)
                            resp.raise_for_status()
                            file_bytes = resp.content
                        import base64
                        b64_data = base64.b64encode(file_bytes).decode("ascii")
                        path_escaped = path.replace("'", "'\"'\"'")
                        parent = f"$(dirname '{path_escaped}')"
                        cmd = f"mkdir -p \"{parent}\" && printf '%s' '{b64_data}' | base64 -d > '{path_escaped}'"
                        async with internal_async_client(timeout=60.0) as vmuse_client:
                            response = await vmuse_client.post(
                                f"{VMCONTROL_URL}/api/vmuse/{self.agent_id}/shell/command",
                                json={"command": cmd},
                            )
                            response.raise_for_status()
                            result = response.json()
                        exit_code = result.get("exit_code", 0)
                        if not result.get("success") or (exit_code is not None and exit_code != 0):
                            err = result.get("stderr", "") or result.get("error", "Write failed")
                            return {"success": False, "error": err or f"Exit code {exit_code}"}
                        # file_push: 不创建文件（写入 VM），不展示
                        return _tool_result(
                            text=f"File pushed to VM at {path} ({len(file_bytes)} bytes).",
                            extra={"path": path, "size": len(file_bytes)},
                        )
                    except Exception as e:
                        logger.error(f"[ToolExecutor] file_push failed: {e}", exc_info=True)
                        return {"success": False, "error": str(e)}
                
                # 从映射表获取 tool 和 operation（通用 VM 工具）
                tool, operation = VM_TOOL_MAPPING[tool_name]
                
                # 通过 vmcontrol 代理访问 VM 的 VMUSE 服务
                # vmcontrol 会自动从 Gateway 获取端口并转发
                url = f"{VMCONTROL_URL}/api/vmuse/{self.agent_id}/{tool}/{operation}"
                
                logger.info(f"[ToolExecutor] Calling VMUSE via vmcontrol: {url}")
                
                try:
                    # VMUSE 工具也使用无超时限制，由心跳机制管理
                    async with internal_async_client(timeout=None) as vmuse_client:
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
                    
                    # 转换旧格式 {"data": "..."} -> {"screenshot": "..."}（供适配层识别）
                    if "data" in vm_result and "screenshot" not in vm_result:
                        data_value = vm_result.get("data", "")
                        if isinstance(data_value, str) and len(data_value) > 100:
                            vm_result["screenshot"] = data_value
                            vm_result.pop("data", None)
                    # 截图类工具：适配层转为 File Service URL
                    adapted = await _adapt_tool_result(tool_name, vm_result, self.agent_id)
                    if adapted is not None:
                        return adapted
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
        
        支持 unified contract：operation failures 返回 HTTP 200 + {success: false, error}，
        不依赖 HTTP status 判断成功与否，需解析 body 中的 success 字段。
        
        Args:
            response: httpx Response 对象
        
        Returns:
            解析后的 JSON 响应，或错误 dict
        """
        try:
            response.raise_for_status()
            result = response.json()
            # 确保结果包含 success 字段（unified contract 兼容）
            if "success" not in result:
                result["success"] = "error" not in result
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
