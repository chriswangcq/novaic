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
    ):
        self.gateway_url = gateway_url
        self.session = session
        self.agent_id = agent_id
        
        # LLM settings
        self.model: Optional[str] = None
        self.api_key: Optional[str] = None
        self.api_base: Optional[str] = None
        self.provider: Optional[str] = None
        
        # Tools schema
        self.tools: List[Dict[str, Any]] = []
        
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
            # Call Aggregate MCP server's tools/list via JSON-RPC
            # MCP server is mounted at the path directly, no /mcp suffix needed
            full_mcp_url = f"{self.gateway_url}{self.mcp_url}"
            
            async with self.session.post(
                full_mcp_url,
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "")
                    
                    # Handle SSE response (text/event-stream)
                    if "text/event-stream" in content_type:
                        data = await self._parse_sse_response(response)
                    else:
                        # Regular JSON response
                        data = await response.json()
                    
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
        """Add a tool execution result to conversation."""
        result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result_str,
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
                anthropic_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                anthropic_messages.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "tool":
                # Anthropic uses tool_result
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
        if content:
            reasoning = content
        
        # Check for tool calls
        tool_calls = message.get("tool_calls", [])
        
        if tool_calls:
            # Has tool calls
            for tc in tool_calls:
                func = tc.get("function", {})
                tool_name = func.get("name", "")
                tool_call_id = tc.get("id", "")  # v12: 保存 LLM 返回的 tool_call.id
                
                # Parse arguments
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except json.JSONDecodeError:
                    args = {}
                
                # v2.8: 所有工具调用统一处理，包括 chat_reply
                actions.append(AgentAction(
                    type=ActionType.TOOL_CALL,
                    tool_name=tool_name,
                    args=args,
                    tool_call_id=tool_call_id,  # v12: 传递 tool_call_id
                ))
            
            # Add assistant message with tool calls to history
            self.messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            })
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
                args = tu.get("input", {})
                
                # v2.8: 所有工具调用统一处理，包括 chat_reply
                actions.append(AgentAction(
                    type=ActionType.TOOL_CALL,
                    tool_name=tool_name,
                    args=args,
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
        )


# Default system prompt for ReACT Agent
DEFAULT_SYSTEM_PROMPT = """You are an AI assistant that can use tools to help users.

When you need to perform an action, use the available tools.
When you have finished the task or have a final answer, respond directly without using tools.

Think step by step:
1. Understand what the user wants
2. Decide if you need to use any tools
3. If yes, call the appropriate tool(s)
4. Based on tool results, decide next steps or provide final answer

Always be helpful and provide clear explanations."""
