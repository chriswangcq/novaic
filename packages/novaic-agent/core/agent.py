"""
NovAIC Agent - Core Agent Implementation

ReAct (Reasoning + Acting) 循环实现
"""

from typing import AsyncGenerator, Dict, Any, List, Optional
import asyncio
import json

from .llm_client import LLMClient, LLMError
from .session import SessionManager
from .mcp_client import MCPClient
from config import settings


class NBCCAgent:
    """
    Main Agent class that orchestrates:
    - LLM communication (reasoning)
    - Tool execution (acting) - via MCP Client
    - Environment perception (sensing)
    - Session management
    """
    
    def __init__(self, api_base: str, api_key: str):
        """
        Initialize the Agent.
        
        Args:
            api_base: LLM API base URL
            api_key: LLM API key
        """
        self.api_base = api_base
        self.api_key = api_key
        
        # Initialize components
        self.llm_client = LLMClient(api_base=api_base, api_key=api_key)
        self.session = SessionManager()
        self.mcp_client = MCPClient()
        
        # Tools list (dynamically loaded from MCP)
        self.tools: List[Dict[str, Any]] = []
        self._tools_initialized = False
        
        # Control flags
        self._interrupted = False
        
        # Environment state
        self._executor_healthy = None
        self._last_health_check = None
        
        # For responses API mode: track response chain
        self._response_id: Optional[str] = None
    
    async def check_executor_health(self, retries: int = 3, delay: float = 1.0) -> Dict[str, Any]:
        """检查 Executor 服务健康状态（带重试）"""
        import httpx
        import asyncio
        
        url = f"{settings.executor_url}/health"
        print(f"[Agent] Checking Executor health at {url} (retries={retries})")
        
        last_error = None
        for attempt in range(retries):
            try:
                print(f"[Agent] Health check attempt {attempt + 1}/{retries}...")
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    print(f"[Agent] Health check response: status={resp.status_code}")
                    if resp.status_code == 200:
                        self._executor_healthy = True
                        print(f"[Agent] Executor is healthy!")
                        return {"healthy": True, "data": resp.json()}
                    else:
                        last_error = f"Status {resp.status_code}"
            except Exception as e:
                import traceback
                last_error = f"{type(e).__name__}: {str(e)}"
                print(f"[Agent] Health check failed: {last_error}")
                traceback.print_exc()
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < retries - 1:
                await asyncio.sleep(delay)
        
        print(f"[Agent] Executor unhealthy after {retries} attempts: {last_error}")
        self._executor_healthy = False
        return {"healthy": False, "error": last_error}
    
    async def initialize(self) -> None:
        """
        初始化 Agent：从 MCP Server 发现工具
        
        必须在第一次调用 chat() 之前调用，或者在 chat() 中自动调用。
        """
        if self._tools_initialized:
            return
        
        # 注册 Executor MCP Server
        await self.mcp_client.register_server("executor", settings.executor_url)
        
        # 发现所有工具
        tools = await self.mcp_client.list_all_tools()
        
        # 转换为 LLM 工具格式
        self.tools = self.mcp_client.to_llm_tools_format(tools)
        
        print(f"[Agent] Initialized with MCP: discovered {len(self.tools)} tools")
        self._tools_initialized = True
    
    async def get_environment_info(self) -> Dict[str, Any]:
        """获取当前环境信息（感知）"""
        info = {
            "executor_url": settings.executor_url,
            "executor_healthy": self._executor_healthy,
            "work_dir": settings.work_dir,
        }
        
        # 检查 Executor 健康
        health = await self.check_executor_health()
        info["executor_healthy"] = health["healthy"]
        
        return info
    
    async def chat(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message and return responses.
        Dispatches to appropriate API style based on configuration.
        """
        self._interrupted = False
        
        # 确保工具已初始化
        if not self._tools_initialized:
            await self.initialize()
        
        # 【感知】检查环境
        env_info = await self.get_environment_info()
        if not env_info["executor_healthy"]:
            yield {
                "type": "warning",
                "data": f"⚠️ Executor service not available at {settings.executor_url}"
            }
        
        # Dispatch based on api_style configuration
        if settings.api_style == "responses":
            print(f"[Agent] Using Doubao responses API style")
            async for event in self._chat_responses_style(user_message):
                yield event
        else:
            print(f"[Agent] Using OpenAI chat/completions API style")
            async for event in self._chat_completions_style(user_message):
                yield event
    
    async def _chat_completions_style(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        OpenAI chat/completions style - sends full message history each time.
        ReAct Loop: Reason -> Act -> Observe -> Repeat
        """
        # Add user message to history
        self.session.add_user_message(user_message)
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": SessionManager.SYSTEM_PROMPT}
        ] + self.session.get_messages_for_llm()
        
        # ReAct Loop
        max_iterations = settings.max_iterations  # 从配置读取
        iteration = 0
        
        while not self._interrupted and iteration < max_iterations:
            iteration += 1
            
            try:
                # 【推理】调用 LLM
                response = await self.llm_client.chat(
                    messages=messages,
                    tools=self.tools
                )
                
                # Parse response
                choice = response.get("choices", [{}])[0]
                message = choice.get("message", {})
                finish_reason = choice.get("finish_reason")
                
                content = message.get("content") or ""
                tool_calls = message.get("tool_calls") or []
                
                # Debug: 记录 LLM 返回内容
                print(f"[Agent] LLM response - content: {content[:200] if content else '(empty)'}, tool_calls: {len(tool_calls)}")
                
                # Yield thinking content only when there are tool calls
                # (final content will be sent separately at the end to avoid duplication)
                if tool_calls:
                    if content:
                        yield {
                            "type": "thinking",
                            "data": content
                        }
                    else:
                        # LLM 没有输出思考内容但要调用工具 - 生成一个简短说明
                        tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                        thinking_text = f"Executing: {', '.join(tool_names)}"
                        yield {
                            "type": "thinking",
                            "data": thinking_text
                        }
                
                # 检查是否需要执行工具
                if finish_reason == "tool_calls" and tool_calls:
                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": content,
                        "tool_calls": tool_calls
                    })
                    
                    # 【行动】执行每个工具
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
                        
                        # Notify: tool start
                        yield {
                            "type": "tool_start",
                            "data": {
                                "tool": tool_name,
                                "input": tool_input,
                                "id": tool_id
                            }
                        }
                        
                        # Execute the tool via MCP Client
                        mcp_result = await self.mcp_client.call_tool(tool_name, tool_input)
                        # 转换 MCP 响应格式到标准格式
                        result = self._convert_mcp_result(mcp_result)
                        
                        # 【观察】处理工具结果
                        # 转换为 LLM 兼容格式（图片使用 vision API 格式）
                        tool_content = self._convert_result_to_llm_content(result)
                        
                        # Notify: tool end
                        yield {
                            "type": "tool_end",
                            "data": {
                                "tool": tool_name,
                                "result": result,
                                "result_summary": result  # 完整结果用于前端显示
                            }
                        }
                        
                        # Add tool result to messages (使用 LLM 兼容格式)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": tool_content
                        })
                    
                else:
                    # 完成：没有更多工具调用
                    self.session.add_assistant_message(content)
                    
                    yield {
                        "type": "final",
                        "data": content
                    }
                    break
                    
            except LLMError as e:
                yield {
                    "type": "error",
                    "data": {"error": str(e)}
                }
                break
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield {
                    "type": "error",
                    "data": {"error": f"Unexpected error: {str(e)}"}
                }
                break
        
        # 检查是否因为迭代次数过多而退出
        if iteration >= max_iterations:
            yield {
                "type": "warning",
                "data": "⚠️ Maximum iterations reached. Task may be incomplete."
            }
    
    async def _chat_responses_style(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Doubao responses API style - uses previous_response_id for conversation chaining.
        ReAct Loop: Reason -> Act -> Observe -> Repeat
        """
        # Add user message to session (for history tracking)
        self.session.add_user_message(user_message)
        
        # Build input for first call or subsequent calls
        if not self._response_id:
            # First call: include system prompt
            input_msgs = [
                {"role": "system", "content": SessionManager.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        else:
            # Subsequent calls: only send new user message
            input_msgs = [{"role": "user", "content": user_message}]
        
        # ReAct Loop
        max_iterations = settings.max_iterations  # 从配置读取
        iteration = 0
        
        while not self._interrupted and iteration < max_iterations:
            iteration += 1
            print(f"[Agent] === Iteration {iteration}/{max_iterations} ===")
            print(f"[Agent] Input messages count: {len(input_msgs)}")
            
            try:
                # 【推理】调用 Doubao responses API
                print(f"[Agent] Calling LLM...")
                response = await self.llm_client.responses_create(
                    input=input_msgs,
                    tools=self.tools,
                    previous_response_id=self._response_id
                )
                
                # Update response chain
                self._response_id = response.get("id")
                
                # Parse Doubao response format
                content, tool_calls, finish_reason = self._parse_responses_output(response)
                
                # Debug: 记录 LLM 返回内容
                print(f"[Agent] Doubao response - content: {content[:200] if content else '(empty)'}, tool_calls: {len(tool_calls)}")
                
                # Yield thinking content only when there are tool calls
                # (final content will be sent separately at the end to avoid duplication)
                if tool_calls:
                    if content:
                        yield {
                            "type": "thinking",
                            "data": content
                        }
                    else:
                        tool_names = [tc.get("function", {}).get("name", "unknown") for tc in tool_calls]
                        thinking_text = f"Executing: {', '.join(tool_names)}"
                        yield {
                            "type": "thinking",
                            "data": thinking_text
                        }
                
                # 检查是否需要执行工具
                if tool_calls:
                    # Collect tool results to send as next input
                    tool_results_input = []
                    
                    # 【行动】执行每个工具
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
                        
                        # Notify: tool start
                        yield {
                            "type": "tool_start",
                            "data": {
                                "tool": tool_name,
                                "input": tool_input,
                                "id": tool_id
                            }
                        }
                        
                        # Execute the tool via MCP Client
                        mcp_result = await self.mcp_client.call_tool(tool_name, tool_input)
                        # 转换 MCP 响应格式到标准格式
                        result = self._convert_mcp_result(mcp_result)
                        
                        # 【观察】处理工具结果
                        # 转换为 LLM 兼容格式（图片使用 vision API 格式）
                        tool_content = self._convert_result_to_llm_content(result)
                        
                        # Notify: tool end
                        yield {
                            "type": "tool_end",
                            "data": {
                                "tool": tool_name,
                                "result": result,
                                "result_summary": result  # 完整结果用于前端显示
                            }
                        }
                        
                        # Build tool result for next input (使用 LLM 兼容格式)
                        tool_results_input.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": tool_content
                        })
                    
                    # Set input for next iteration (tool results)
                    input_msgs = tool_results_input
                    print(f"[Agent] Continuing to next iteration with {len(tool_results_input)} tool results")
                    
                else:
                    # 完成：没有更多工具调用
                    print(f"[Agent] No more tool calls, finishing with content: {content[:100] if content else '(empty)'}...")
                    self.session.add_assistant_message(content)
                    
                    yield {
                        "type": "final",
                        "data": content
                    }
                    print(f"[Agent] Final event yielded, breaking loop")
                    break
                    
            except LLMError as e:
                print(f"[Agent] LLM Error in iteration {iteration}: {e}")
                yield {
                    "type": "error",
                    "data": {"error": str(e)}
                }
                break
            except Exception as e:
                import traceback
                print(f"[Agent] Unexpected error in iteration {iteration}: {e}")
                traceback.print_exc()
                yield {
                    "type": "error",
                    "data": {"error": f"Unexpected error: {str(e)}"}
                }
                break
        
        print(f"[Agent] Loop ended. Iterations: {iteration}, Interrupted: {self._interrupted}")
        
        # 检查是否因为迭代次数过多而退出
        if iteration >= max_iterations:
            yield {
                "type": "warning",
                "data": "⚠️ Maximum iterations reached. Task may be incomplete."
            }
    
    def _convert_mcp_result(self, mcp_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换 MCP 响应格式到标准工具结果格式
        
        MCP Server 直接返回 Executor API 的响应格式，所以这里主要是兼容性处理。
        如果已经是标准格式，直接返回。
        """
        # MCP Server 现在直接返回 Executor API 的响应，所以不需要转换
        # 但为了兼容性，检查一下格式
        if "success" in mcp_result or "observation" in mcp_result:
            # 已经是标准格式
            return mcp_result
        
        # 如果不是标准格式，尝试转换（向后兼容）
        return {
            "success": True,
            "observation": mcp_result
            }
    
    def _convert_result_to_llm_content(self, result: Dict[str, Any]) -> Any:
        """
        将工具结果转换为 LLM 兼容的内容格式
        
        对于包含截图的结果，使用 Vision API 格式：
        - 文本部分：其他结果数据（JSON）
        - 图片部分：使用 image_url 格式
        
        返回格式：
        - 如果有截图：content 数组 [{"type": "text", ...}, {"type": "image_url", ...}]
        - 如果没有截图：JSON 字符串（向后兼容）
        """
        # 检查是否有截图
        screenshot = None
        screenshot_key = None
        
        # 检查顶层
        if "screenshot" in result and isinstance(result["screenshot"], str):
            screenshot = result["screenshot"]
            screenshot_key = "screenshot"
        elif "image" in result and isinstance(result["image"], str):
            screenshot = result["image"]
            screenshot_key = "image"
        # 检查 observation 中
        elif "observation" in result and isinstance(result["observation"], dict):
            obs = result["observation"]
            if "screenshot" in obs and isinstance(obs["screenshot"], str):
                screenshot = obs["screenshot"]
                screenshot_key = "screenshot"
            elif "image" in obs and isinstance(obs["image"], str):
                screenshot = obs["image"]
                screenshot_key = "image"
        # 检查 output 中
        elif "output" in result and isinstance(result["output"], dict):
            output = result["output"]
            if "screenshot" in output and isinstance(output["screenshot"], str):
                screenshot = output["screenshot"]
                screenshot_key = "screenshot"
            elif "image" in output and isinstance(output["image"], str):
                screenshot = output["image"]
                screenshot_key = "image"
        
        if screenshot and len(screenshot) > 100:  # 确保是有效的 base64
            # 构建不包含截图的文本内容
            text_result = {}
            for key, value in result.items():
                if key in ("screenshot", "image"):
                    continue
                elif key == "observation" and isinstance(value, dict):
                    # 递归处理 observation，移除截图
                    text_obs = {}
                    for obs_key, obs_value in value.items():
                        if obs_key not in ("screenshot", "image"):
                            text_obs[obs_key] = obs_value
                    if text_obs:
                        text_result[key] = text_obs
                elif key == "output" and isinstance(value, dict):
                    # 递归处理 output，移除截图
                    text_output = {}
                    for out_key, out_value in value.items():
                        if out_key not in ("screenshot", "image"):
                            text_output[out_key] = out_value
                    if text_output:
                        text_result[key] = text_output
                else:
                    text_result[key] = value
            
            # 构建 LLM Vision API 兼容的内容数组
            content = []
            
            # 添加文本部分（其他结果数据）
            if text_result:
                text_content = json.dumps(text_result, ensure_ascii=False)
                # 截断过长的文本
                if len(text_content) > 5000:
                    text_content = text_content[:5000] + f"... [truncated, total {len(text_content)} chars]"
                content.append({
                    "type": "text",
                    "text": text_content
                })
            
            # 添加图片部分（Vision API 格式）
            # 格式：data:image/png;base64,{base64_string}
            image_url = f"data:image/png;base64,{screenshot}"
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            })
            
            return content
        else:
            # 没有截图，使用传统格式（JSON 字符串）
            # 简化过长的内容
            simplified = {}
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 5000:
                    simplified[key] = value[:5000] + f"... [truncated, total {len(value)} chars]"
                elif isinstance(value, dict):
                    # 递归处理字典
                    simplified[key] = self._simplify_dict_for_llm(value)
                else:
                    simplified[key] = value
            
            return json.dumps(simplified, ensure_ascii=False)
    
    def _simplify_dict_for_llm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """递归简化字典，移除截图，截断过长字符串"""
        simplified = {}
        for key, value in data.items():
            if key in ("screenshot", "image") and isinstance(value, str):
                # 移除截图（已在 content 数组中单独处理）
                continue
            elif isinstance(value, str) and len(value) > 5000:
                simplified[key] = value[:5000] + f"... [truncated, total {len(value)} chars]"
            elif isinstance(value, dict):
                simplified[key] = self._simplify_dict_for_llm(value)
            else:
                simplified[key] = value
        return simplified
    
    def _parse_responses_output(self, response: Dict[str, Any]) -> tuple:
        """
        Parse Doubao responses API output format.
        
        Expected response format:
        {
            "id": "resp_xxx",
            "output": [
                {"type": "message", "content": [{"type": "text", "text": "..."}]}
            ],
            "usage": {...}
        }
        
        Or with tool calls:
        {
            "id": "resp_xxx",
            "output": [
                {
                    "type": "function_call",
                    "function": {"name": "...", "arguments": "..."},
                    "id": "call_xxx"
                }
            ]
        }
        
        Returns:
            tuple: (content: str, tool_calls: list, finish_reason: str)
        """
        content = ""
        tool_calls = []
        finish_reason = "stop"
        
        output = response.get("output", [])
        
        for item in output:
            item_type = item.get("type", "")
            
            if item_type == "message":
                # Text message
                content_list = item.get("content", [])
                for content_item in content_list:
                    if content_item.get("type") == "text":
                        content += content_item.get("text", "")
                        
            elif item_type == "function_call":
                # Tool/function call
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
                # Direct text output (alternative format)
                content += item.get("text", "")
                
        # Check if response indicates more tool calls needed
        if tool_calls:
            finish_reason = "tool_calls"
        
        return content, tool_calls, finish_reason
    
    async def chat_with_logs(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Chat with detailed execution logs."""
        async for event in self.chat(user_message):
            yield event
            
            if event["type"] == "tool_start":
                yield {
                    "type": "status",
                    "data": {
                        "message": f"🔧 Executing {event['data']['tool']}..."
                    }
                }
            elif event["type"] == "tool_end":
                success = event['data'].get('result', {}).get('success', False)
                status = "✅" if success else "❌"
                yield {
                    "type": "status",
                    "data": {
                        "message": f"{status} {event['data']['tool']} completed"
                    }
                }
    
    def interrupt(self) -> None:
        """Interrupt current execution"""
        self._interrupted = True
        # MCP Client 不需要 interrupt（工具调用是独立的）
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get chat history"""
        return self.session.get_all_messages()
    
    def clear_messages(self) -> None:
        """Clear chat history and reset response chain"""
        self.session.clear()
        # Reset response chain for Doubao responses API
        self._response_id = None
        self.llm_client.reset_response_chain()
    
    async def close(self) -> None:
        """Clean up resources"""
        if self.mcp_client:
            await self.mcp_client.close()
