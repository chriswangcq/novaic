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
from ..session.manager import SessionManager
from executor.mcp_client import MCPClient, MCPSkill, get_mcp_url


# ==================== Data Classes ====================

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class ToolCallTrace:
    """工具调用追踪"""
    id: str
    tool_name: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


@dataclass
class AgentStep:
    """Agent 单步执行记录"""
    iteration: int
    reasoning: str = ""  # LLM 的思考内容
    tool_calls: List[ToolCallTrace] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TaskTrace:
    """任务执行追踪"""
    task_id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    steps: List[AgentStep] = field(default_factory=list)
    skills_used: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于日志/审计）"""
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "status": self.status.value,
            "steps_count": len(self.steps),
            "skills_used": self.skills_used,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": int((self.completed_at - self.started_at).total_seconds() * 1000) 
                          if self.completed_at and self.started_at else None,
            "final_result": self.final_result[:500] if self.final_result else None,
            "error": self.error
        }


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
    
    def __init__(self, mcp_port: int):
        """
        Initialize the Agent.
        
        Args:
            mcp_port: MCP Server 端口 (QEMU 转发的端口)
        """
        self.mcp_port = mcp_port
        
        # Cache for LLM clients (cache_key -> client)
        self._llm_clients: Dict[str, BaseLLMClient] = {}
        
        # Initialize other components
        self.session = SessionManager()
        self.mcp_client = MCPClient()
        
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
        
        # Task tracking (可观测性)
        self._current_trace: Optional[TaskTrace] = None
        self._trace_history: List[TaskTrace] = []  # 最近的任务追踪
        self._max_trace_history = 10
    
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
        Initialize Agent: discover tools and skills from MCP Server.
        
        MCP 三元组完整初始化:
        - Tools: 可执行的动作
        - Resources/Skills: 领域知识和工作流指导
        - Prompts: 预定义模板（如果有）
        """
        if self._tools_initialized and len(self.tools) > 0:
            print(f"[Agent] Already initialized with {len(self.tools)} tools")
            return
        
        mcp_url = get_mcp_url(self.mcp_port)
        print(f"[Agent] ========== MCP Initialize Start ==========")
        print(f"[Agent] MCP URL: {mcp_url}")
        print(f"[Agent] MCP Port: {self.mcp_port}")
        
        try:
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
            
            # 发现 Skills (从 Resources)
            print(f"[Agent] Discovering skills...")
            await self._discover_skills()
            
            if len(self.tools) > 0:
                self._executor_healthy = True
                self._tools_initialized = True  # 只有成功发现工具才标记为已初始化
                print(f"[Agent] ✓ Initialized successfully: {len(self.tools)} tools, {len(self.skills)} skills")
            else:
                self._executor_healthy = False
                print(f"[Agent] ✗ MCP Server connected but NO TOOLS discovered!")
                print(f"[Agent] Check if MCP server is running at {mcp_url}")
                
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
        """Get current environment info."""
        return {
            "mcp_port": self.mcp_port,
            "mcp_url": get_mcp_url(self.mcp_port),
            "executor_healthy": self._executor_healthy,
            "tools_count": len(self.tools),
            "skills_count": len(self.skills),
            "skills": [s.name for s in self.skills.values()],
        }
    
    # ==================== Task Tracking ====================
    
    def _start_task_trace(self, goal: str) -> TaskTrace:
        """开始新的任务追踪"""
        trace = TaskTrace(
            task_id=str(uuid.uuid4())[:8],
            goal=goal,
            status=TaskStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        self._current_trace = trace
        return trace
    
    def _complete_task_trace(self, result: str = None, error: str = None) -> None:
        """完成当前任务追踪"""
        if not self._current_trace:
            return
        
        self._current_trace.completed_at = datetime.now()
        self._current_trace.final_result = result
        self._current_trace.error = error
        
        if error:
            self._current_trace.status = TaskStatus.FAILED
        elif self._interrupted:
            self._current_trace.status = TaskStatus.INTERRUPTED
        else:
            self._current_trace.status = TaskStatus.COMPLETED
        
        # 保存到历史
        self._trace_history.append(self._current_trace)
        if len(self._trace_history) > self._max_trace_history:
            self._trace_history = self._trace_history[-self._max_trace_history:]
        
        # 打印追踪摘要
        trace_summary = self._current_trace.to_dict()
        print(f"[Agent] Task completed: {json.dumps(trace_summary, ensure_ascii=False)}")
        
        self._current_trace = None
    
    def _add_step_to_trace(self, iteration: int, reasoning: str = "") -> AgentStep:
        """添加步骤到当前追踪"""
        if not self._current_trace:
            return AgentStep(iteration=iteration)
        
        step = AgentStep(iteration=iteration, reasoning=reasoning)
        self._current_trace.steps.append(step)
        return step
    
    def _add_tool_call_to_step(
        self, 
        step: AgentStep, 
        tool_name: str, 
        tool_input: Dict[str, Any],
        tool_id: str
    ) -> ToolCallTrace:
        """添加工具调用到步骤"""
        trace = ToolCallTrace(
            id=tool_id,
            tool_name=tool_name,
            input=tool_input,
            started_at=datetime.now()
        )
        step.tool_calls.append(trace)
        return trace
    
    def _complete_tool_call_trace(
        self, 
        trace: ToolCallTrace, 
        output: Dict[str, Any],
        success: bool,
        error: str = None
    ) -> None:
        """完成工具调用追踪"""
        trace.completed_at = datetime.now()
        trace.output = output
        trace.success = success
        trace.error = error
        if trace.started_at:
            trace.duration_ms = int((trace.completed_at - trace.started_at).total_seconds() * 1000)
    
    def get_trace_history(self) -> List[Dict[str, Any]]:
        """获取任务追踪历史"""
        return [trace.to_dict() for trace in self._trace_history]
    
    def get_current_trace(self) -> Optional[Dict[str, Any]]:
        """获取当前任务追踪"""
        return self._current_trace.to_dict() if self._current_trace else None
    
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
        
        # 开始任务追踪
        trace = self._start_task_trace(user_message)
        
        env_info = await self.get_environment_info()
        if not env_info["executor_healthy"] or env_info["tools_count"] == 0:
            yield {
                "type": "warning",
                "data": f"⚠️ Executor service not available at {env_info['mcp_url']} (MCP tools: {env_info['tools_count']})"
            }
        
        # 加载相关 Skills
        relevant_skills = await self._load_relevant_skills(user_message)
        if relevant_skills:
            trace.skills_used = [s.name for s in relevant_skills]
            yield {
                "type": "skills_loaded",
                "data": {"skills": [s.name for s in relevant_skills]}
            }
        
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
                    # 提取最终结果用于追踪
                    if event.get("type") == "final":
                        self._complete_task_trace(result=event.get("data"))
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
                    # 提取最终结果用于追踪
                    if event.get("type") == "final":
                        self._complete_task_trace(result=event.get("data"))
                    elif event.get("type") == "error":
                        self._complete_task_trace(error=str(event.get("data", {}).get("error")))
        except Exception as e:
            self._complete_task_trace(error=str(e))
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
        
        while not self._interrupted and iteration < self.max_iterations:
            iteration += 1
            
            # 创建步骤追踪
            current_step = self._add_step_to_trace(iteration)
            
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
                
                # 记录 reasoning
                current_step.reasoning = content
                
                print(f"[Agent] LLM response - iteration: {iteration}, "
                      f"content: {content[:200] if content else '(empty)'}, "
                      f"tool_calls: {len(tool_calls)}, finish_reason: {finish_reason}")
                
                if tool_calls:
                    if content:
                        yield {"type": "thinking", "data": content}
                    else:
                        tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                        yield {"type": "thinking", "data": f"Executing: {', '.join(tool_names)}"}
                
                # 修复：有些 API 返回 finish_reason 可能不是 "tool_calls"
                # 只要有 tool_calls 就应该执行
                if tool_calls:
                    messages.append({
                        "role": "assistant",
                        "content": content,
                        "tool_calls": tool_calls
                    })
                    
                    for tool_call in tool_calls:
                        if self._interrupted:
                            break
                        
                        func = tool_call.get("function", {})
                        tool_name = func.get("name")
                        tool_id = tool_call.get("id")
                        
                        # 安全解析 arguments（修复空参数 bug）
                        tool_input = self._parse_tool_arguments(func, tool_name)
                        
                        # 开始工具调用追踪
                        tool_trace = self._add_tool_call_to_step(
                            current_step, tool_name, tool_input, tool_id
                        )
                        
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
                            self._complete_tool_call_trace(tool_trace, result, False, validation_error)
                        else:
                            # 执行工具调用
                            mcp_result = await self.mcp_client.call_tool(tool_name, tool_input)
                            result = self._convert_mcp_result(mcp_result)
                            tool_content = self._convert_result_to_llm_content(result)
                            
                            # 完成工具调用追踪
                            success = result.get("success", False)
                            error = result.get("error") if not success else None
                            self._complete_tool_call_trace(tool_trace, result, success, error)
                        
                        yield {
                            "type": "tool_end",
                            "data": {
                                "tool": tool_name, 
                                "result": result, 
                                "result_summary": result,
                                "success": result.get("success", False),
                                "duration_ms": tool_trace.duration_ms
                            }
                        }
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": tool_content
                        })
                    
                else:
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
        
        if iteration >= self.max_iterations:
            yield {"type": "warning", "data": "⚠️ Maximum iterations reached. Task may be incomplete."}
    
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
        
        while not self._interrupted and iteration < self.max_iterations:
            iteration += 1
            
            # 创建步骤追踪
            current_step = self._add_step_to_trace(iteration)
            
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
                
                # 记录 reasoning
                current_step.reasoning = content
                
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
                        
                        # 开始工具调用追踪
                        tool_trace = self._add_tool_call_to_step(
                            current_step, tool_name, tool_input, tool_id
                        )
                        
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
                            self._complete_tool_call_trace(tool_trace, result, False, validation_error)
                        else:
                            # 执行工具调用
                            mcp_result = await self.mcp_client.call_tool(tool_name, tool_input)
                            result = self._convert_mcp_result(mcp_result)
                            tool_content = self._convert_result_to_llm_content(result)
                            
                            # 完成工具调用追踪
                            success = result.get("success", False)
                            error = result.get("error") if not success else None
                            self._complete_tool_call_trace(tool_trace, result, success, error)
                        
                        yield {
                            "type": "tool_end",
                            "data": {
                                "tool": tool_name, 
                                "result": result, 
                                "result_summary": result,
                                "success": result.get("success", False),
                                "duration_ms": tool_trace.duration_ms
                            }
                        }
                        
                        tool_results_input.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": tool_content
                        })
                    
                    input_msgs = tool_results_input
                    
                else:
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
        
        if iteration >= self.max_iterations:
            yield {"type": "warning", "data": "⚠️ Maximum iterations reached. Task may be incomplete."}
    
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
        """Interrupt current execution."""
        self._interrupted = True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get chat history."""
        return self.session.get_all_messages()
    
    def clear_messages(self) -> None:
        """Clear chat history and reset response chain."""
        self.session.clear()
        self._response_id = None
        for client in self._llm_clients.values():
            if hasattr(client, 'reset_response_chain'):
                client.reset_response_chain()
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.mcp_client:
            await self.mcp_client.close()
