"""
AgentMCPGateway - MCP Gateway for a single Agent

Creates a FastMCP server that aggregates tools from:
- VM MCP server (vmuse) - VM desktop/browser/file operations
- Embedded tools - session, local, memory, chat (run in Gateway process)
- Skills - operation guides as MCP Resources

Architecture:
    AgentMCPGateway (FastMCP)
        ├── VM Tools: Proxied from VM MCP server via ToolRegistry
        ├── Embedded Tools: session, local, memory, chat (no external process)
        ├── Skills: Aggregated as MCP Resources
        ├── task_*: Async task system
        └── agent_*: Agent capabilities
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import partial

from fastmcp import FastMCP

from config.agents import PortConfig, allocate_ports_for_agent
from executor.registry import ToolRegistry

# Skills directory (relative to gateway root)
SKILLS_DIR = Path(__file__).parent.parent / "skills"

logger = logging.getLogger(__name__)


class AgentMCPGateway:
    """
    MCP Gateway for a single Agent.
    
    Aggregates all tools and skills from the agent's sub-MCP servers
    and exposes them through a unified FastMCP interface.
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_index: int,
    ):
        """
        Initialize the MCP Gateway for an agent.
        
        Args:
            agent_id: Unique agent identifier (UUID)
            agent_index: Agent index for port allocation (0, 1, 2, ...)
        """
        self.agent_id = agent_id
        self.agent_index = agent_index
        
        # Allocate ports for this agent
        self.ports = allocate_ports_for_agent(agent_index)
        
        # Create dedicated ToolRegistry for this agent
        self.registry = ToolRegistry()
        self._register_agent_servers()
        
        # Create FastMCP instance
        self.mcp = FastMCP(
            name=f"novaic-agent-{agent_index}",
            instructions=self._build_instructions(),
        )
        
        # Track registered tools and skills
        self._registered_tools: List[str] = []
        self._registered_skills: List[str] = []
        
        logger.info(f"[MCPGateway] Created gateway for agent {agent_id} (index={agent_index})")
    
    def _build_instructions(self) -> str:
        """Build MCP server instructions."""
        return f"""NovAIC Agent Gateway - 统一 MCP 入口

本 Gateway 聚合了所有子 MCP 服务的工具和技能，是 Agent 操作 VM 的唯一入口。

## 核心原则

1. **直接工具**：立即执行，适合 <30s 的操作
2. **task_async**：异步执行，适合 >30s 的长时间操作
3. **agent_call**：委托子代理，适合需要多步推理的复杂任务

## 工具一览

### 桌面操作 (直接)
| 工具 | 用途 | 何时使用 |
|------|------|----------|
| screenshot | 获取屏幕截图 | 需要看屏幕内容时 |
| mouse | 鼠标操作 (点击/移动/滚动) | 与 UI 交互 |
| keyboard | 键盘操作 (输入/快捷键) | 输入文字或使用快捷键 |

### 浏览器自动化 (直接)
| 工具 | 用途 | 何时使用 |
|------|------|----------|
| browser_navigate | 打开 URL | 访问网页 |
| browser_click | CSS 选择器点击 | 比坐标点击更稳定 |
| browser_type | 在元素输入 | 表单填写 |
| browser_screenshot | 浏览器截图 | 网页截图 |

### 文件与命令 (直接/异步)
| 工具 | 用途 | 建议 |
|------|------|------|
| run_command | 执行 shell 命令 | <30s 直接用，否则用 task_async |
| file_read/write | 读写文件 | 直接使用 |
| file_list/search | 浏览文件 | 直接使用 |

### 异步任务系统
| 工具 | 用途 |
|------|------|
| **task_async** | 异步执行任意工具（返回 task_id） |
| **task_query** | 查询任务状态/进度/结果 |
| task_list | 列出所有任务 |
| task_cancel | 取消任务 |
| task_summary | 获取 AI 结果摘要 |

### Agent 能力
| 工具 | 用途 |
|------|------|
| **agent_call** | 同步委托子代理执行复杂任务 |
| agent_context_list | 列出所有上下文 |
| agent_context_history | 查看上下文历史 |
| agent_context_send | 向上下文发消息 |
| agent_inbox | 检查待处理事件 |
| agent_rest | 主动进入休息状态 |

## 使用决策树

```
需要执行操作
├─ 预计 <30 秒？
│   └─ 直接调用工具 (screenshot, run_command, etc.)
├─ 预计 >30 秒？
│   └─ 使用 task_async 包装
│       task_async(tool="run_command", args={{"command": "make"}}, label="编译")
│       稍后用 task_query 检查进度
└─ 需要多步推理/研究？
    └─ 使用 agent_call 委托
        agent_call(task="分析这个代码库的架构")
```

## 自动截断机制

长输出 (>4000字符) 会自动截断并存储，返回结果中包含：
- `xxx_truncated: true` - 表示该字段被截断
- `xxx_task_id: "so_abc..."` - 用于查询完整内容
- 使用 `task_query(task_id="so_abc...", start_line=1, end_line=100)` 分段获取完整内容

## 最佳实践

1. **编译/构建/测试**: task_async + task_query 定期检查
2. **文件下载**: task_async 包装，避免阻塞
3. **研究报告**: agent_call 委托，让子代理深入分析
4. **UI 操作**: screenshot → 分析 → mouse/keyboard 直接操作
5. **长输出**: 自动截断，用 task_query 查看完整内容

## Skills (操作指南)
访问 skill:// 资源获取详细操作指南：
- skill://desktop - 桌面操作详细指南
- skill://browser - 浏览器自动化指南
- skill://software - 常用软件操作
- skill://wechat - 微信操作指南
"""
    
    def _register_agent_servers(self) -> None:
        """Register external MCP servers for this agent.
        
        Only VM server is external now. Session/local/memory/chat are embedded.
        """
        # VM server (runs inside the virtual machine)
        self.registry.register_server("vm", port=self.ports.vm, priority=0)
        
        # QEMU debug server (optional, runs on host)
        qemu_enabled = os.getenv("NOVAIC_MCP_QEMUDEBUG_ENABLED", "false").lower() == "true"
        if qemu_enabled:
            self.registry.register_server("qemudebug", port=self.ports.qemudebug, enabled=True, priority=3)
        
        logger.info(f"[MCPGateway] Registered VM server for agent {self.agent_index}")
    
    async def setup(self) -> None:
        """
        Setup the gateway by discovering and registering all tools and skills.
        
        This must be called before mounting the gateway.
        """
        # Setup aggregated tools from VM server
        await self._setup_tools()
        
        # Setup embedded tools (session, local, memory, chat)
        self._setup_embedded_tools()
        
        # Setup skills as MCP resources
        await self._setup_skills()
        
        # Setup Gateway-specific tools (task_*, agent_*)
        self._setup_task_tools()
        self._setup_agent_tools()
        
        logger.info(
            f"[MCPGateway] Setup complete for agent {self.agent_index}: "
            f"{len(self._registered_tools)} tools, {len(self._registered_skills)} skills"
        )
    
    async def _setup_tools(self) -> None:
        """Discover tools from sub-servers and register them as MCP tools."""
        try:
            tools = await self.registry.discover_all_tools(use_cache=False)
            
            for tool in tools:
                tool_name = tool.get("name", "")
                if not tool_name:
                    continue
                
                # Register proxy tool
                self._register_proxy_tool(tool)
                self._registered_tools.append(tool_name)
            
            logger.info(f"[MCPGateway] Registered {len(self._registered_tools)} aggregated tools")
            
        except Exception as e:
            logger.error(f"[MCPGateway] Failed to setup tools: {e}")
    
    def _register_proxy_tool(self, tool_def: Dict[str, Any]) -> None:
        """Register a proxy tool that forwards calls to the underlying MCP server.
        
        Note: FastMCP doesn't support **kwargs, so we create a function with
        explicit 'args' parameter that accepts a dict of arguments.
        """
        tool_name = tool_def.get("name", "")
        description = tool_def.get("description", "")
        input_schema = tool_def.get("inputSchema", {})
        
        # Create a closure to capture tool_name and self
        gateway = self  # Capture self for async method access
        
        async def proxy_handler(args: Dict[str, Any] = {}) -> Dict[str, Any]:
            """Proxy tool call to underlying MCP server.
            
            Args:
                args: Dictionary of arguments to pass to the underlying tool
            """
            try:
                result = await gateway.registry.execute(tool_name, args)
                # Auto-truncate long outputs (now async)
                return await gateway._auto_truncate_result(result, tool_name)
            except Exception as e:
                logger.error(f"[MCPGateway] Tool {tool_name} failed: {e}")
                return {"success": False, "error": str(e)}
        
        # Set function attributes for FastMCP
        proxy_handler.__name__ = tool_name
        
        # Build description with parameter info from original schema
        params_desc = ""
        if input_schema.get("properties"):
            props = input_schema["properties"]
            required = input_schema.get("required", [])
            params_desc = "\n\nParameters (pass as args dict):\n"
            for prop_name, prop_schema in props.items():
                req_mark = " (required)" if prop_name in required else ""
                prop_type = prop_schema.get("type", "any")
                params_desc += f"- {prop_name}{req_mark}: {prop_type}\n"
        
        proxy_handler.__doc__ = f"{description}{params_desc}"
        
        # Use the @tool decorator pattern
        self.mcp.tool(name=tool_name)(proxy_handler)
    
    async def _auto_truncate_result(self, result: Any, tool_name: str = "") -> Any:
        """
        Auto-truncate long string fields in result and store as sync_output task.
        
        Creates a completed task that can be queried via task_query for full content.
        
        Handles:
        - String results: truncate if > 4000 chars
        - Dict with 'stdout'/'stderr'/'content'/'output' fields: truncate each
        """
        from core.task_manager import get_task_manager
        
        MAX_LENGTH = 4000
        HEAD_LENGTH = 1500
        TAIL_LENGTH = 1500
        
        def truncate_content(content: str, task_id: str) -> str:
            """Truncate content with hint about task_id."""
            head = content[:HEAD_LENGTH]
            tail = content[-TAIL_LENGTH:]
            
            # Try to cut at newline for cleaner output
            if '\n' in head[HEAD_LENGTH//2:]:
                head = head[:head.rfind('\n', HEAD_LENGTH//2) + 1]
            if '\n' in tail[:TAIL_LENGTH//2]:
                tail = tail[tail.find('\n', 0) + 1:]
            
            omitted = len(content) - len(head) - len(tail)
            total_lines = content.count('\n') + 1
            
            return f"""{head}
... [已省略 {omitted} 字符 / 约 {total_lines - head.count(chr(10)) - tail.count(chr(10))} 行] ...
... [任务ID: {task_id}] ...
... [使用 task_query(task_id='{task_id}') 获取完整内容] ...

{tail}"""
        
        task_manager = get_task_manager()
        
        if isinstance(result, str):
            if len(result) > MAX_LENGTH:
                if task_manager:
                    task_id = await task_manager.create_completed(
                        tool_name=tool_name or "unknown",
                        truncated_result="",  # Will be set after we have task_id
                        full_output=result,
                    )
                    truncated = truncate_content(result, task_id)
                    return {
                        "content": truncated,
                        "task_id": task_id,
                        "truncated": True,
                        "total_chars": len(result),
                        "hint": f"输出已截断，用 task_query('{task_id}') 获取完整内容"
                    }
                else:
                    # Fallback: simple truncation without storage
                    return {
                        "content": result[:HEAD_LENGTH] + "\n...[已截断]...\n" + result[-TAIL_LENGTH:],
                        "truncated": True,
                        "total_chars": len(result),
                    }
            return result
        
        if isinstance(result, dict):
            # Fields that commonly contain long outputs
            long_fields = ['stdout', 'stderr', 'content', 'output', 'result', 'body']
            modified = False
            result_copy = result.copy()
            
            for field in long_fields:
                if field in result_copy and isinstance(result_copy[field], str):
                    value = result_copy[field]
                    if len(value) > MAX_LENGTH:
                        if task_manager:
                            task_id = await task_manager.create_completed(
                                tool_name=f"{tool_name or 'unknown'}.{field}",
                                truncated_result="",
                                full_output=value,
                            )
                            result_copy[field] = truncate_content(value, task_id)
                            result_copy[f"{field}_task_id"] = task_id
                            result_copy[f"{field}_truncated"] = True
                            result_copy[f"{field}_total_chars"] = len(value)
                        else:
                            result_copy[field] = value[:HEAD_LENGTH] + "\n...[已截断]...\n" + value[-TAIL_LENGTH:]
                            result_copy[f"{field}_truncated"] = True
                            result_copy[f"{field}_total_chars"] = len(value)
                        modified = True
            
            return result_copy if modified else result
        
        return result
    
    async def _setup_skills(self) -> None:
        """Load skills from local files and register as MCP resources."""
        try:
            if not SKILLS_DIR.exists():
                logger.warning(f"[MCPGateway] Skills directory not found: {SKILLS_DIR}")
                return
            
            # Skill descriptions for better discoverability
            skill_descriptions = {
                "desktop": "Desktop control - screenshot, mouse, keyboard operations",
                "browser": "Browser automation - Playwright-based web operations",
                "context": "Context awareness - environment and system information",
                "shell": "Shell commands - command execution and Python code",
                "files": "File operations - reading, writing, listing files",
                "windows": "Window management - listing, focusing, resizing windows",
                "software": "Software management - installation and troubleshooting",
                "wechat": "WeChat operation - messaging and input handling",
            }
            
            # Register each skill as a resource
            for skill_dir in sorted(SKILLS_DIR.iterdir()):
                if not skill_dir.is_dir():
                    continue
                
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    continue
                
                skill_name = skill_dir.name
                uri = f"skill://{skill_name}"
                description = skill_descriptions.get(skill_name, f"Skill: {skill_name}")
                
                self._register_skill_resource(skill_name, uri, description)
                self._registered_skills.append(uri)
            
            # Register skill_list resource
            self._register_skill_list_resource()
            
            logger.info(f"[MCPGateway] Registered {len(self._registered_skills)} skills from {SKILLS_DIR}")
            
        except Exception as e:
            logger.error(f"[MCPGateway] Failed to setup skills: {e}")
    
    def _register_skill_resource(self, skill_name: str, uri: str, description: str) -> None:
        """Register a skill as an MCP resource."""
        
        def skill_handler(name: str = skill_name) -> str:
            """Load and return skill content from file."""
            skill_file = SKILLS_DIR / name / "SKILL.md"
            if skill_file.exists():
                return skill_file.read_text(encoding="utf-8")
            return f"Skill '{name}' not found"
        
        self.mcp.add_resource(
            fn=partial(skill_handler, name=skill_name),
            uri=uri,
            name=skill_name,
            description=description,
        )
    
    def _register_skill_list_resource(self) -> None:
        """Register skill_list resource that lists all available skills."""
        
        def skill_list_handler() -> str:
            """List all available skills with descriptions."""
            skills = []
            if SKILLS_DIR.exists():
                for skill_dir in sorted(SKILLS_DIR.iterdir()):
                    if not skill_dir.is_dir():
                        continue
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        content = skill_file.read_text(encoding="utf-8")
                        description = ""
                        # Parse YAML frontmatter for description
                        if content.startswith("---"):
                            lines = content.split("\n")
                            for line in lines[1:]:
                                if line.strip() == "---":
                                    break
                                if line.startswith("description:"):
                                    description = line.replace("description:", "").strip()
                        skills.append({
                            "name": skill_dir.name,
                            "uri": f"skill://{skill_dir.name}",
                            "description": description
                        })
            return json.dumps({"skills": skills}, ensure_ascii=False, indent=2)
        
        self.mcp.add_resource(
            fn=skill_list_handler,
            uri="skill://list",
            name="skill_list",
            description="List all available skills with descriptions",
        )
    
    def _setup_embedded_tools(self) -> None:
        """Register embedded tools (session, local, memory, chat).
        
        These tools run directly in the Gateway process, eliminating
        the need for separate MCP service processes.
        """
        from embedded_tools import (
            # Session tools
            agent_context_list,
            agent_context_history,
            agent_context_send,
            agent_inbox,
            agent_rest,
            # Local tools
            web_search,
            web_fetch,
            # Memory tools
            memory_save,
            memory_recall,
            memory_delete,
            memory_list_namespaces,
            task_log,
            task_history,
            goal_set,
            goal_progress,
            goal_complete,
            session_state,
            # Chat tools
            chat_reply,
            chat_ask,
            chat_notify,
            chat_show_image,
            chat_history,
            chat_get_message,
        )
        
        # Register embedded tools using the @tool decorator pattern
        embedded_funcs = [
            # Session tools
            agent_context_list,
            agent_context_history,
            agent_context_send,
            agent_inbox,
            agent_rest,
            # Local tools
            web_search,
            web_fetch,
            # Memory tools
            memory_save,
            memory_recall,
            memory_delete,
            memory_list_namespaces,
            task_log,
            task_history,
            goal_set,
            goal_progress,
            goal_complete,
            session_state,
            # Chat tools
            chat_reply,
            chat_ask,
            chat_notify,
            chat_show_image,
            chat_history,
            chat_get_message,
        ]
        
        for func in embedded_funcs:
            # Use the @tool decorator pattern to register each function
            self.mcp.tool()(func)
        
        embedded_count = 23  # 5 + 2 + 10 + 6
        self._registered_tools.extend([
            "agent_context_list", "agent_context_history", "agent_context_send",
            "agent_inbox", "agent_rest",
            "web_search", "web_fetch",
            "memory_save", "memory_recall", "memory_delete", "memory_list_namespaces",
            "task_log", "task_history", "goal_set", "goal_progress", "goal_complete",
            "session_state",
            "chat_reply", "chat_ask", "chat_notify", "chat_show_image",
            "chat_history", "chat_get_message",
        ])
        
        logger.info(f"[MCPGateway] Registered {embedded_count} embedded tools")
    
    def _setup_task_tools(self) -> None:
        """Register task_* async wrapper tools."""
        
        @self.mcp.tool()
        async def task_async(
            tool: str,
            args: Dict[str, Any],
            label: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            Asynchronously execute any MCP tool in the background.
            
            Use this for long-running operations (>30s) like:
            - Compilation, downloads, tests
            - Parallel research tasks  
            - Background operations that shouldn't block conversation
            
            Args:
                tool: Name of the MCP tool to execute (e.g., "run_command", "browser_navigate")
                args: Arguments to pass to the tool (e.g., {"command": "npm run build"})
                label: Human-readable label for tracking (e.g., "Build Project")
            
            Returns:
                Dictionary with:
                - success: Whether task was created
                - task_id: Unique ID for querying status (use with task_query)
                - status: Initial status ("pending" or "running")
            
            Examples:
                # Run a long build command
                task_async(tool="run_command", args={"command": "make -j8"}, label="Compile")
                
                # Parallel browser tasks
                task_async(tool="browser_navigate", args={"url": "https://..."}, label="Load page")
            """
            try:
                from core.task_manager import get_task_manager
                task_manager = get_task_manager()
                if task_manager:
                    result = await task_manager.spawn(
                        task_type="tool",
                        config={"tool": tool, "args": args, "registry": "gateway"},
                        label=label or f"Tool: {tool}",
                    )
                    return result
                else:
                    return {"success": False, "error": "TaskManager not available"}
            except Exception as e:
                logger.error(f"[MCPGateway] task_async failed: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_query(
            task_id: str,
            tail_lines: Optional[int] = None,
            start_line: Optional[int] = None,
            end_line: Optional[int] = None,
        ) -> Dict[str, Any]:
            """
            Query task status, outputs, and results with pagination support.
            
            Use this to:
            - Check progress of async tasks (task_async)
            - Get full content of truncated outputs (sync_output tasks)
            - Review completed task results
            
            Works for all task types: tool, agent, shell, sync_output.
            
            Args:
                task_id: Task ID from task_async, agent_call, or truncated output hint
                tail_lines: Get last N lines of output (default: 50 for running tasks)
                start_line: Get output starting from line N (1-based)
                end_line: Get output up to line N (inclusive)
            
            Returns:
                Dictionary with:
                - success: Whether query succeeded
                - task_id: The task ID
                - type: Task type (tool, agent, shell, sync_output)
                - label: Task label
                - status: Current status (pending, running, completed, failed, cancelled)
                - running_seconds: Elapsed time (if running)
                - duration_seconds: Total duration (if completed)
                - result: Task result / truncated content (if completed)
                - full_output: Paginated full output (if start_line/end_line/tail_lines used)
                - output_range: Line range returned (e.g., "1-100")
                - output_total_lines: Total lines in output file
                - output_has_more: Whether more content is available
                - error: Error message (if failed)
            
            Examples:
                # Check async task status
                task_query(task_id="abc123")
                
                # Get full content of truncated output
                task_query(task_id="so_def456", start_line=1, end_line=100)
                
                # Get last 200 lines
                task_query(task_id="so_def456", tail_lines=200)
            """
            try:
                from core.task_manager import get_task_manager
                task_manager = get_task_manager()
                if task_manager:
                    return await task_manager.get_status(
                        task_id=task_id,
                        include_outputs=True,
                        output_limit=tail_lines or 50,
                        start_line=start_line,
                        end_line=end_line,
                        tail_lines=tail_lines,
                    )
                else:
                    return {"success": False, "error": "TaskManager not available"}
            except Exception as e:
                logger.error(f"[MCPGateway] task_query failed: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_list(
            status: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            List all tasks, optionally filtered by status.
            
            Args:
                status: Filter by status (pending, running, completed, failed, cancelled)
                        Leave empty to list all tasks.
            
            Returns:
                Dictionary with:
                - success: Whether query succeeded
                - tasks: List of task summaries
                - total: Total number of tasks
            
            Examples:
                task_list()                      # All tasks
                task_list(status="running")      # Only running tasks
            """
            try:
                from core.task_manager import get_task_manager
                task_manager = get_task_manager()
                if task_manager:
                    status_filter = [status] if status else None
                    return await task_manager.get_status(
                        task_id=None,
                        status_filter=status_filter,
                    )
                else:
                    return {"success": False, "error": "TaskManager not available"}
            except Exception as e:
                logger.error(f"[MCPGateway] task_list failed: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_cancel(
            task_id: str,
            reason: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            Cancel a running task.
            
            Args:
                task_id: Task ID to cancel
                reason: Optional reason for cancellation
            
            Returns:
                Dictionary with:
                - success: Whether cancellation succeeded
                - task_id: The task ID
                - status: Final status (should be "cancelled")
            
            Examples:
                task_cancel(task_id="abc123")
                task_cancel(task_id="abc123", reason="No longer needed")
            """
            try:
                from core.task_manager import get_task_manager
                task_manager = get_task_manager()
                if task_manager:
                    return await task_manager.cancel(task_id, reason)
                else:
                    return {"success": False, "error": "TaskManager not available"}
            except Exception as e:
                logger.error(f"[MCPGateway] task_cancel failed: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def task_summary(task_id: str) -> Dict[str, Any]:
            """
            Get AI-generated summary of a completed task's result.
            
            Use this to get a concise, human-readable summary of what the task accomplished.
            Only works for completed or failed tasks.
            
            Args:
                task_id: Task ID to summarize
            
            Returns:
                Dictionary with:
                - success: Whether query succeeded
                - task_id: The task ID
                - label: Task label
                - status: Task status
                - summary: AI-generated summary (1-2 sentences)
            
            Examples:
                task_summary(task_id="abc123")
            """
            try:
                from core.task_manager import get_task_manager
                task_manager = get_task_manager()
                if task_manager:
                    return await task_manager.get_result(task_id, format="summary")
                else:
                    return {"success": False, "error": "TaskManager not available"}
            except Exception as e:
                logger.error(f"[MCPGateway] task_summary failed: {e}")
                return {"success": False, "error": str(e)}
        
        logger.info("[MCPGateway] Registered task_* tools")
    
    def _setup_agent_tools(self) -> None:
        """Register agent_* tools."""
        
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
                # Delegate research task
                agent_call(task="研究 React 和 Vue 的性能差异，写一份对比报告")
                
                # With context
                agent_call(
                    task="分析这个 bug 并提出修复方案",
                    context="用户报告登录页面偶尔卡死",
                    model="claude-sonnet-4"
                )
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
                import asyncio
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
                logger.error(f"[MCPGateway] agent_call failed: {e}")
                return {"success": False, "error": str(e)}
        
        logger.info("[MCPGateway] Registered agent_* tools")
    
    
    def get_asgi_app(self):
        """Get the ASGI app for mounting in FastAPI."""
        return self.mcp.http_app(path="/")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "agent_id": self.agent_id,
            "agent_index": self.agent_index,
            "tools_count": len(self._registered_tools),
            "skills_count": len(self._registered_skills),
            "registry_stats": self.registry.get_stats(),
        }
    
    async def close(self) -> None:
        """Close the gateway and release resources."""
        await self.registry.close()
        logger.info(f"[MCPGateway] Closed gateway for agent {self.agent_id}")
