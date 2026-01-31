"""
NovAIC Gateway - Core Agent Implementation

ReAct (Reasoning + Acting) 循环实现

最佳实践遵循:
- MCP 三元组: Tools, Resources (Skills), Prompts
- 分层架构: Agent(非确定性) <-> MCP(接口) <-> Tools(确定性执行)
- 目标追踪和评估
- 可观测性和追踪
"""

from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import uuid

from .llm_client import LLMError, BaseLLMClient, OpenAIClient, AnthropicClient, GoogleAIClient
from .session import SessionManager
from .mcp_client import MCPClient, MCPSkill
from executor.registry import ToolRegistry
from agent.session.compaction import Compactor
from agent.session.storage_db import SessionStorage


# ==================== Data Classes ====================
# Note: TaskStatus and TaskTrace have been removed in v3.
# Execution tracking is now done via console logs and execution_logs table.


class NovAICAgent:
    """
    Main Agent class that orchestrates:
    - LLM communication (reasoning) - 非确定性规划
    - Tool execution (acting) - via MCP Client - 确定性执行
    - Environment perception (sensing)
    - Session management
    - Skill awareness - 动态加载相关技能
    - Goal tracking - 目标追踪和评估
    - Observability - 完整执行追踪
    
    架构遵循 MCP 最佳实践:
    - Agent 负责规划、重规划和评估
    - Tools 负责执行
    - Skills (Resources) 提供领域知识
    """
    
    def __init__(self, mcp_port: int, tool_registry: Optional[ToolRegistry] = None, session_key: str = "main"):
        """
        Initialize the Agent.
        
        Args:
            mcp_port: MCP Server 端口 (QEMU 转发的端口)
            tool_registry: Optional unified tool registry (aggregates multiple MCP servers)
            session_key: Session identifier for persistence (default: "main")
        """
        self.mcp_port = mcp_port
        self.session_key = session_key
        
        # ToolRegistry for unified tool access (if provided)
        self.tool_registry = tool_registry
        
        # Session persistence
        self.storage = SessionStorage()
        
        # Cache for LLM clients (cache_key -> client)
        self._llm_clients: Dict[str, BaseLLMClient] = {}
        
        # Initialize other components
        self.session = SessionManager()
        self.mcp_client = MCPClient()  # Fallback direct client
        
        # Tools list (dynamically loaded from MCP)
        self.tools: List[Dict[str, Any]] = []
        self._tools_initialized = False
        
        # Skills (dynamically loaded from MCP Resources)
        self.skills: Dict[str, MCPSkill] = {}  # uri -> skill
        self._skills_initialized = False
        
        # Control flags
        self._interrupted = False
        
        # Environment state
        self._executor_healthy = None
        
        # Settings (can be overridden)
        self.max_iterations = 20
        self.max_tokens = 4096
        self.llm_timeout = 120  # 2分钟超时，避免长时间卡住
        self.llm_max_retries = 3
        self.api_style = "chat_completions"
        
        # For responses API mode: track response chain
        self._response_id: Optional[str] = None
        
        # Session compaction
        self.compactor = Compactor(
            max_context_ratio=0.75,  # Compact when at 75% of context
            compaction_ratio=0.5,    # Compact 50% of oldest messages
            min_messages_to_keep=6,  # Always keep recent 6 messages
        )
        self.compaction_check_interval = 10  # 每 10 轮检查一次 compaction
        self._compaction_lock = asyncio.Lock()  # Lock for async compaction
        self._compaction_task: Optional[asyncio.Task] = None  # Background compaction task
        
        # Session persistence tracking
        self._last_saved_msg_count = 0  # Track how many messages have been saved
        self._session_restored = False  # Whether session was restored from disk
        
        # Context injection settings (自主调度 - inbox)
        self.inbox_check_interval = 5  # 每 5 轮注入一次上下文 (legacy, now check every loop)
        self._inbox_callback = None  # Callback to get pending events
        self.model_context_sizes = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4o": 128000,
            "gpt-3.5-turbo": 16384,
            "claude-3-opus": 200000,
            "claude-3-sonnet": 200000,
            "claude-3-haiku": 200000,
            "claude-sonnet-4-20250514": 200000,
            "gemini-pro": 32000,
            "gemini-1.5-pro": 1000000,
        }
        self._default_context_size = 128000  # Default to 128k if unknown
    
    def _get_model_context_size(self, model: str) -> int:
        """Get context size for a model."""
        # Check exact match first
        if model in self.model_context_sizes:
            return self.model_context_sizes[model]
        
        # Check partial match
        for key, size in self.model_context_sizes.items():
            if key in model.lower():
                return size
        
        return self._default_context_size
    
    async def _check_compaction(
        self, 
        model: str,
        provider: str,
        api_base: str,
        api_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if compaction is needed and start async compaction if so (non-blocking).
        
        Args:
            model: Model being used
            provider: LLM provider
            api_base: API base URL
            api_key: API key
        
        Returns:
            None (compaction runs asynchronously)
        """
        # 如果已经有一个 compaction 任务在运行，跳过
        if self._compaction_task and not self._compaction_task.done():
            print(f"[Agent] Compaction already in progress, skipping")
            return None
        
        messages = self.session.get_all_messages()
        context_size = self._get_model_context_size(model)
        
        if not self.compactor.should_compact(messages, context_size):
            return None
        
        # 获取需要压缩的消息快照
        messages_snapshot = messages.copy()
        
        # 启动后台 compaction 任务（非阻塞）
        print(f"[Agent] Starting async compaction task...")
        self._compaction_task = asyncio.create_task(
            self._do_compaction_async(
                messages_snapshot=messages_snapshot,
                model=model,
                provider=provider,
                api_base=api_base,
                api_key=api_key,
            )
        )
        
        return None  # 不等待结果，立即返回
    
    async def _do_compaction_async(
        self,
        messages_snapshot: List[Dict[str, Any]],
        model: str,
        provider: str,
        api_base: str,
        api_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        异步执行 compaction（后台任务）。
        
        使用锁保护 session 更新，确保原子操作。
        同时保存 compaction summary 到磁盘。
        """
        try:
            # Get LLM client for summary generation
            llm_client = self._get_llm_client(provider, api_base, api_key)
            
            # Perform compaction (this is the slow part)
            result = await self.compactor.compact(messages_snapshot, llm_client, model)
            
            if result.get("stats", {}).get("compacted"):
                # 使用锁保护 session 更新
                async with self._compaction_lock:
                    # 区间替换逻辑：
                    # 计算快照中被压缩掉的消息数量
                    compacted_count = result["stats"].get("messages_compacted", 0)
                    
                    # 获取当前 session 的最新消息（可能在 compaction 期间有新消息）
                    current_messages = self.session.get_all_messages()
                    
                    # 新消息 = 当前消息中，快照之后新增的消息
                    new_messages_since_snapshot = current_messages[len(messages_snapshot):]
                    
                    # 最终消息列表 = compacted 结果 + 新增消息
                    final_messages = result["new_messages"] + new_messages_since_snapshot
                    self.session.messages = final_messages
                    
                    # 保存 compaction summary 到磁盘
                    if result.get("summary"):
                        self.storage.save_compaction_summary(
                            session_key=self.session_key,
                            summary=result["summary"],
                            compacted_count=compacted_count,
                            original_tokens=result["stats"].get("original_tokens", 0),
                            summary_tokens=result["stats"].get("new_tokens", 0),
                        )
                    
                    # 更新保存计数（compaction 后重置）
                    self._last_saved_msg_count = len(final_messages)
                    
                    print(f"[Agent] Async compaction completed: {result['stats']}")
            
            return result
            
        except Exception as e:
            print(f"[Agent] Async compaction failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def set_inbox_callback(self, callback) -> None:
        """
        Set callback to get pending events for context injection.
        
        Args:
            callback: Async function that returns inbox info dict
        """
        self._inbox_callback = callback
    
    async def _get_inbox_context(self) -> Optional[str]:
        """
        Get formatted inbox context for injection into messages.
        
        Includes both regular inbox events and task completion notifications.
        
        Returns:
            Formatted string with inbox summary, or None if empty/unavailable
        """
        lines = []
        total_pending = 0
        has_urgent = False
        recommendation = "continue"
        
        # 1. Get regular inbox events
        if self._inbox_callback:
            try:
                inbox = await self._inbox_callback()
                pending_count = inbox.get("pending_count", 0)
                total_pending += pending_count
                
                if pending_count > 0:
                    events = inbox.get("events", [])
                    has_urgent = inbox.get("has_urgent", False)
                    recommendation = inbox.get("recommendation", "continue")
                    
                    for event in events[:5]:  # Show first 5 events
                        event_type = event.get("type", "unknown")
                        content = event.get("content", "")
                        priority = event.get("priority", "normal")
                        marker = "🔴" if priority == "high" else "⚪"
                        
                        if event_type == "user_message":
                            lines.append(f"  {marker} [用户消息] \"{content}\"")
                        elif event_type == "task_completed":
                            task_id = event.get("task_id", "")
                            label = event.get("label", "")
                            summary = event.get("summary", "")[:100]
                            lines.append(f"  ✅ [任务完成] {label} ({task_id}): {summary}")
                        elif event_type == "task_failed":
                            task_id = event.get("task_id", "")
                            label = event.get("label", "")
                            error = event.get("error", "")[:100]
                            lines.append(f"  ❌ [任务失败] {label} ({task_id}): {error}")
                        else:
                            summary = event.get("summary", "")[:100]
                            lines.append(f"  {marker} [{event_type}] {summary}")
            except Exception as e:
                print(f"[Agent] Failed to get inbox events: {e}")
        
        # 2. Get task notifications from TaskManager
        try:
            from core.task_manager import get_task_manager
            task_manager = get_task_manager()
            
            if task_manager:
                # Get recently completed tasks for this session
                result = await task_manager.get_status(
                    task_id=None,
                    status_filter=["completed", "failed"],
                    agent_id=None,  # Get all tasks
                )
                
                if result.get("success"):
                    tasks = result.get("tasks", [])
                    # Filter to tasks completed in the last 5 minutes that haven't been shown
                    from datetime import datetime, timedelta
                    cutoff = datetime.now() - timedelta(minutes=5)
                    
                    for task in tasks[:5]:  # Show at most 5 task notifications
                        completed_str = task.get("completed_at")
                        if completed_str:
                            try:
                                completed_at = datetime.fromisoformat(completed_str)
                                if completed_at > cutoff:
                                    status = task.get("status", "")
                                    label = task.get("label", "Unknown task")
                                    task_id = task.get("task_id", "")
                                    
                                    # Only add if not already in lines from inbox
                                    task_line_check = f"({task_id})"
                                    if not any(task_line_check in line for line in lines):
                                        if status == "completed":
                                            summary = task.get("result_summary", "")[:100]
                                            lines.append(f"  ✅ [任务完成] {label} ({task_id}): {summary}")
                                        elif status == "failed":
                                            error = task.get("error", "")[:100]
                                            lines.append(f"  ❌ [任务失败] {label} ({task_id}): {error}")
                                        total_pending += 1
                            except:
                                pass
        except Exception as e:
            print(f"[Agent] Failed to get task notifications: {e}")
        
        # 3. Build final context message
        if total_pending == 0 and not lines:
            return None
        
        header = f"📬 [收件箱] 有 {total_pending} 个待处理事件:" if total_pending > 0 else ""
        
        if has_urgent:
            lines.append("⚠️ 有高优先级事件需要处理")
        
        if recommendation == "check_urgent":
            lines.append("建议: 优先处理高优先级事件")
        elif recommendation == "process_all":
            lines.append("建议: 处理积压事件")
        
        if lines:
            result_lines = [header] if header else []
            result_lines.extend(lines)
            print(f"[Agent] Inbox context: {total_pending} pending events, urgent={has_urgent}")
            return "\n".join(result_lines)
        
        return None
    
    def _get_llm_client(
        self, 
        provider: str,
        api_base: str,
        api_key: str
    ) -> BaseLLMClient:
        """Get or create LLM client for the given provider configuration."""
        cache_key = f"{provider}:{api_base}"
        
        if cache_key in self._llm_clients:
            return self._llm_clients[cache_key]
        
        print(f"[Agent] Creating LLM client: provider={provider}, api_base={api_base}")
        
        if provider == "anthropic":
            client = AnthropicClient(api_key=api_key, api_base=api_base)
        elif provider == "google":
            client = GoogleAIClient(api_key=api_key, api_base=api_base)
        else:
            client = OpenAIClient(api_base=api_base, api_key=api_key)
        
        # Update timeout settings
        client.timeout.read = self.llm_timeout
        
        self._llm_clients[cache_key] = client
        return client
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool using ToolRegistry (if available) or direct MCPClient.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool arguments
        
        Returns:
            Tool execution result
        """
        if self.tool_registry:
            # Use unified ToolRegistry (supports multiple MCP servers)
            return await self.tool_registry.execute(tool_name, tool_input)
        else:
            # Fallback to direct MCPClient
            return await self.mcp_client.call_tool(tool_name, tool_input)
    
    async def check_executor_health(self) -> Dict[str, Any]:
        """Check Executor (MCP Server) health status."""
        if self._tools_initialized and len(self.tools) > 0:
            self._executor_healthy = True
            return {"healthy": True, "tools_count": len(self.tools)}
        
        try:
            await self.initialize()
            if len(self.tools) > 0:
                self._executor_healthy = True
                return {"healthy": True, "tools_count": len(self.tools)}
        except Exception as e:
            print(f"[Agent] MCP connection failed: {e}")
        
        self._executor_healthy = False
        return {"healthy": False, "error": "MCP Server not available"}
    
    async def initialize(self) -> None:
        """
        Initialize Agent: discover tools and skills from MCP Server(s).
        
        MCP 三元组完整初始化:
        - Tools: 可执行的动作
        - Resources/Skills: 领域知识和工作流指导
        - Prompts: 预定义模板（如果有）
        
        If tool_registry is provided, uses unified registry for multiple MCP servers.
        Otherwise falls back to direct MCPClient for single server.
        """
        from .mcp_client import get_mcp_url
        
        if self._tools_initialized and len(self.tools) > 0:
            print(f"[Agent] Already initialized with {len(self.tools)} tools")
            return
        
        print(f"[Agent] ========== MCP Initialize Start ==========")
        
        try:
            if self.tool_registry:
                # Use unified ToolRegistry (multiple MCP servers)
                print(f"[Agent] Using ToolRegistry (unified mode)")
                
                # Discover tools from all registered servers
                print(f"[Agent] Discovering tools from registry...")
                raw_tools = await self.tool_registry.discover_all_tools(use_cache=False)
                print(f"[Agent] Raw tools discovered: {len(raw_tools)}")
                
                # Convert to LLM format
                self.tools = self.tool_registry.to_llm_tools_format(raw_tools)
                print(f"[Agent] LLM-formatted tools: {len(self.tools)}")
                
                # Get registry stats
                stats = self.tool_registry.get_stats()
                print(f"[Agent] Tools by server: {stats.get('tools_by_server', {})}")
                
                # Also initialize direct MCPClient for skills (skills from primary VM server)
                mcp_url = get_mcp_url(self.mcp_port)
                print(f"[Agent] Registering primary MCP server for skills at port {self.mcp_port}...")
                await self.mcp_client.register_server(name="executor", port=self.mcp_port)
                
            else:
                # Direct MCPClient mode (single server)
                mcp_url = get_mcp_url(self.mcp_port)
                print(f"[Agent] Using direct MCPClient mode")
                print(f"[Agent] MCP URL: {mcp_url}")
                print(f"[Agent] MCP Port: {self.mcp_port}")
                
                # 注册 MCP Server (HTTP)
                print(f"[Agent] Registering MCP server 'executor' at port {self.mcp_port}...")
                await self.mcp_client.register_server(name="executor", port=self.mcp_port)
                print(f"[Agent] MCP server registered")
                
                # 发现 Tools
                print(f"[Agent] Discovering tools...")
                tools = await self.mcp_client.list_all_tools()
                print(f"[Agent] Raw tools discovered: {len(tools)}")
                
                self.tools = self.mcp_client.to_llm_tools_format(tools)
                print(f"[Agent] LLM-formatted tools: {len(self.tools)}")
            
            if self.tools:
                tool_names = [t.get('function', {}).get('name', 'unknown') for t in self.tools[:10]]
                print(f"[Agent] First 10 tools: {tool_names}")
            
            # 发现 Skills (从 Resources) - always from primary MCP server
            print(f"[Agent] Discovering skills...")
            await self._discover_skills()
            
            if len(self.tools) > 0:
                self._executor_healthy = True
                self._tools_initialized = True  # 只有成功发现工具才标记为已初始化
                print(f"[Agent] ✓ Initialized successfully: {len(self.tools)} tools, {len(self.skills)} skills")
                
                # 尝试恢复之前的会话
                self.restore_session()
            else:
                self._executor_healthy = False
                print(f"[Agent] ✗ MCP Server connected but NO TOOLS discovered!")
                
        except Exception as e:
            import traceback
            print(f"[Agent] ✗ Failed to initialize MCP connection: {e}")
            print(f"[Agent] Traceback:\n{traceback.format_exc()}")
            self._executor_healthy = False
            self.tools = []
        
        print(f"[Agent] ========== MCP Initialize End ==========")
        print(f"[Agent] Status: tools_initialized={self._tools_initialized}, tools_count={len(self.tools)}, healthy={self._executor_healthy}")
    
    async def _discover_skills(self) -> None:
        """发现并缓存所有可用的 Skills"""
        try:
            skills = await self.mcp_client.discover_all_skills()
            self.skills = {skill.uri: skill for skill in skills}
            self._skills_initialized = True
            print(f"[Agent] Discovered skills: {[s.name for s in skills]}")
        except Exception as e:
            print(f"[Agent] Failed to discover skills: {e}")
            self.skills = {}
    
    async def _load_relevant_skills(self, task: str) -> List[MCPSkill]:
        """
        根据任务加载相关的 Skills
        
        Args:
            task: 用户任务描述
        
        Returns:
            相关的 Skills 列表（已加载内容）
        """
        if not self._skills_initialized:
            await self._discover_skills()
        
        return await self.mcp_client.load_relevant_skills(task, max_skills=3)
    
    def _build_enhanced_system_prompt(self, skills: List[MCPSkill]) -> str:
        """
        构建增强的 System Prompt，包含相关 Skills
        
        Args:
            skills: 相关的 Skills 列表
        
        Returns:
            增强后的 system prompt
        """
        base_prompt = SessionManager.SYSTEM_PROMPT
        
        if not skills:
            return base_prompt
        
        skill_sections = []
        for skill in skills:
            if skill.content:
                skill_sections.append(f"### {skill.name}\n{skill.content}")
        
        if skill_sections:
            skills_text = "\n\n".join(skill_sections)
            return f"""{base_prompt}

## Loaded Skills (Domain Knowledge)

{skills_text}
"""
        
        return base_prompt
    
    async def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment info.
        
        When using tool_registry (new architecture), returns Gateway info.
        Otherwise returns direct VM MCP info (legacy).
        """
        from .mcp_client import get_mcp_url
        import os
        
        # New architecture: use Gateway URL
        if self.tool_registry is not None:
            gateway_port = int(os.getenv("NOVAIC_PORT", "19999"))
            return {
                "mcp_port": gateway_port,
                "mcp_url": f"http://127.0.0.1:{gateway_port}/mcp",
                "executor_healthy": len(self.tools) > 0,  # Healthy if we have any tools
                "tools_count": len(self.tools),
                "skills_count": len(self.skills),
                "skills": [s.name for s in self.skills.values()],
            }
        
        # Legacy: direct VM connection
        return {
            "mcp_port": self.mcp_port,
            "mcp_url": get_mcp_url(self.mcp_port),
            "executor_healthy": self._executor_healthy,
            "tools_count": len(self.tools),
            "skills_count": len(self.skills),
            "skills": [s.name for s in self.skills.values()],
        }
    
    # ==================== Session Persistence ====================
    
    def _save_session(self) -> None:
        """
        保存当前会话到磁盘（增量保存）
        
        只保存自上次保存以来的新消息，避免重复写入。
        """
        messages = self.session.get_all_messages()
        new_messages = messages[self._last_saved_msg_count:]
        
        if not new_messages:
            print(f"[Agent] No new messages to save for session '{self.session_key}'")
            return
        
        for msg in new_messages:
            try:
                timestamp = None
                if "timestamp" in msg:
                    timestamp = datetime.fromisoformat(msg["timestamp"])
                
                self.storage.save_message(
                    session_key=self.session_key,
                    role=msg.get("role", "unknown"),
                    content=msg.get("content", ""),
                    timestamp=timestamp,
                    metadata=msg.get("metadata"),
                )
            except Exception as e:
                print(f"[Agent] Error saving message: {e}")
        
        self._last_saved_msg_count = len(messages)
        print(f"[Agent] Saved {len(new_messages)} new messages to session '{self.session_key}' (total: {self._last_saved_msg_count})")
    
    def restore_session(self) -> bool:
        """
        从磁盘恢复之前的会话。
        
        加载逻辑：
        1. 如果有 compaction summary，加载它作为历史摘要
        2. 加载 compaction 之后的所有消息
        
        Returns:
            True if session was restored, False if no previous session
        """
        if self._session_restored:
            print(f"[Agent] Session '{self.session_key}' already restored")
            return True
        
        if not self.storage.session_exists(self.session_key):
            print(f"[Agent] No previous session found for '{self.session_key}'")
            return False
        
        try:
            # 加载完整会话（包括 compaction summaries）
            entries = self.storage.load_full_session(self.session_key)
            
            if not entries:
                print(f"[Agent] Session file exists but is empty for '{self.session_key}'")
                return False
            
            # 找到最后一个 compaction summary
            last_compaction_idx = -1
            last_compaction = None
            for i, entry in enumerate(entries):
                if entry.get("type") == "compaction_summary":
                    last_compaction_idx = i
                    last_compaction = entry
            
            # 构建恢复的消息列表
            restored_messages = []
            
            # 如果有 compaction summary，加载它
            if last_compaction:
                restored_messages.append({
                    "role": "system",
                    "content": f"[Previous conversation summary]\n\n{last_compaction.get('summary', '')}",
                    "timestamp": last_compaction.get("timestamp", datetime.now().isoformat()),
                })
                
                # 只加载 compaction 之后的消息
                messages_to_load = entries[last_compaction_idx + 1:]
            else:
                # 没有 compaction，加载所有消息
                messages_to_load = entries
            
            # 加载消息（跳过 compaction_summary 类型）
            for entry in messages_to_load:
                if entry.get("type") == "message":
                    restored_messages.append({
                        "role": entry.get("role", "user"),
                        "content": entry.get("content", ""),
                        "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                    })
            
            # 恢复到 session manager
            self.session.messages = restored_messages
            self._last_saved_msg_count = len(restored_messages)
            self._session_restored = True
            
            print(f"[Agent] Restored session '{self.session_key}': {len(restored_messages)} messages"
                  + (f" (with compaction summary)" if last_compaction else ""))
            
            return True
            
        except Exception as e:
            print(f"[Agent] Error restoring session '{self.session_key}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==================== Parameter Validation ====================
    
    def _get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具的 schema"""
        for tool in self.tools:
            if tool.get("function", {}).get("name") == tool_name:
                return tool.get("function", {}).get("parameters", {})
        return None
    
    def _parse_tool_arguments(self, func: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        安全解析工具调用的 arguments
        
        处理各种边界情况：
        - arguments 是 None
        - arguments 是空字符串
        - arguments 不是有效的 JSON
        - arguments 解析后不是 dict
        
        Args:
            func: LLM 返回的 function 对象
            tool_name: 工具名称（用于日志）
        
        Returns:
            解析后的参数字典
        """
        raw_args = func.get("arguments")
        
        # 调试日志：打印原始 arguments
        print(f"[Agent] Tool '{tool_name}' raw arguments: {repr(raw_args)}")
        
        # 处理 None、空字符串、非字符串的情况
        if raw_args is None:
            print(f"[Agent] Warning: '{tool_name}' arguments is None")
            return {}
        
        if not isinstance(raw_args, str):
            # 如果已经是 dict，直接返回
            if isinstance(raw_args, dict):
                return raw_args
            print(f"[Agent] Warning: '{tool_name}' arguments is not a string: {type(raw_args)}")
            return {}
        
        if not raw_args.strip():
            print(f"[Agent] Warning: '{tool_name}' arguments is empty string")
            return {}
        
        try:
            parsed = json.loads(raw_args)
            if not isinstance(parsed, dict):
                print(f"[Agent] Warning: '{tool_name}' parsed arguments is not a dict: {type(parsed)}")
                return {}
            return parsed
        except json.JSONDecodeError as e:
            print(f"[Agent] Error parsing '{tool_name}' arguments: {e}, raw: {repr(raw_args)}")
            return {}
    
    def _validate_tool_input(self, tool_name: str, tool_input: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证工具输入参数
        
        Returns:
            (is_valid, error_message)
        """
        schema = self._get_tool_schema(tool_name)
        if not schema:
            return True, ""  # 找不到 schema，跳过验证
        
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # 检查必需参数
        missing = []
        for param in required:
            if param not in tool_input or tool_input[param] is None:
                # 获取参数描述以提供更好的错误信息
                param_desc = properties.get(param, {}).get("description", "")
                missing.append(f"'{param}'" + (f" ({param_desc})" if param_desc else ""))
        
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        
        return True, ""
    
    def _create_validation_error_result(self, tool_name: str, error: str) -> Dict[str, Any]:
        """创建参数验证错误的结果"""
        # 获取工具 schema 以提供使用示例
        schema = self._get_tool_schema(tool_name)
        example = ""
        
        if schema:
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # 生成简单的使用示例
            example_params = {}
            for param in required[:3]:  # 只显示前 3 个必需参数
                param_type = properties.get(param, {}).get("type", "string")
                if param_type == "string":
                    example_params[param] = f"<{param}>"
                elif param_type == "integer":
                    example_params[param] = 0
                elif param_type == "boolean":
                    example_params[param] = True
            
            if example_params:
                example = f"\n\nExample: {tool_name}({', '.join(f'{k}={repr(v)}' for k, v in example_params.items())})"
        
        return {
            "success": False,
            "error": f"Parameter validation error: {error}{example}",
            "observation": f"Tool '{tool_name}' was called with invalid parameters. Please provide all required parameters."
        }
    
    async def _call_llm_with_retry(
        self, 
        messages: List[Dict[str, Any]], 
        model: str,
        provider: str,
        api_base: str,
        api_key: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Call LLM with automatic retry on timeout."""
        max_retries = self.llm_max_retries
        last_error = None
        
        llm_client = self._get_llm_client(provider=provider, api_base=api_base, api_key=api_key)
        
        print(f"[Agent] Using provider: {provider}, api_base: {api_base}, model: {model}")
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[Agent] LLM call attempt {attempt}/{max_retries}")
                response = await llm_client.chat(
                    messages=messages,
                    tools=tools,
                    model=model,
                    max_tokens=self.max_tokens
                )
                return response
            except LLMError as e:
                last_error = e
                error_str = str(e).lower()
                
                if 'timeout' in error_str or 'rate' in error_str or '429' in error_str:
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        print(f"[Agent] LLM request failed (attempt {attempt}): {e}")
                        print(f"[Agent] Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"[Agent] LLM request failed after {max_retries} attempts: {e}")
                        raise
                else:
                    raise
        
        raise last_error or LLMError("Unknown error")
    
    async def chat(
        self, 
        user_message: str, 
        model: str = None,
        provider: str = None,
        api_base: str = None,
        api_key: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message and return responses.
        
        增强功能:
        - 自动加载相关 Skills
        - 任务追踪和可观测性
        - 目标评估
        """
        self._interrupted = False
        
        if not self._tools_initialized:
            await self.initialize()
        
        env_info = await self.get_environment_info()
        if env_info["tools_count"] == 0:
            # Only show warning if we have NO tools at all
            if self.tool_registry:
                # New architecture: show which servers are unavailable
                stats = self.tool_registry.get_stats()
                servers_info = stats.get("tools_by_server", {})
                unavailable = [k for k, v in servers_info.items() if v == 0]
                if unavailable:
                    yield {
                        "type": "warning",
                        "data": f"⚠️ MCP servers not ready: {', '.join(unavailable)}"
                    }
                else:
                    yield {
                        "type": "warning",
                        "data": f"⚠️ No MCP tools available"
                    }
            else:
                # Legacy: direct VM connection
                yield {
                    "type": "warning",
                    "data": f"⚠️ Executor service not available at {env_info['mcp_url']} (MCP tools: 0)"
                }
        
        # 加载相关 Skills
        relevant_skills = await self._load_relevant_skills(user_message)
        if relevant_skills:
            yield {
                "type": "skills_loaded",
                "data": {"skills": [s.name for s in relevant_skills]}
            }
        
        # Check for session compaction
        try:
            compaction_result = await self._check_compaction(model, provider, api_base, api_key)
            if compaction_result and compaction_result.get("stats", {}).get("compacted"):
                yield {
                    "type": "status",
                    "data": {"message": f"📦 Session compacted: saved {compaction_result['stats']['tokens_saved']} tokens"}
                }
        except Exception as e:
            print(f"[Agent] Compaction check failed (non-fatal): {e}")
        
        try:
            if self.api_style == "responses":
                async for event in self._chat_responses_style(
                    user_message, 
                    model=model, 
                    provider=provider, 
                    api_base=api_base, 
                    api_key=api_key,
                    skills=relevant_skills
                ):
                    yield event
                    # Save session when task completes
                    if event.get("type") == "final":
                        self._save_session()
            else:
                async for event in self._chat_completions_style(
                    user_message, 
                    model=model, 
                    provider=provider, 
                    api_base=api_base, 
                    api_key=api_key,
                    skills=relevant_skills
                ):
                    yield event
                    # Save session when task completes
                    if event.get("type") in ("final", "error"):
                        self._save_session()
        except Exception as e:
            self._save_session()
            raise
    
    async def _chat_completions_style(
        self, 
        user_message: str, 
        model: str = None,
        provider: str = None,
        api_base: str = None,
        api_key: str = None,
        skills: List[MCPSkill] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        OpenAI chat/completions style - ReAct Loop.
        
        增强功能:
        - 动态注入相关 Skills 到 system prompt
        - 完整的工具调用追踪
        - 目标评估
        """
        self.session.add_user_message(user_message)
        
        # 构建增强的 system prompt（包含相关 Skills）
        system_prompt = self._build_enhanced_system_prompt(skills or [])
        
        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.session.get_messages_for_llm()
        
        iteration = 0
        
        # 无限循环，依赖 Agent 自主调用 agent_rest() 结束任务
        # 上下文压缩机制会自动管理 context window
        while not self._interrupted:
            iteration += 1
            
            # 定期检查 context compaction (在 loop 内部)
            if iteration % self.compaction_check_interval == 0:
                try:
                    compaction_result = await self._check_compaction(model, provider, api_base, api_key)
                    if compaction_result and compaction_result.get("stats", {}).get("compacted"):
                        # 更新 messages 列表
                        messages = [
                            {"role": "system", "content": system_prompt}
                        ] + self.session.get_messages_for_llm()
                        yield {
                            "type": "status",
                            "data": {"message": f"📦 [Iteration {iteration}] Context compacted: saved {compaction_result['stats']['tokens_saved']} tokens"}
                        }
                except Exception as e:
                    print(f"[Agent] Compaction check failed at iteration {iteration} (non-fatal): {e}")
            
            # 每轮都检查收件箱（自主调度支持）
            inbox_context = await self._get_inbox_context()
            if inbox_context:
                # 注入为 system 消息，提醒 Agent 检查收件箱
                messages.append({
                    "role": "system",
                    "content": inbox_context
                })
                yield {"type": "status", "data": f"[Iteration {iteration}] 收件箱有新消息"}
            
            try:
                response = await self._call_llm_with_retry(
                    messages=messages,
                    model=model,
                    provider=provider,
                    api_base=api_base,
                    api_key=api_key,
                    tools=self.tools
                )
                
                choice = response.get("choices", [{}])[0]
                message = choice.get("message", {})
                finish_reason = choice.get("finish_reason")
                
                content = message.get("content") or ""
                tool_calls = message.get("tool_calls") or []
                # 通用提取 reasoning_content (支持 kimi/deepseek 等)
                reasoning_content = message.get("reasoning_content")
                
                print(f"[Agent] LLM response - iteration: {iteration}, "
                      f"content: {content[:200] if content else '(empty)'}, "
                      f"tool_calls: {len(tool_calls)}, finish_reason: {finish_reason}"
                      f"{', has_reasoning' if reasoning_content else ''}")
                
                if tool_calls:
                    # 如果有 reasoning_content，优先展示；否则展示 content
                    thinking_text = reasoning_content or content
                    if thinking_text:
                        yield {"type": "thinking", "data": thinking_text}
                    else:
                        tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                        yield {"type": "thinking", "data": f"Executing: {', '.join(tool_names)}"}
                
                # 修复：有些 API 返回 finish_reason 可能不是 "tool_calls"
                # 只要有 tool_calls 就应该执行
                if tool_calls:
                    assistant_msg = {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": tool_calls
                    }
                    # 透传 reasoning_content (kimi/deepseek 需要)
                    if reasoning_content:
                        assistant_msg["reasoning_content"] = reasoning_content
                    messages.append(assistant_msg)
                    
                    for tool_call in tool_calls:
                        if self._interrupted:
                            break
                        
                        func = tool_call.get("function", {})
                        tool_name = func.get("name")
                        tool_id = tool_call.get("id")
                        
                        # 安全解析 arguments（修复空参数 bug）
                        tool_input = self._parse_tool_arguments(func, tool_name)
                        
                        yield {
                            "type": "tool_start",
                            "data": {"tool": tool_name, "input": tool_input, "id": tool_id}
                        }
                        
                        # 验证参数
                        is_valid, validation_error = self._validate_tool_input(tool_name, tool_input)
                        
                        if not is_valid:
                            # 参数验证失败，返回清晰的错误信息让 LLM 重试
                            print(f"[Agent] Parameter validation failed for {tool_name}: {validation_error}")
                            result = self._create_validation_error_result(tool_name, validation_error)
                            tool_content = json.dumps(result, ensure_ascii=False)
                        else:
                            # 执行工具调用 (via ToolRegistry or direct MCPClient)
                            mcp_result = await self._execute_tool(tool_name, tool_input)
                            result = self._convert_mcp_result(mcp_result)
                            tool_content = self._convert_result_to_llm_content(result)
                        
                        yield {
                            "type": "tool_end",
                            "data": {
                                "tool": tool_name, 
                                "result": result, 
                                "result_summary": result,
                                "success": result.get("success", False),
                            }
                        }
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": tool_content
                        })
                    
                else:
                    # 任务可能完成，但先检查 inbox 是否有新消息
                    inbox_context = await self._get_inbox_context()
                    if inbox_context:
                        # 有新消息！注入到 context 并继续处理
                        print(f"[Agent] Task complete but inbox has new messages, continuing...")
                        messages.append({
                            "role": "system",
                            "content": inbox_context
                        })
                        # 添加当前回复到消息历史，然后继续
                        self.session.add_assistant_message(content)
                        messages.append({"role": "assistant", "content": content})
                        yield {"type": "status", "data": "📬 检测到新消息，继续处理..."}
                        # 不 break，继续循环处理新消息
                    else:
                        # 没有新消息，真正完成
                        self.session.add_assistant_message(content)
                        yield {"type": "final", "data": content}
                        break
                    
            except LLMError as e:
                yield {"type": "error", "data": {"error": str(e)}}
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield {"type": "error", "data": {"error": f"Unexpected error: {str(e)}"}}
                break
    
    async def _chat_responses_style(
        self, 
        user_message: str, 
        model: str = None,
        provider: str = None,
        api_base: str = None,
        api_key: str = None,
        skills: List[MCPSkill] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Doubao responses API style.
        
        增强功能:
        - 动态注入相关 Skills
        - 完整的工具调用追踪
        """
        self.session.add_user_message(user_message)
        
        # 构建增强的 system prompt
        system_prompt = self._build_enhanced_system_prompt(skills or [])
        
        if not self._response_id:
            input_msgs = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        else:
            input_msgs = [{"role": "user", "content": user_message}]
        
        iteration = 0
        
        # 无限循环，依赖 Agent 自主调用 agent_rest() 结束任务
        while not self._interrupted:
            iteration += 1
            
            # 定期检查 context compaction (在 loop 内部)
            # responses API 模式下，compaction 会更新 session，但不影响 _response_id 链
            if iteration % self.compaction_check_interval == 0:
                try:
                    compaction_result = await self._check_compaction(model, provider, api_base, api_key)
                    if compaction_result and compaction_result.get("stats", {}).get("compacted"):
                        yield {
                            "type": "status",
                            "data": {"message": f"📦 [Iteration {iteration}] Context compacted: saved {compaction_result['stats']['tokens_saved']} tokens"}
                        }
                except Exception as e:
                    print(f"[Agent] Compaction check failed at iteration {iteration} (non-fatal): {e}")
            
            # 每轮都检查收件箱（自主调度支持）
            inbox_context = await self._get_inbox_context()
            if inbox_context:
                # 注入为用户消息（responses API 模式）
                input_msgs.append({
                    "role": "user",
                    "content": f"[系统通知]\n{inbox_context}"
                })
                yield {"type": "status", "data": f"[Iteration {iteration}] 收件箱有新消息"}
            
            try:
                llm_client = self._get_llm_client(provider=provider, api_base=api_base, api_key=api_key)
                
                response = await llm_client.responses_create(
                    input=input_msgs,
                    tools=self.tools,
                    previous_response_id=self._response_id,
                    max_tokens=self.max_tokens
                )
                
                self._response_id = response.get("id")
                content, tool_calls, finish_reason = self._parse_responses_output(response)
                
                if tool_calls:
                    if content:
                        yield {"type": "thinking", "data": content}
                    else:
                        tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                        yield {"type": "thinking", "data": f"Executing: {', '.join(tool_names)}"}
                
                if tool_calls:
                    tool_results_input = []
                    
                    for tool_call in tool_calls:
                        if self._interrupted:
                            break
                        
                        func = tool_call.get("function", {})
                        tool_name = func.get("name")
                        tool_id = tool_call.get("id")
                        
                        # 安全解析 arguments（修复空参数 bug）
                        tool_input = self._parse_tool_arguments(func, tool_name)
                        
                        yield {
                            "type": "tool_start",
                            "data": {"tool": tool_name, "input": tool_input, "id": tool_id}
                        }
                        
                        # 验证参数
                        is_valid, validation_error = self._validate_tool_input(tool_name, tool_input)
                        
                        if not is_valid:
                            # 参数验证失败，返回清晰的错误信息让 LLM 重试
                            print(f"[Agent] Parameter validation failed for {tool_name}: {validation_error}")
                            result = self._create_validation_error_result(tool_name, validation_error)
                            tool_content = json.dumps(result, ensure_ascii=False)
                        else:
                            # 执行工具调用 (via ToolRegistry or direct MCPClient)
                            mcp_result = await self._execute_tool(tool_name, tool_input)
                            result = self._convert_mcp_result(mcp_result)
                            tool_content = self._convert_result_to_llm_content(result)
                        
                        yield {
                            "type": "tool_end",
                            "data": {
                                "tool": tool_name, 
                                "result": result, 
                                "result_summary": result,
                                "success": result.get("success", False),
                            }
                        }
                        
                        tool_results_input.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": tool_content
                        })
                    
                    input_msgs = tool_results_input
                    
                else:
                    # 任务可能完成，但先检查 inbox 是否有新消息
                    inbox_context = await self._get_inbox_context()
                    if inbox_context:
                        # 有新消息！注入到 context 并继续处理
                        print(f"[Agent] Task complete but inbox has new messages, continuing...")
                        input_msgs = [{
                            "role": "user",
                            "content": f"[系统通知]\n{inbox_context}"
                        }]
                        # 添加当前回复到 session
                        self.session.add_assistant_message(content)
                        yield {"type": "status", "data": "📬 检测到新消息，继续处理..."}
                        # 不 break，继续循环处理新消息
                    else:
                        # 没有新消息，真正完成
                        self.session.add_assistant_message(content)
                        yield {"type": "final", "data": content}
                        break
                    
            except LLMError as e:
                yield {"type": "error", "data": {"error": str(e)}}
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield {"type": "error", "data": {"error": f"Unexpected error: {str(e)}"}}
                break
    
    def _convert_mcp_result(self, mcp_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP response to standard format."""
        if "success" in mcp_result or "observation" in mcp_result:
            return mcp_result
        return {"success": True, "observation": mcp_result}
    
    def _convert_result_to_llm_content(self, result: Dict[str, Any]) -> Any:
        """Convert tool result to LLM-compatible format."""
        screenshot = None
        
        # Check for screenshot in various locations
        for key in ["screenshot", "image"]:
            if key in result and isinstance(result[key], str):
                screenshot = result[key]
                break
        
        if not screenshot:
            for container_key in ["observation", "output"]:
                if container_key in result and isinstance(result[container_key], dict):
                    container = result[container_key]
                    for key in ["screenshot", "image"]:
                        if key in container and isinstance(container[key], str):
                            screenshot = container[key]
                            break
                    if screenshot:
                        break
        
        if screenshot and len(screenshot) > 100:
            text_result = {}
            for key, value in result.items():
                if key in ("screenshot", "image"):
                    continue
                elif key in ("observation", "output") and isinstance(value, dict):
                    filtered = {k: v for k, v in value.items() if k not in ("screenshot", "image")}
                    if filtered:
                        text_result[key] = filtered
                else:
                    text_result[key] = value
            
            content = []
            
            if text_result:
                text_content = json.dumps(text_result, ensure_ascii=False)
                if len(text_content) > 5000:
                    text_content = text_content[:5000] + f"... [truncated, total {len(text_content)} chars]"
                content.append({"type": "text", "text": text_content})
            
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{screenshot}"}
            })
            
            return content
        else:
            simplified = {}
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 5000:
                    simplified[key] = value[:5000] + f"... [truncated, total {len(value)} chars]"
                elif isinstance(value, dict):
                    simplified[key] = self._simplify_dict_for_llm(value)
                else:
                    simplified[key] = value
            
            return json.dumps(simplified, ensure_ascii=False)
    
    def _simplify_dict_for_llm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simplify dict for LLM, removing screenshots and truncating long strings."""
        simplified = {}
        for key, value in data.items():
            if key in ("screenshot", "image") and isinstance(value, str):
                continue
            elif isinstance(value, str) and len(value) > 5000:
                simplified[key] = value[:5000] + f"... [truncated, total {len(value)} chars]"
            elif isinstance(value, dict):
                simplified[key] = self._simplify_dict_for_llm(value)
            else:
                simplified[key] = value
        return simplified
    
    def _parse_responses_output(self, response: Dict[str, Any]) -> tuple:
        """Parse Doubao responses API output format."""
        content = ""
        tool_calls = []
        finish_reason = "stop"
        
        output = response.get("output", [])
        
        for item in output:
            item_type = item.get("type", "")
            
            if item_type == "message":
                content_list = item.get("content", [])
                for content_item in content_list:
                    if content_item.get("type") == "text":
                        content += content_item.get("text", "")
                        
            elif item_type == "function_call":
                func_info = item.get("function", {})
                tool_call = {
                    "id": item.get("id", f"call_{len(tool_calls)}"),
                    "type": "function",
                    "function": {
                        "name": func_info.get("name", ""),
                        "arguments": func_info.get("arguments", "{}")
                    }
                }
                tool_calls.append(tool_call)
                finish_reason = "tool_calls"
                
            elif item_type == "text":
                content += item.get("text", "")
        
        if tool_calls:
            finish_reason = "tool_calls"
        
        return content, tool_calls, finish_reason
    
    async def chat_with_logs(
        self, 
        user_message: str, 
        model: str = None,
        provider: str = None,
        api_base: str = None,
        api_key: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Chat with detailed execution logs."""
        async for event in self.chat(
            user_message, model=model, provider=provider, api_base=api_base, api_key=api_key
        ):
            yield event
            
            if event["type"] == "tool_start":
                yield {
                    "type": "status",
                    "data": {"message": f"🔧 Executing {event['data']['tool']}..."}
                }
            elif event["type"] == "tool_end":
                success = event['data'].get('result', {}).get('success', False)
                status = "✅" if success else "❌"
                yield {
                    "type": "status",
                    "data": {"message": f"{status} {event['data']['tool']} completed"}
                }

    async def simple_chat(
        self, 
        user_message: str, 
        model: str = None,
        provider: str = None,
        api_base: str = None,
        api_key: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Simple chat mode without tools."""
        self._interrupted = False
        self.session.add_user_message(user_message)
        
        simple_system = """You are a helpful AI assistant. Provide clear, concise, and accurate responses.
You do not have access to any tools in this mode - just engage in conversation."""
        
        messages = [
            {"role": "system", "content": simple_system}
        ] + self.session.get_messages_for_llm()
        
        try:
            response = await self._call_llm_with_retry(
                messages=messages,
                model=model,
                provider=provider,
                api_base=api_base,
                api_key=api_key,
                tools=None
            )
            
            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content") or ""
            
            self.session.add_assistant_message(content)
            
            yield {"type": "final", "data": {"content": content}}
            
        except Exception as e:
            print(f"[Agent] Simple chat error: {e}")
            yield {"type": "error", "data": {"error": str(e)}}
    
    def interrupt(self) -> None:
        """Interrupt current execution and save session."""
        self._interrupted = True
        # 保存会话到磁盘
        self._save_session()
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get chat history."""
        return self.session.get_all_messages()
    
    def clear_messages(self) -> None:
        """Clear chat history and reset response chain."""
        # 先保存当前会话
        self._save_session()
        
        # 归档当前会话文件
        if self.storage.session_exists(self.session_key):
            self.storage.archive_session(self.session_key)
            print(f"[Agent] Archived session '{self.session_key}'")
        
        # 清除内存中的会话
        self.session.clear()
        self._response_id = None
        self._last_saved_msg_count = 0
        self._session_restored = False
        
        for client in self._llm_clients.values():
            if hasattr(client, 'reset_response_chain'):
                client.reset_response_chain()
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.mcp_client:
            await self.mcp_client.close()
