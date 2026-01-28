"""
NovAIC Gateway - Core Agent Implementation

ReAct (Reasoning + Acting) 循环实现
"""

from typing import AsyncGenerator, Dict, Any, List, Optional
import asyncio
import json

from .llm_client import LLMError, BaseLLMClient, OpenAIClient, AnthropicClient, GoogleAIClient
from .session import SessionManager
from .mcp_client import MCPClient


class NovAICAgent:
    """
    Main Agent class that orchestrates:
    - LLM communication (reasoning)
    - Tool execution (acting) - via MCP Client
    - Environment perception (sensing)
    - Session management
    """
    
    def __init__(self, vsock_cid: int, vsock_port: int = 8080):
        """
        Initialize the Agent.
        
        Args:
            vsock_cid: VSOCK Context ID (用于 VM 通信)
            vsock_port: VSOCK 端口 (默认 8080)
        """
        self.vsock_cid = vsock_cid
        self.vsock_port = vsock_port
        
        # Cache for LLM clients (cache_key -> client)
        self._llm_clients: Dict[str, BaseLLMClient] = {}
        
        # Initialize other components
        self.session = SessionManager()
        self.mcp_client = MCPClient()
        
        # Tools list (dynamically loaded from MCP)
        self.tools: List[Dict[str, Any]] = []
        self._tools_initialized = False
        
        # Control flags
        self._interrupted = False
        
        # Environment state
        self._executor_healthy = None
        
        # Settings (can be overridden)
        self.max_iterations = 20
        self.max_tokens = 4096
        self.llm_timeout = 300
        self.llm_max_retries = 3
        self.api_style = "chat_completions"
        
        # For responses API mode: track response chain
        self._response_id: Optional[str] = None
    
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
        """Initialize Agent: discover tools from MCP Server."""
        if self._tools_initialized:
            return
        
        try:
            # 注册 MCP Server (VSOCK)
            await self.mcp_client.register_server(
                name="executor",
                vsock_cid=self.vsock_cid,
                vsock_port=self.vsock_port,
            )
            tools = await self.mcp_client.list_all_tools()
            self.tools = self.mcp_client.to_llm_tools_format(tools)
            
            if len(self.tools) > 0:
                self._executor_healthy = True
                print(f"[Agent] Initialized with MCP via VSOCK CID={self.vsock_cid}: discovered {len(self.tools)} tools")
            else:
                self._executor_healthy = False
                print(f"[Agent] MCP Server connected but no tools discovered")
                
        except Exception as e:
            print(f"[Agent] Failed to initialize MCP connection: {e}")
            self._executor_healthy = False
            self.tools = []
        
        self._tools_initialized = True
    
    async def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment info."""
        return {
            "vsock_cid": self.vsock_cid,
            "vsock_port": self.vsock_port,
            "executor_healthy": self._executor_healthy,
            "tools_count": len(self.tools),
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
        """Process a user message and return responses."""
        self._interrupted = False
        
        if not self._tools_initialized:
            await self.initialize()
        
        env_info = await self.get_environment_info()
        if not env_info["executor_healthy"] or env_info["tools_count"] == 0:
            yield {
                "type": "warning",
                "data": f"⚠️ Executor service not available via VSOCK CID={self.vsock_cid} (MCP tools: {env_info['tools_count']})"
            }
        
        if self.api_style == "responses":
            async for event in self._chat_responses_style(
                user_message, model=model, provider=provider, api_base=api_base, api_key=api_key
            ):
                yield event
        else:
            async for event in self._chat_completions_style(
                user_message, model=model, provider=provider, api_base=api_base, api_key=api_key
            ):
                yield event
    
    async def _chat_completions_style(
        self, 
        user_message: str, 
        model: str = None,
        provider: str = None,
        api_base: str = None,
        api_key: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """OpenAI chat/completions style - ReAct Loop."""
        self.session.add_user_message(user_message)
        
        messages = [
            {"role": "system", "content": SessionManager.SYSTEM_PROMPT}
        ] + self.session.get_messages_for_llm()
        
        iteration = 0
        
        while not self._interrupted and iteration < self.max_iterations:
            iteration += 1
            
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
                
                print(f"[Agent] LLM response - content: {content[:200] if content else '(empty)'}, tool_calls: {len(tool_calls)}")
                
                if tool_calls:
                    if content:
                        yield {"type": "thinking", "data": content}
                    else:
                        tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                        yield {"type": "thinking", "data": f"Executing: {', '.join(tool_names)}"}
                
                if finish_reason == "tool_calls" and tool_calls:
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
                        tool_args_str = func.get("arguments", "{}")
                        tool_id = tool_call.get("id")
                        
                        try:
                            tool_input = json.loads(tool_args_str)
                        except json.JSONDecodeError:
                            tool_input = {}
                        
                        yield {
                            "type": "tool_start",
                            "data": {"tool": tool_name, "input": tool_input, "id": tool_id}
                        }
                        
                        mcp_result = await self.mcp_client.call_tool(tool_name, tool_input)
                        result = self._convert_mcp_result(mcp_result)
                        tool_content = self._convert_result_to_llm_content(result)
                        
                        yield {
                            "type": "tool_end",
                            "data": {"tool": tool_name, "result": result, "result_summary": result}
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
        api_key: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Doubao responses API style."""
        self.session.add_user_message(user_message)
        
        if not self._response_id:
            input_msgs = [
                {"role": "system", "content": SessionManager.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        else:
            input_msgs = [{"role": "user", "content": user_message}]
        
        iteration = 0
        
        while not self._interrupted and iteration < self.max_iterations:
            iteration += 1
            
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
                        tool_args_str = func.get("arguments", "{}")
                        tool_id = tool_call.get("id")
                        
                        try:
                            tool_input = json.loads(tool_args_str)
                        except json.JSONDecodeError:
                            tool_input = {}
                        
                        yield {
                            "type": "tool_start",
                            "data": {"tool": tool_name, "input": tool_input, "id": tool_id}
                        }
                        
                        mcp_result = await self.mcp_client.call_tool(tool_name, tool_input)
                        result = self._convert_mcp_result(mcp_result)
                        tool_content = self._convert_result_to_llm_content(result)
                        
                        yield {
                            "type": "tool_end",
                            "data": {"tool": tool_name, "result": result, "result_summary": result}
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
