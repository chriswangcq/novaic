"""
AgentMCPGateway - MCP Gateway for a single Agent

Gateway 作为纯中间件，负责：
1. 聚合所有子 MCP Servers 的工具（通过 ToolRegistry）
2. 提供 task_* 异步任务代理工具
3. 暴露 Skills 作为 MCP Resources

Architecture:
    AgentMCPGateway (FastMCP)
        ├── VM MCP Tools: 通过 ToolRegistry 代理 (32 tools)
        ├── Agent Context MCP Tools: 通过 ToolRegistry 代理 (6 tools)
        ├── Local MCP Tools: 通过 ToolRegistry 代理 (2 tools)
        ├── Memory MCP Tools: 通过 ToolRegistry 代理 (10 tools)
        ├── Chat MCP Tools: 通过 ToolRegistry 代理 (6 tools)
        ├── Skills: MCP Resources
        └── task_*: Gateway 内置的异步任务工具 (5 tools)
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from functools import partial

from fastmcp import FastMCP

from config.agents import PortConfig, allocate_ports_for_agent
from executor.registry import ToolRegistry

# Discovery intervals
DISCOVERY_INTERVAL_FAILED = 5  # seconds for failed servers
DISCOVERY_INTERVAL_SUCCESS = 30  # seconds for successful servers
DISCOVERY_TIMEOUT = 1  # seconds timeout for discovery

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
        
        # Track server discovery status
        self._discovered_servers: Set[str] = set()  # servers with tools discovered
        self._discovery_task: Optional[asyncio.Task] = None
        self._discovery_running = False
        
        logger.info(f"[MCPGateway] Created gateway for agent {agent_id} (index={agent_index})")
    
    def _build_instructions(self) -> str:
        """Build initial MCP server instructions (will be updated after setup)."""
        return "NovAIC Agent Gateway - 统一 MCP 入口\n\n正在初始化，请稍候..."
    
    def _build_dynamic_instructions(self) -> str:
        """
        根据实际挂载的子 MCP 和发现的工具动态生成说明。
        在 setup() 完成后调用。
        """
        lines = [
            "# NovAIC Agent Gateway - 统一 MCP 入口",
            "",
            "本 Gateway 是 Agent 操作的唯一入口，聚合了所有子 MCP 服务的工具。",
            "",
            "---",
            "",
            "## 已挂载的 MCP Servers",
            "",
        ]
        
        # 从 registry 获取工具统计
        stats = self.registry.get_stats()
        tools_by_server = stats.get("tools_by_server", {})
        
        # 列出各 server 的工具数
        lines.append("| Server | 工具数 | 状态 |")
        lines.append("|--------|--------|------|")
        
        for server_name, tool_count in tools_by_server.items():
            status = "✅ 已发现" if tool_count > 0 else "⏳ 等待中"
            lines.append(f"| {server_name} | {tool_count} | {status} |")
        
        lines.append("")
        lines.append(f"**总计**: {len(self._registered_tools)} 个工具")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Gateway 内置工具
        lines.append("## Gateway 内置工具")
        lines.append("")
        lines.append("| 工具 | 用途 |")
        lines.append("|------|------|")
        lines.append("| task_async | 异步执行任意工具 |")
        lines.append("| task_query | 查询任务状态/结果 |")
        lines.append("| task_list | 列出所有任务 |")
        lines.append("| task_cancel | 取消任务 |")
        lines.append("| task_summary | 获取 AI 摘要 |")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 按 server 分组显示工具（从 registry 获取）
        lines.append("## 聚合的工具列表")
        lines.append("")
        
        # 从 registry 缓存获取工具详情
        try:
            cached_tools = self.registry._tools_cache or []
            # 按 server 分组
            server_tools: Dict[str, List[Dict]] = {}
            for tool in cached_tools:
                server = tool.get("_server", "unknown")
                if server not in server_tools:
                    server_tools[server] = []
                server_tools[server].append(tool)
            
            for server_name, tools in sorted(server_tools.items()):
                lines.append(f"### {server_name} ({len(tools)} 工具)")
                lines.append("")
                lines.append("| 工具 | 说明 |")
                lines.append("|------|------|")
                
                for tool in sorted(tools, key=lambda t: t.get("name", "")):
                    name = tool.get("name", "")
                    desc = tool.get("description", "")
                    # 截断过长的描述
                    if len(desc) > 60:
                        desc = desc[:57] + "..."
                    # 转义管道符
                    desc = desc.replace("|", "\\|").replace("\n", " ")
                    lines.append(f"| {name} | {desc} |")
                
                lines.append("")
        except Exception as e:
            lines.append(f"(工具列表加载中: {e})")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Skills
        if self._registered_skills:
            lines.append("## Skills (操作指南)")
            lines.append("")
            for skill_uri in self._registered_skills:
                lines.append(f"- {skill_uri}")
            lines.append("")
        
        # 使用决策树
        lines.append("---")
        lines.append("")
        lines.append("## 使用决策树")
        lines.append("")
        lines.append("```")
        lines.append("需要执行操作")
        lines.append("├─ 预计 <30 秒？ → 直接调用工具")
        lines.append("├─ 预计 >30 秒？ → task_async 包装")
        lines.append("└─ 需要多步推理？ → agent_call 委托")
        lines.append("```")
        
        return "\n".join(lines)
    
    def _register_agent_servers(self) -> None:
        """Register all MCP servers for this agent.
        
        All servers are discovered via HTTP protocol:
        - VM: runs inside the virtual machine
        - Sub MCPs: agent-context, local, memory, chat (mounted at /sub-mcp/)
        """
        # VM server (runs inside the virtual machine)
        self.registry.register_server("vm", port=self.ports.vm, priority=0)
        
        # Sub MCP servers (mounted as sub-paths, discovered via HTTP)
        gateway_port = int(os.getenv("NOVAIC_PORT", "19999"))
        base_url = f"http://127.0.0.1:{gateway_port}/agents/{self.agent_id}/sub-mcp"
        
        # All sub MCPs use HTTP discovery (same as VM)
        self.registry.register_server("agent-context", url=f"{base_url}/agent-context/", priority=1)
        self.registry.register_server("local", url=f"{base_url}/local/", priority=1)
        self.registry.register_server("memory", url=f"{base_url}/memory/", priority=1)
        self.registry.register_server("chat", url=f"{base_url}/chat/", priority=1)
        
        # QEMU debug server (optional, runs on host)
        qemu_enabled = os.getenv("NOVAIC_MCP_QEMUDEBUG_ENABLED", "false").lower() == "true"
        if qemu_enabled:
            self.registry.register_server("qemudebug", port=self.ports.qemudebug, enabled=True, priority=3)
        
        logger.info(f"[MCPGateway] Registered 5 servers for agent {self.agent_index} (VM + 4 sub-MCPs)")
    
    async def setup(self) -> None:
        """
        Setup the gateway by discovering and registering all tools and skills.
        
        This must be called before mounting the gateway.
        """
        # Setup aggregated tools from external MCP servers (VM)
        await self._setup_tools()
        
        # Setup skills as MCP resources
        await self._setup_skills()
        
        # Setup Gateway-specific tools (task_* only)
        self._setup_task_tools()
        
        # 动态更新 instructions，反映实际挂载的子 MCP 和工具
        self._update_instructions()
        
        logger.info(
            f"[MCPGateway] Setup complete for agent {self.agent_index}: "
            f"{len(self._registered_tools)} tools, {len(self._registered_skills)} skills"
        )
    
    def _update_instructions(self) -> None:
        """更新 MCP instructions 为动态生成的内容。"""
        try:
            dynamic_instructions = self._build_dynamic_instructions()
            # FastMCP 的 instructions 可以直接赋值更新
            if hasattr(self.mcp, '_instructions'):
                self.mcp._instructions = dynamic_instructions
            elif hasattr(self.mcp, 'instructions'):
                self.mcp.instructions = dynamic_instructions
            logger.debug(f"[MCPGateway] Updated instructions for agent {self.agent_index}")
        except Exception as e:
            logger.warning(f"[MCPGateway] Failed to update instructions: {e}")
    
    async def _setup_tools(self) -> None:
        """Discover tools from sub-servers and register them as MCP tools."""
        await self._discover_and_register_tools()
    
    async def _discover_and_register_tools(self, timeout: float = DISCOVERY_TIMEOUT) -> int:
        """
        Discover tools from sub-servers and register new ones.
        
        Args:
            timeout: Timeout for discovery in seconds
        
        Returns:
            Number of new tools registered
        """
        new_tools_count = 0
        
        try:
            # Discover tools with timeout
            tools = await asyncio.wait_for(
                self.registry.discover_all_tools(use_cache=False),
                timeout=timeout
            )
            
            # Track which servers have tools
            stats = self.registry.get_stats()
            tools_by_server = stats.get("tools_by_server", {})
            
            for server_name, tool_count in tools_by_server.items():
                if tool_count > 0:
                    if server_name not in self._discovered_servers:
                        logger.info(f"[MCPGateway] Server '{server_name}' now available with {tool_count} tools")
                    self._discovered_servers.add(server_name)
            
            # Register new tools (skip already registered)
            for tool in tools:
                tool_name = tool.get("name", "")
                if not tool_name:
                    continue
                
                if tool_name not in self._registered_tools:
                    # Register proxy tool
                    self._register_proxy_tool(tool)
                    self._registered_tools.append(tool_name)
                    new_tools_count += 1
            
            if new_tools_count > 0:
                logger.info(f"[MCPGateway] Registered {new_tools_count} new tools (total: {len(self._registered_tools)})")
                # 更新 instructions 反映新发现的工具
                self._update_instructions()
            
        except asyncio.TimeoutError:
            logger.debug(f"[MCPGateway] Tool discovery timed out after {timeout}s")
        except Exception as e:
            logger.debug(f"[MCPGateway] Tool discovery failed: {e}")
        
        return new_tools_count
    
    def start_discovery_task(self) -> None:
        """Start the background discovery task."""
        if self._discovery_task is not None:
            return
        
        self._discovery_running = True
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        logger.info(f"[MCPGateway] Started discovery task for agent {self.agent_index}")
    
    def stop_discovery_task(self) -> None:
        """Stop the background discovery task."""
        self._discovery_running = False
        if self._discovery_task is not None:
            self._discovery_task.cancel()
            self._discovery_task = None
            logger.info(f"[MCPGateway] Stopped discovery task for agent {self.agent_index}")
    
    async def _discovery_loop(self) -> None:
        """
        Background task to periodically discover tools from servers.
        
        - Failed servers: check every 5 seconds (1s timeout)
        - Successful servers: check every 30 seconds
        """
        last_success_check = 0
        
        while self._discovery_running:
            try:
                # Check if any server is not yet discovered
                stats = self.registry.get_stats()
                registered_servers = set(stats.get("tools_by_server", {}).keys())
                undiscovered = registered_servers - self._discovered_servers
                
                current_time = asyncio.get_event_loop().time()
                
                if undiscovered:
                    # Has undiscovered servers - check frequently
                    new_tools = await self._discover_and_register_tools(timeout=DISCOVERY_TIMEOUT)
                    if new_tools > 0:
                        last_success_check = current_time
                    await asyncio.sleep(DISCOVERY_INTERVAL_FAILED)
                else:
                    # All servers discovered - check less frequently
                    if current_time - last_success_check >= DISCOVERY_INTERVAL_SUCCESS:
                        await self._discover_and_register_tools(timeout=DISCOVERY_TIMEOUT * 3)
                        last_success_check = current_time
                    await asyncio.sleep(DISCOVERY_INTERVAL_SUCCESS)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[MCPGateway] Discovery loop error: {e}")
                await asyncio.sleep(DISCOVERY_INTERVAL_FAILED)
    
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
        """Register a skill as an MCP resource using FastMCP 2.x decorator."""
        
        # Use the decorator pattern for FastMCP 2.x
        @self.mcp.resource(uri, name=skill_name, description=description)
        def skill_handler() -> str:
            """Load and return skill content from file."""
            skill_file = SKILLS_DIR / skill_name / "SKILL.md"
            if skill_file.exists():
                return skill_file.read_text(encoding="utf-8")
            return f"Skill '{skill_name}' not found"
    
    def _register_skill_list_resource(self) -> None:
        """Register skill_list resource that lists all available skills."""
        
        @self.mcp.resource("skill://list", name="skill_list", description="List all available skills with descriptions")
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
    
    def get_asgi_app(self):
        """Get the ASGI app for mounting in FastAPI.
        
        Returns a Starlette ASGI application that can be mounted in FastAPI.
        
        IMPORTANT: When mounting this app, you MUST either:
        1. Pass mcp_app.lifespan to FastAPI's lifespan parameter, OR
        2. Manually call the lifespan context manager before mounting
        
        Without proper lifespan handling, requests will fail with:
        "RuntimeError: FastMCP's StreamableHTTPSessionManager task group was not initialized"
        """
        mcp_app = self.mcp.http_app(path="/")
        
        # Log available lifespan attributes for debugging
        lifespan_info = []
        if hasattr(mcp_app, 'lifespan') and mcp_app.lifespan is not None:
            lifespan_info.append("lifespan")
        if hasattr(mcp_app, 'lifespan_handler') and mcp_app.lifespan_handler:
            lifespan_info.append("lifespan_handler")
        if hasattr(mcp_app, 'router') and hasattr(mcp_app.router, 'lifespan_context'):
            if mcp_app.router.lifespan_context is not None:
                lifespan_info.append("router.lifespan_context")
        
        logger.info(f"[MCPGateway] Created ASGI app for agent {self.agent_index}, available lifespans: {lifespan_info or 'none'}")
        
        return mcp_app
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        registry_stats = self.registry.get_stats()
        registered_servers = set(registry_stats.get("tools_by_server", {}).keys())
        
        return {
            "agent_id": self.agent_id,
            "agent_index": self.agent_index,
            "tools_count": len(self._registered_tools),
            "skills_count": len(self._registered_skills),
            "discovered_servers": list(self._discovered_servers),
            "pending_servers": list(registered_servers - self._discovered_servers),
            "discovery_running": self._discovery_running,
            "registry_stats": registry_stats,
        }
    
    async def close(self) -> None:
        """Close the gateway and release resources."""
        # Stop discovery task first
        self.stop_discovery_task()
        
        await self.registry.close()
        logger.info(f"[MCPGateway] Closed gateway for agent {self.agent_id}")
