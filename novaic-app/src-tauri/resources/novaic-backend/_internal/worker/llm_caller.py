"""
LLM Caller

Standalone LLM calling module for Worker processes.
Only handles LLM communication, does not execute tools.

v11: Created for multi-process architecture.
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import aiohttp

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import multimodal


class ActionType(str, Enum):
    """Types of actions Agent can decide on.
    
    v2.8: 只有 TOOL_CALL 和 DONE，reply 通过 chat_reply 工具实现
    """
    TOOL_CALL = "tool_call"
    DONE = "done"
    WAIT = "wait"


@dataclass
class AgentAction:
    """Represents a single action decided by the Agent.
    
    v2.8: 只有 TOOL_CALL 和 DONE 类型，reply 通过 chat_reply 工具
    """
    type: ActionType
    tool_name: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    tool_call_id: Optional[str] = None  # v12: LLM 返回的 tool_call.id，用于返回结果


@dataclass 
class ThinkingResult:
    """Result of Agent thinking."""
    actions: List[AgentAction]
    reasoning: str
    is_final: bool = False
    final_answer: Optional[str] = None
    mcp_session_id: Optional[str] = None  # Session ID for MCP tool calls


class LLMCaller:
    """
    Handles LLM communication for Agent thinking.
    
    This is a lightweight wrapper that:
    1. Builds prompts with tools schema
    2. Calls LLM API
    3. Parses response into actions
    
    Does NOT execute any tools.
    """
    
    def __init__(
        self,
        gateway_url: str,
        session: aiohttp.ClientSession,
        agent_id: str,
        mcp_gateway_url: Optional[str] = None,
    ):
        self.gateway_url = gateway_url
        self.mcp_gateway_url = mcp_gateway_url or gateway_url
        self.session = session
        self.agent_id = agent_id
        
        # LLM settings
        self.model: Optional[str] = None
        self.api_key: Optional[str] = None
        self.api_base: Optional[str] = None
        self.provider: Optional[str] = None
        
        # Tools schema
        self.tools: List[Dict[str, Any]] = []
        
        # MCP session ID for tool calls
        self.mcp_session_id: Optional[str] = None
        
        # Conversation history
        self.messages: List[Dict[str, Any]] = []
    
    async def initialize(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        provider: Optional[str] = None,
        mcp_url: Optional[str] = None,
    ):
        """
        Initialize LLM settings and load tools.
        
        Args:
            model: Model name
            api_key: API key
            api_base: API base URL
            provider: Provider name (openai, anthropic, google)
            mcp_url: Aggregate MCP URL (e.g. /mcp/aggregate/main-xxx)
        """
        self.model = model or "gpt-4o"
        self.api_key = api_key
        self.api_base = api_base
        self.provider = provider or "openai"
        self.mcp_url = mcp_url
        
        # Load tools schema from Runtime MCP
        await self._load_tools()
    
    async def _load_tools(self):
        """Load available tools from Runtime MCP server."""
        if not self.mcp_url:
            print(f"[LLMCaller] No MCP URL provided, skipping tool loading")
            self.tools = []
            return
        
        try:
            # mcp_url may be full URL (from MCP Gateway) or path (legacy)
            base = self.mcp_gateway_url
            if self.mcp_url.startswith("http://") or self.mcp_url.startswith("https://"):
                full_mcp_url = self.mcp_url
            else:
                full_mcp_url = f"{base.rstrip('/')}{self.mcp_url}" if self.mcp_url.startswith("/") else f"{base.rstrip('/')}/{self.mcp_url}"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
            
            # Step 1: Initialize MCP session to get session ID
            init_payload = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 1,
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "llm-caller", "version": "1.0"}
                }
            }
            
            async with self.session.post(
                full_mcp_url,
                json=init_payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    print(f"[LLMCaller] MCP initialize failed: {response.status}")
                    self.tools = []
                    return
                
                # Get session ID from header
                session_id = response.headers.get("mcp-session-id")
                if not session_id:
                    print(f"[LLMCaller] MCP initialize: no session ID returned")
                    self.tools = []
                    return
                
                # Save session ID for later tool calls
                self.mcp_session_id = session_id
                
                # Parse init response (to drain the stream)
                content_type = response.headers.get("Content-Type", "")
                if "text/event-stream" in content_type:
                    await self._parse_sse_response(response)
                else:
                    await response.json()
            
            # Step 2: Call tools/list with session ID
            headers["mcp-session-id"] = session_id
            
            async with self.session.post(
                full_mcp_url,
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 2},
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "")
                    
                    # Handle SSE response (text/event-stream)
                    if "text/event-stream" in content_type:
                        data = await self._parse_sse_response(response)
                    else:
                        # Regular JSON response
                        data = await response.json()
                    
                    # Check for errors
                    if "error" in data:
                        print(f"[LLMCaller] MCP tools/list error: {data['error']}")
                        self.tools = []
                        return
                    
                    # MCP protocol: result contains tools list
                    result = data.get("result", {})
                    self.tools = result.get("tools", [])
                    print(f"[LLMCaller] Loaded {len(self.tools)} tools from Runtime MCP: {self.mcp_url}")
                else:
                    print(f"[LLMCaller] Runtime MCP tools/list failed: {response.status}")
                    self.tools = []
        except Exception as e:
            print(f"[LLMCaller] Error loading tools from Runtime MCP: {e}")
            import traceback
            traceback.print_exc()
            self.tools = []
    
    async def _parse_sse_response(self, response) -> Dict[str, Any]:
        """
        Parse SSE (Server-Sent Events) response from MCP server.
        
        SSE format:
        event: message
        data: {"jsonrpc": "2.0", "result": {...}, "id": 1}
        
        Returns the last complete JSON-RPC response.
        """
        last_data = {}
        
        async for line in response.content:
            line = line.decode("utf-8").strip()
            
            # Skip empty lines and event lines
            if not line or line.startswith("event:"):
                continue
            
            # Parse data lines
            if line.startswith("data:"):
                json_str = line[5:].strip()
                if json_str:
                    try:
                        data = json.loads(json_str)
                        # Keep the last response with result or error
                        if "result" in data or "error" in data:
                            last_data = data
                    except json.JSONDecodeError:
                        continue
        
        return last_data
    
    async def _get_mcp_url(self) -> Optional[str]:
        """Get MCP server URL from agent configuration."""
        try:
            async with self.session.get(
                f"{self.gateway_url}/api/agents/{self.agent_id}",
            ) as response:
                if response.status == 200:
                    agent = await response.json()
                    # Get port configuration
                    ports = agent.get("ports", {})
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
                        
                        # Fallback: use agent index
                        agent_index = vm.get("agent_index", 0)
                        return f"http://localhost:{19900 + agent_index}"
        except Exception as e:
            print(f"[LLMCaller] Get MCP URL error: {e}")
        
        return None
    
    def set_system_prompt(self, system_prompt: str):
        """Set the system prompt."""
        # Remove existing system message if any
        self.messages = [m for m in self.messages if m.get("role") != "system"]
        # Add new system message at the beginning
        self.messages.insert(0, {"role": "system", "content": system_prompt})
    
    def add_user_message(self, content: str):
        """Add a user message to conversation."""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        """Add an assistant message to conversation."""
        self.messages.append({"role": "assistant", "content": content})
    
    def add_tool_result(self, tool_name: str, tool_call_id: str, result: Any):
        """
        Add a tool execution result to conversation.
        
        基于 MCP 协议的 _mcp_content 数组处理多模态内容：
        - 检查 _mcp_content 中的 type 字段
        - type="image" 的内容转换为 LLM 多模态格式
        - 图片作为单独的 user message 添加（LLM API 不支持在 tool result 中放图片）
        """
        # 使用通用工具检测和提取多模态内容
        images = []
        if isinstance(result, dict) and multimodal.has_images(result):
            _, images = multimodal.extract_from_result(result)
        
        # 生成纯文本版本（不含 base64）
        if images and isinstance(result, dict):
            result_str = multimodal.result_to_text_only(result)
        else:
            result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
        
        # Add tool result message (text only)
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result_str,
        })
        
        # 如果有图片，作为 user message 添加
        if images:
            self._add_images_message(images, tool_name)
    
    def _add_images_message(self, images: List[Dict[str, str]], tool_name: str):
        """
        将图片作为 user message 添加到对话中
        
        Args:
            images: 图片列表 [{"data": "base64...", "mime_type": "image/png"}, ...]
            tool_name: 工具名称（用于说明）
        """
        description = f"[Image from {tool_name}]"
        
        if self.provider == "anthropic":
            content = multimodal.to_anthropic_content(images, description)
        else:
            # OpenAI 和兼容 API
            content = multimodal.to_openai_content(images, description)
        
        self.messages.append({
            "role": "user",
            "content": content
        })
    
    async def think(self) -> ThinkingResult:
        """
        Call LLM to think and decide on actions.
        
        Returns:
            ThinkingResult with list of actions to take
        """
        if self.provider == "openai":
            return await self._think_openai()
        elif self.provider == "anthropic":
            return await self._think_anthropic()
        else:
            # Default to OpenAI-compatible
            return await self._think_openai()
    
    async def _think_openai(self) -> ThinkingResult:
        """Call OpenAI-compatible API."""
        api_base = self.api_base or "https://api.openai.com/v1"
        
        # Build request
        # Kimi k2.5 requires temperature=1
        temperature = 1.0 if "kimi-k2" in self.model.lower() else 0.7
        
        request_body = {
            "model": self.model,
            "messages": self.messages,
            "temperature": temperature,
        }
        
        # Add tools if available
        if self.tools:
            request_body["tools"] = self._convert_tools_to_openai_format()
            request_body["tool_choice"] = "auto"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            async with self.session.post(
                f"{api_base}/chat/completions",
                json=request_body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[LLMCaller] OpenAI API error: {response.status} - {error_text}")
                    return ThinkingResult(
                        actions=[AgentAction(type=ActionType.DONE)],
                        reasoning=f"API error: {error_text}",
                        is_final=True,
                    )
                
                data = await response.json()
                return self._parse_openai_response(data)
                
        except Exception as e:
            print(f"[LLMCaller] OpenAI API call error: {e}")
            return ThinkingResult(
                actions=[AgentAction(type=ActionType.DONE)],
                reasoning=f"API call error: {e}",
                is_final=True,
            )
    
    async def _think_anthropic(self) -> ThinkingResult:
        """Call Anthropic API."""
        api_base = self.api_base or "https://api.anthropic.com"
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_content = ""
        
        for msg in self.messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            elif msg["role"] == "user":
                # Handle multimodal content (already in Anthropic format from _add_image_message)
                content = msg["content"]
                if isinstance(content, list):
                    # Already multimodal format - pass through
                    anthropic_messages.append({"role": "user", "content": content})
                else:
                    # String content
                    anthropic_messages.append({"role": "user", "content": content})
            elif msg["role"] == "assistant":
                anthropic_messages.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "tool":
                # Anthropic uses tool_result in user message
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", "unknown"),
                        "content": msg["content"],
                    }]
                })
        
        request_body = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": anthropic_messages,
        }
        
        if system_content:
            request_body["system"] = system_content
        
        if self.tools:
            request_body["tools"] = self._convert_tools_to_anthropic_format()
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        try:
            async with self.session.post(
                f"{api_base}/v1/messages",
                json=request_body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[LLMCaller] Anthropic API error: {response.status} - {error_text}")
                    return ThinkingResult(
                        actions=[AgentAction(type=ActionType.DONE)],
                        reasoning=f"API error: {error_text}",
                        is_final=True,
                    )
                
                data = await response.json()
                return self._parse_anthropic_response(data)
                
        except Exception as e:
            print(f"[LLMCaller] Anthropic API call error: {e}")
            return ThinkingResult(
                actions=[AgentAction(type=ActionType.DONE)],
                reasoning=f"API call error: {e}",
                is_final=True,
            )
    
    def _convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function calling format."""
        openai_tools = []
        for tool in self.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
                }
            })
        return openai_tools
    
    def _convert_tools_to_anthropic_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to Anthropic tool format."""
        anthropic_tools = []
        for tool in self.tools:
            anthropic_tools.append({
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", {"type": "object", "properties": {}}),
            })
        return anthropic_tools
    
    def _get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a tool."""
        for tool in self.tools:
            if tool.get("name") == tool_name:
                return tool.get("inputSchema", {})
        return None
    
    def _parse_tool_arguments(self, func: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        安全解析工具调用的 arguments
        
        处理各种边界情况：
        - arguments 是 None
        - arguments 是空字符串
        - arguments 不是有效的 JSON
        - arguments 解析后不是 dict
        - arguments 有多余的包装层（如 {"args": {...}}）
        """
        raw_args = func.get("arguments")
        
        # 处理 None、空字符串的情况
        if raw_args is None:
            print(f"[LLMCaller] Warning: '{tool_name}' arguments is None")
            return {}
        
        if not isinstance(raw_args, str):
            if isinstance(raw_args, dict):
                return self._unwrap_args(raw_args, tool_name)
            print(f"[LLMCaller] Warning: '{tool_name}' arguments is not a string: {type(raw_args)}")
            return {}
        
        if not raw_args.strip():
            return {}
        
        try:
            parsed = json.loads(raw_args)
            if not isinstance(parsed, dict):
                print(f"[LLMCaller] Warning: '{tool_name}' parsed arguments is not a dict: {type(parsed)}")
                return {}
            return self._unwrap_args(parsed, tool_name)
        except json.JSONDecodeError as e:
            print(f"[LLMCaller] Error parsing '{tool_name}' arguments: {e}, raw: {repr(raw_args)}")
            return {}
    
    def _unwrap_args(self, args: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        解包多余的 args 包装层
        
        有些 LLM 会错误地把参数包装成 {"args": {...}}
        这里检测并解包这种情况
        """
        schema = self._get_tool_schema(tool_name)
        if not schema:
            return args
        
        properties = schema.get("properties", {})
        
        # 检查是否有多余的 "args" 包装
        if "args" in args and "args" not in properties:
            inner_args = args.get("args")
            if isinstance(inner_args, dict):
                print(f"[LLMCaller] Unwrapping nested 'args' for {tool_name}")
                return inner_args
        
        # 检查是否有多余的 "tool_args" 包装
        if "tool_args" in args and "tool_args" not in properties:
            inner_args = args.get("tool_args")
            if isinstance(inner_args, dict):
                print(f"[LLMCaller] Unwrapping nested 'tool_args' for {tool_name}")
                return inner_args
        
        return args
    
    def _validate_tool_input(self, tool_name: str, tool_input: Dict[str, Any]) -> tuple:
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
        
        # 检查是否有未知参数
        unknown_params = [k for k in tool_input.keys() if k not in properties]
        if unknown_params:
            valid_params = list(properties.keys())
            return False, f"Unknown parameters: {unknown_params}. Valid parameters: {valid_params}"
        
        # 检查必需参数
        missing = []
        for param in required:
            if param not in tool_input or tool_input[param] is None:
                param_desc = properties.get(param, {}).get("description", "")
                missing.append(f"'{param}'" + (f" ({param_desc})" if param_desc else ""))
        
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        
        return True, ""
    
    def _parse_openai_response(self, data: Dict[str, Any]) -> ThinkingResult:
        """Parse OpenAI API response into ThinkingResult."""
        actions = []
        reasoning = ""
        is_final = False
        final_answer = None
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "")
        
        # Get text content
        content = message.get("content", "")
        
        # Get reasoning_content for models that support thinking (e.g., kimi-k2.5)
        # reasoning_content takes priority for display
        reasoning_content = message.get("reasoning_content", "")
        reasoning = reasoning_content or content
        
        # Check for tool calls
        tool_calls = message.get("tool_calls", [])
        
        if tool_calls:
            # Has tool calls
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                tool_call_id = tc.get("id", "")  # v12: 保存 LLM 返回的 tool_call.id
                
                # Parse and validate arguments
                args = self._parse_tool_arguments(func, tool_name)
                
                # Validate against schema
                is_valid, validation_error = self._validate_tool_input(tool_name, args)
                if not is_valid:
                    print(f"[LLMCaller] Parameter validation failed for {tool_name}: {validation_error}")
                    # Still create the action, but log the warning
                    # The MCP server will return a clear error
                
                # v2.8: 所有工具调用统一处理，包括 chat_reply
                actions.append(AgentAction(
                    type=ActionType.TOOL_CALL,
                    tool_name=tool_name,
                    args=args,
                    tool_call_id=tool_call_id,  # v12: 传递 tool_call_id
                ))
            
            # Add assistant message with tool calls to history
            # Include reasoning_content for models with thinking enabled (e.g., kimi-k2.5)
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            }
            if reasoning_content:
                assistant_msg["reasoning_content"] = reasoning_content
            self.messages.append(assistant_msg)
        else:
            # No tool calls - this is a final answer
            is_final = True
            final_answer = content
            
            # Add assistant message to history
            if content:
                self.messages.append({"role": "assistant", "content": content})
            
            # LLM 返回纯文本时，记录为 final_answer
            # think_handler 会根据 runtime 类型决定是否转换为 chat_reply
            if content:
                final_answer = content
            
            actions.append(AgentAction(type=ActionType.DONE))
        
        return ThinkingResult(
            actions=actions,
            reasoning=reasoning,
            is_final=is_final,
            final_answer=final_answer,
            mcp_session_id=self.mcp_session_id,
        )
    
    def _parse_anthropic_response(self, data: Dict[str, Any]) -> ThinkingResult:
        """Parse Anthropic API response into ThinkingResult."""
        actions = []
        reasoning = ""
        is_final = False
        final_answer = None
        
        content_blocks = data.get("content", [])
        stop_reason = data.get("stop_reason", "")
        
        text_content = ""
        tool_uses = []
        
        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_uses.append(block)
        
        reasoning = text_content
        
        if tool_uses:
            # Has tool calls
            for tu in tool_uses:
                tool_name = tu.get("name", "")
                tool_call_id = tu.get("id", "")
                raw_args = tu.get("input", {})
                
                # Unwrap nested args if present
                args = self._unwrap_args(raw_args, tool_name) if isinstance(raw_args, dict) else {}
                
                # Validate against schema
                is_valid, validation_error = self._validate_tool_input(tool_name, args)
                if not is_valid:
                    print(f"[LLMCaller] Parameter validation failed for {tool_name}: {validation_error}")
                
                # v2.8: 所有工具调用统一处理，包括 chat_reply
                actions.append(AgentAction(
                    type=ActionType.TOOL_CALL,
                    tool_name=tool_name,
                    args=args,
                    tool_call_id=tool_call_id,
                ))
            
            # Add to history
            self.messages.append({"role": "assistant", "content": content_blocks})
        else:
            # No tool calls
            is_final = True
            final_answer = text_content
            
            # LLM 返回纯文本时，记录为 final_answer
            # think_handler 会根据 runtime 类型决定是否转换为 chat_reply
            if text_content:
                self.messages.append({"role": "assistant", "content": text_content})
                final_answer = text_content
            
            actions.append(AgentAction(type=ActionType.DONE))
        
        return ThinkingResult(
            actions=actions,
            reasoning=reasoning,
            is_final=is_final,
            final_answer=final_answer,
            mcp_session_id=self.mcp_session_id,
        )


# Default system prompt for ReACT Agent
# v14: 恢复详细的 system prompt，引导 LLM 正确使用 runtime_rest() 进入休息状态
DEFAULT_SYSTEM_PROMPT = """You are NovAIC Agent, an AI assistant with access to a virtual computer through MCP (Model Context Protocol).

## 你是谁？

你是一个 7x24 待命的 AI 助手。你的工作模式是：
- 用户给你任务 → 你执行 → 完成后休息等待下一个任务
- 你不会"下班"，只会"休息等待"
- 完成一个任务不代表工作结束，只是这个任务结束了，你要休息等用户的下一个任务

## 核心原则 (必须遵守!)

1. **用户沟通**: 必须通过 `chat_reply()` 与用户交流 - 你的思考用户看不到!
2. **完成后休息**: 当前任务完成后，必须调用 `runtime_rest()` 休息等待下一个任务
3. **观察优先**: 行动前先观察当前状态 (screenshot, browser_screenshot)
4. **验证结果**: 每次操作后验证是否成功

## 用户沟通 (CRITICAL)

**用户看不到你的思考! 必须调用工具与用户交流：**

| 工具 | 用途 |
|------|------|
| `chat_reply(message)` | 回复用户 - 报告进度、展示结果 |
| `chat_ask(question, options)` | 询问用户 - 需要选择/确认 |
| `chat_notify(message, level)` | 发送通知 - 后台更新、警告 |

## 工作流程 (CRITICAL - 完成任务后必须休息!)

**你的标准工作流程：**
1. 接收用户任务
2. 执行任务（可能需要多个步骤）
3. 用 `chat_reply()` 告诉用户结果
4. 调用 `runtime_rest()` 休息，等待用户的下一个任务

**记住：完成一个任务 ≠ 工作结束，而是 = 休息等待下一个任务！**

**何时调用 runtime_rest()：**
- ✅ 当前任务完成了 → 休息等下一个任务
- ✅ 需要等用户回复/确认 → 休息等用户回复
- ✅ 需要等外部操作完成 → 休息等操作完成
- ✅ 遇到问题搞不定 → 休息等用户指示

**示例 - 正确的工作结束方式：**
```python
# ❌ 错误：只回复不休息
chat_reply(message="✅ 任务完成！")
# 然后就没了？用户下次找你怎么叫醒你？

# ✅ 正确：回复 + 休息等待
chat_reply(message="✅ 任务完成！如有需要请随时告诉我。")
runtime_rest(
    reason="当前任务完成，休息等待用户下一个任务",
    wake_triggers=[{"type": "user_response"}]
)
```

**示例 - 等待用户确认：**
```python
chat_ask(question="是否继续？", options=["是", "否"])
runtime_rest(
    reason="等待用户确认",
    wake_triggers=[{"type": "user_response"}]
)
```

## 技术实现：如何"停止"

**重要：当你决定"停止"或"等待用户"时，你有两种选择：**

1. **调用 runtime_rest()** - 主动进入休息状态（推荐）
   ```python
   runtime_rest(reason="任务完成，等待用户下一步指示")
   ```

2. **不返回任何工具调用** - 直接返回纯文本响应，系统会自动结束当前轮次

**绝对禁止：**
- ❌ 说"让我停止"然后又调用 chat_reply
- ❌ 重复发送相似的消息
- ❌ 在 reasoning 中说"我不再调用工具"但 actions 里还有 tool_call

**正确示例：**
- 用户说"你好" → chat_reply("你好！有什么可以帮你的？") → runtime_rest(reason="等待用户指示")
- 用户说"停" → runtime_rest(reason="用户要求停止") （不需要再 chat_reply）
"""
