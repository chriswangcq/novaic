"""
LLM Client - Multi-Provider Support (OpenAI, Anthropic, Google, Azure, Bedrock)
"""

import httpx
from typing import AsyncGenerator, Optional, List, Dict, Any
import json
from abc import ABC, abstractmethod


# Default settings (can be overridden via instance attributes)
DEFAULT_LLM_TIMEOUT = 300
DEFAULT_MAX_TOKENS = 4096
DEFAULT_MODEL = "gpt-4o"


class LLMError(Exception):
    """LLM API Error"""
    pass


# ==================== Base Client ====================

class BaseLLMClient(ABC):
    """Base class for LLM clients"""
    
    def __init__(self, timeout: float = DEFAULT_LLM_TIMEOUT):
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=timeout,
            write=10.0,
            pool=10.0
        )
        self.default_max_tokens = DEFAULT_MAX_TOKENS
        self.default_model = DEFAULT_MODEL
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to the LLM."""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from LLM."""
        pass
    
    def _convert_tools_to_openai(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to OpenAI format (nested function)"""
        return tools
        
    def _convert_tools_to_anthropic(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Anthropic format"""
        converted = []
        for tool in tools:
            if tool.get("type") == "function" and "function" in tool:
                func = tool["function"]
                input_schema = func.get("parameters", {})
                
                # 调试日志：打印前 3 个工具的 schema
                if len(converted) < 3:
                    print(f"[Anthropic] Tool '{func.get('name')}' input_schema: {json.dumps(input_schema, indent=2)}")
                
                converted.append({
                    "name": func.get("name"),
                    "description": func.get("description"),
                    "input_schema": input_schema
                })
            else:
                converted.append(tool)
        return converted


# ==================== OpenAI Client ====================

class OpenAIClient(BaseLLMClient):
    """OpenAI API Client (also works with OpenAI-compatible APIs)"""
    
    def __init__(self, api_base: str, api_key: str):
        super().__init__()
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        # For responses API: track response chain
        self.last_response_id: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to OpenAI API."""
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": stream
        }
        
        if tools:
            converted_tools = self._convert_tools_to_openai(tools)
            payload["tools"] = converted_tools
            
            # 调试日志：打印发送的 tool 定义
            for t in converted_tools:
                if t.get("function", {}).get("name") == "browser_navigate":
                    print(f"[OpenAI] Sending browser_navigate tool:")
                    print(json.dumps(t, indent=2))
        
        url = f"{self.api_base}/chat/completions"
        print(f"[OpenAI] Calling {url} with model {payload['model']}")
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, 
                proxy=None,
                trust_env=False
            ) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
        except httpx.TimeoutException as e:
            print(f"[OpenAI] Timeout error: {e}")
            raise LLMError(f"Request timeout: {e}")
        except Exception as e:
            print(f"[OpenAI] Request error: {e}")
            raise LLMError(f"Request failed: {e}")
        
        print(f"[OpenAI] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[OpenAI] Error response: {response.text}")
            raise LLMError(f"API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # 调试日志：打印 tool_calls
        choices = result.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls", [])
            for tc in tool_calls[:2]:  # 只打印前 2 个
                print(f"[OpenAI] Raw tool_call: {json.dumps(tc, ensure_ascii=False)}")
        
        return result
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from OpenAI."""
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": True
        }
        
        if tools:
            payload["tools"] = self._convert_tools_to_openai(tools)
        
        url = f"{self.api_base}/chat/completions"
        print(f"[OpenAI] Streaming from {url} with model {payload['model']}")
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            proxy=None,
            trust_env=False
        ) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._get_headers(),
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise LLMError(f"API error: {response.status_code} - {error_text}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue
    
    async def responses_create(
        self,
        input: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        previous_response_id: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call responses.create API (for Doubao/specific providers)."""
        payload = {
            "model": model or self.default_model,
            "input": input,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = self._convert_tools_to_openai(tools)
        
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        
        url = f"{self.api_base}/responses"
        print(f"[OpenAI] Calling responses API: {url} with model {payload['model']}")
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                proxy=None,
                trust_env=False
            ) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
        except httpx.TimeoutException as e:
            raise LLMError(f"Request timeout: {e}")
        except Exception as e:
            raise LLMError(f"Request failed: {e}")
        
        if response.status_code != 200:
            raise LLMError(f"API error: {response.status_code} - {response.text}")
        
        result = response.json()
        self.last_response_id = result.get("id")
        return result
    
    def reset_response_chain(self) -> None:
        """Reset response chain."""
        self.last_response_id = None


# ==================== Anthropic Client ====================

class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API Client"""
    
    ANTHROPIC_VERSION = "2023-06-01"
    
    def __init__(self, api_key: str, api_base: str = None):
        super().__init__()
        self.api_base = (api_base or "https://api.anthropic.com").rstrip("/")
        self.api_key = api_key
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Content-Type": "application/json"
        }
    
    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple:
        """Convert OpenAI-style messages to Anthropic format.
        Returns (system_prompt, messages)
        
        Important: Anthropic requires that multiple tool_results be combined into
        a single user message, and user/assistant messages must alternate.
        """
        system_prompt = None
        converted = []
        pending_tool_results = []  # Accumulate tool results
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                # Flush any pending tool results first
                if pending_tool_results:
                    converted.append({"role": "user", "content": pending_tool_results})
                    pending_tool_results = []
                # Convert user content (may contain images)
                converted.append({"role": "user", "content": self._convert_content_to_anthropic(content)})
            elif role == "assistant":
                # Flush any pending tool results first
                if pending_tool_results:
                    converted.append({"role": "user", "content": pending_tool_results})
                    pending_tool_results = []
                # Handle tool_calls in assistant message
                if "tool_calls" in msg:
                    tool_use_blocks = []
                    for tc in msg["tool_calls"]:
                        tool_use_blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id"),
                            "name": tc.get("function", {}).get("name"),
                            "input": json.loads(tc.get("function", {}).get("arguments", "{}"))
                        })
                    if content:
                        converted.append({"role": "assistant", "content": [{"type": "text", "text": content}] + tool_use_blocks})
                    else:
                        converted.append({"role": "assistant", "content": tool_use_blocks})
                else:
                    converted.append({"role": "assistant", "content": content})
            elif role == "tool":
                # Accumulate tool results - they will be combined into one user message
                tool_content = self._convert_content_to_anthropic(content)
                pending_tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id"),
                    "content": tool_content
                })
        
        # Flush any remaining tool results
        if pending_tool_results:
            converted.append({"role": "user", "content": pending_tool_results})
        
        # Ensure messages alternate between user and assistant
        # Anthropic requires this strictly
        merged = []
        for msg in converted:
            if merged and merged[-1]["role"] == msg["role"]:
                # Merge consecutive same-role messages
                prev_content = merged[-1]["content"]
                curr_content = msg["content"]
                
                if isinstance(prev_content, str) and isinstance(curr_content, str):
                    merged[-1]["content"] = prev_content + "\n" + curr_content
                elif isinstance(prev_content, list) and isinstance(curr_content, list):
                    merged[-1]["content"] = prev_content + curr_content
                elif isinstance(prev_content, str):
                    merged[-1]["content"] = [{"type": "text", "text": prev_content}] + (curr_content if isinstance(curr_content, list) else [{"type": "text", "text": curr_content}])
                else:
                    merged[-1]["content"] = prev_content + ([{"type": "text", "text": curr_content}] if isinstance(curr_content, str) else curr_content)
            else:
                merged.append(msg)
        
        return system_prompt, merged
    
    def _convert_content_to_anthropic(self, content: Any) -> Any:
        """Convert OpenAI-style content to Anthropic format.
        
        Handles:
        - String content (pass through)
        - Array content with text and image_url blocks
        """
        if isinstance(content, str):
            return content
        
        if not isinstance(content, list):
            return str(content) if content else ""
        
        # Convert array content
        converted = []
        for item in content:
            if isinstance(item, str):
                converted.append({"type": "text", "text": item})
            elif isinstance(item, dict):
                item_type = item.get("type")
                
                if item_type == "text":
                    # Text block - pass through
                    converted.append({"type": "text", "text": item.get("text", "")})
                    
                elif item_type == "image_url":
                    # OpenAI image_url -> Anthropic image
                    image_url = item.get("image_url", {})
                    url = image_url.get("url", "") if isinstance(image_url, dict) else str(image_url)
                    
                    if url.startswith("data:"):
                        # Data URL: data:image/png;base64,XXXXX
                        try:
                            # Parse data URL
                            header, data = url.split(",", 1)
                            # Extract media type: data:image/png;base64 -> image/png
                            media_type = header.split(":")[1].split(";")[0]
                            converted.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": data
                                }
                            })
                        except Exception as e:
                            # Fallback: treat as text description
                            print(f"[Anthropic] Failed to parse image data URL: {e}")
                            converted.append({"type": "text", "text": "[Image data could not be parsed]"})
                    else:
                        # Regular URL - Anthropic doesn't support URLs directly
                        # Add as text reference
                        converted.append({"type": "text", "text": f"[Image URL: {url}]"})
                        
                elif item_type == "image":
                    # Already Anthropic format - pass through
                    converted.append(item)
                    
                else:
                    # Unknown type - convert to text
                    converted.append({"type": "text", "text": str(item)})
            else:
                # Unknown format - convert to text
                converted.append({"type": "text", "text": str(item)})
        
        return converted if converted else ""
    
    def _convert_response_to_openai(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Anthropic response to OpenAI format."""
        content_blocks = response.get("content", [])
        text_content = ""
        tool_calls = []
        
        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_input = block.get("input", {})
                
                # 调试日志：打印 Anthropic 返回的 tool_use 原始数据
                print(f"[Anthropic] Raw tool_use block: name={block.get('name')}, input={tool_input}")
                
                tool_calls.append({
                    "id": block.get("id"),
                    "type": "function",
                    "function": {
                        "name": block.get("name"),
                        "arguments": json.dumps(tool_input)
                    }
                })
        
        message = {
            "role": "assistant",
            "content": text_content if text_content else None
        }
        
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        return {
            "id": response.get("id"),
            "object": "chat.completion",
            "model": response.get("model"),
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if tool_calls else response.get("stop_reason", "stop")
            }],
            "usage": {
                "prompt_tokens": response.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response.get("usage", {}).get("output_tokens", 0),
                "total_tokens": response.get("usage", {}).get("input_tokens", 0) + response.get("usage", {}).get("output_tokens", 0)
            }
        }
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to Anthropic API."""
        system_prompt, converted_messages = self._convert_messages(messages)
        
        payload = {
            "model": model or self.default_model,
            "messages": converted_messages,
            "max_tokens": max_tokens or self.default_max_tokens,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if tools:
            converted_tools = self._convert_tools_to_anthropic(tools)
            payload["tools"] = converted_tools
            
            # 调试日志：打印发送给 Anthropic 的工具定义
            print(f"[Anthropic] Sending {len(converted_tools)} tools to API")
            for t in converted_tools:
                if t.get('name') == 'browser_navigate':
                    print(f"[Anthropic] browser_navigate FULL schema:")
                    print(json.dumps(t, indent=2))
        
        url = f"{self.api_base}/v1/messages"
        print(f"[Anthropic] Calling {url} with model {payload['model']}")
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, 
                proxy=None,
                trust_env=False
            ) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
        except httpx.TimeoutException as e:
            raise LLMError(f"Request timeout: {e}")
        except Exception as e:
            raise LLMError(f"Request failed: {e}")
        
        print(f"[Anthropic] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[Anthropic] Error response: {response.text}")
            raise LLMError(f"API error: {response.status_code} - {response.text}")
        
        raw_response = response.json()
        
        # 调试日志：打印完整的 API 响应
        content = raw_response.get("content", [])
        for block in content:
            if block.get("type") == "tool_use":
                print(f"[Anthropic] Raw tool_use FULL block:")
                print(json.dumps(block, indent=2, ensure_ascii=False))
        
        return self._convert_response_to_openai(raw_response)
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from Anthropic."""
        system_prompt, converted_messages = self._convert_messages(messages)
        
        payload = {
            "model": model or self.default_model,
            "messages": converted_messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": True
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if tools:
            payload["tools"] = self._convert_tools_to_anthropic(tools)
        
        url = f"{self.api_base}/v1/messages"
        print(f"[Anthropic] Streaming from {url} with model {payload['model']}")
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            proxy=None,
            trust_env=False
        ) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._get_headers(),
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise LLMError(f"API error: {response.status_code} - {error_text}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            event = json.loads(data)
                            # Convert Anthropic stream events to OpenAI format
                            yield self._convert_stream_event(event)
                        except json.JSONDecodeError:
                            continue
    
    def _convert_stream_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Anthropic stream event to OpenAI format."""
        event_type = event.get("type")
        
        if event_type == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return {
                    "choices": [{
                        "index": 0,
                        "delta": {"content": delta.get("text", "")},
                        "finish_reason": None
                    }]
                }
            elif delta.get("type") == "input_json_delta":
                return {
                    "choices": [{
                        "index": 0,
                        "delta": {"tool_calls": [{"function": {"arguments": delta.get("partial_json", "")}}]},
                        "finish_reason": None
                    }]
                }
        elif event_type == "message_stop":
            return {
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
        
        return {"choices": [{"index": 0, "delta": {}, "finish_reason": None}]}


# ==================== Azure Client ====================

class AzureOpenAIClient(BaseLLMClient):
    """Azure OpenAI API Client"""
    
    def __init__(self, api_base: str, deployment_name: str, api_key: str, api_version: str = "2024-02-01"):
        super().__init__()
        self.api_base = api_base.rstrip("/")
        self.deployment_name = deployment_name
        self.api_key = api_key
        self.api_version = api_version
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to Azure OpenAI."""
        payload = {
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": stream
        }
        
        if tools:
            payload["tools"] = self._convert_tools_to_openai(tools)
        
        url = f"{self.api_base}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        print(f"[Azure] Calling {url}")
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, 
                proxy=None,
                trust_env=False
            ) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
        except httpx.TimeoutException as e:
            raise LLMError(f"Request timeout: {e}")
        except Exception as e:
            raise LLMError(f"Request failed: {e}")
        
        print(f"[Azure] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[Azure] Error response: {response.text}")
            raise LLMError(f"API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from Azure OpenAI."""
        payload = {
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": True
        }
        
        if tools:
            payload["tools"] = self._convert_tools_to_openai(tools)
        
        url = f"{self.api_base}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        print(f"[Azure] Streaming from {url}")
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            proxy=None,
            trust_env=False
        ) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._get_headers(),
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise LLMError(f"API error: {response.status_code} - {error_text}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue


# ==================== Google Client ====================

class GoogleAIClient(BaseLLMClient):
    """Google AI (Gemini) API Client"""
    
    def __init__(self, api_key: str, api_base: str = None):
        super().__init__()
        self.api_base = (api_base or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self.api_key = api_key
    
    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple:
        """Convert OpenAI messages to Gemini format. Returns (system_instruction, contents)"""
        system_instruction = None
        contents = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                parts = self._convert_content_to_gemini(content)
                contents.append({"role": "user", "parts": parts})
            elif role == "assistant":
                if "tool_calls" in msg:
                    # Assistant with tool calls
                    parts = []
                    if content:
                        parts.append({"text": content})
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        parts.append({
                            "functionCall": {
                                "name": func.get("name"),
                                "args": json.loads(func.get("arguments", "{}"))
                            }
                        })
                    contents.append({"role": "model", "parts": parts})
                else:
                    contents.append({"role": "model", "parts": [{"text": content if content else ""}]})
            elif role == "tool":
                # Tool result in Gemini format
                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.get("name", "unknown"),
                            "response": {"result": content if isinstance(content, str) else json.dumps(content)}
                        }
                    }]
                })
        
        return system_instruction, contents
    
    def _convert_content_to_gemini(self, content: Any) -> List[Dict[str, Any]]:
        """Convert OpenAI-style content to Gemini parts format."""
        if isinstance(content, str):
            return [{"text": content}]
        
        if not isinstance(content, list):
            return [{"text": str(content) if content else ""}]
        
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append({"text": item})
            elif isinstance(item, dict):
                item_type = item.get("type")
                
                if item_type == "text":
                    parts.append({"text": item.get("text", "")})
                elif item_type == "image_url":
                    # Convert OpenAI image_url to Gemini inline_data
                    image_url = item.get("image_url", {})
                    url = image_url.get("url", "") if isinstance(image_url, dict) else str(image_url)
                    
                    if url.startswith("data:"):
                        try:
                            header, data = url.split(",", 1)
                            mime_type = header.split(":")[1].split(";")[0]
                            parts.append({
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": data
                                }
                            })
                        except Exception as e:
                            print(f"[Google] Failed to parse image data URL: {e}")
                            parts.append({"text": "[Image data could not be parsed]"})
                    else:
                        # Gemini supports file_data for URLs
                        parts.append({"text": f"[Image URL: {url}]"})
                else:
                    parts.append({"text": str(item)})
            else:
                parts.append({"text": str(item)})
        
        return parts if parts else [{"text": ""}]
    
    def _convert_tools_to_gemini(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tools format to Gemini function declarations."""
        function_declarations = []
        for tool in tools:
            if tool.get("type") == "function" and "function" in tool:
                func = tool["function"]
                function_declarations.append({
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {})
                })
        return function_declarations
    
    def _convert_response_to_openai(self, response: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Convert Gemini response to OpenAI format."""
        candidates = response.get("candidates", [])
        if not candidates:
            return {"choices": [], "usage": {}}
        
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        text_content = ""
        tool_calls = []
        
        for i, part in enumerate(parts):
            if "text" in part:
                text_content += part.get("text", "")
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "id": f"call_{i}_{fc.get('name', 'unknown')}",
                    "type": "function",
                    "function": {
                        "name": fc.get("name"),
                        "arguments": json.dumps(fc.get("args", {}))
                    }
                })
        
        finish_reason = candidate.get("finishReason", "STOP")
        # Map Gemini finish reasons to OpenAI format
        if tool_calls:
            finish_reason = "tool_calls"
        elif finish_reason == "STOP":
            finish_reason = "stop"
        else:
            finish_reason = finish_reason.lower()
        
        message = {
            "role": "assistant",
            "content": text_content if text_content else None
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        return {
            "id": "gemini-" + str(hash(str(response))),
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": finish_reason
            }],
            "usage": {
                "prompt_tokens": response.get("usageMetadata", {}).get("promptTokenCount", 0),
                "completion_tokens": response.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                "total_tokens": response.get("usageMetadata", {}).get("totalTokenCount", 0)
            }
        }
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to Google AI."""
        model_name = model or self.default_model
        system_instruction, contents = self._convert_messages(messages)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens or self.default_max_tokens
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        if tools:
            function_declarations = self._convert_tools_to_gemini(tools)
            if function_declarations:
                payload["tools"] = [{"functionDeclarations": function_declarations}]
        
        url = f"{self.api_base}/models/{model_name}:generateContent?key={self.api_key}"
        print(f"[Google] Calling with model {model_name}, tools: {len(tools) if tools else 0}")
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, 
                proxy=None,
                trust_env=False
            ) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
        except httpx.TimeoutException as e:
            raise LLMError(f"Request timeout: {e}")
        except Exception as e:
            raise LLMError(f"Request failed: {e}")
        
        print(f"[Google] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[Google] Error response: {response.text}")
            raise LLMError(f"API error: {response.status_code} - {response.text}")
        
        return self._convert_response_to_openai(response.json(), model_name)
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from Google AI."""
        model_name = model or self.default_model
        system_instruction, contents = self._convert_messages(messages)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens or self.default_max_tokens
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        if tools:
            function_declarations = self._convert_tools_to_gemini(tools)
            if function_declarations:
                payload["tools"] = [{"functionDeclarations": function_declarations}]
        
        url = f"{self.api_base}/models/{model_name}:streamGenerateContent?key={self.api_key}&alt=sse"
        print(f"[Google] Streaming with model {model_name}")
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            proxy=None,
            trust_env=False
        ) as client:
            async with client.stream(
                "POST",
                url,
                headers={"Content-Type": "application/json"},
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise LLMError(f"API error: {response.status_code} - {error_text}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            event = json.loads(data)
                            # Convert to OpenAI format
                            candidates = event.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                text = "".join(p.get("text", "") for p in parts if "text" in p)
                                yield {
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"content": text},
                                        "finish_reason": None
                                    }]
                                }
                        except json.JSONDecodeError:
                            continue


# ==================== Factory ====================

def create_llm_client(provider: str, api_key: str, api_base: str = None, **kwargs) -> BaseLLMClient:
    """
    Factory function to create appropriate LLM client based on provider.
    
    Args:
        provider: Provider type ("openai", "anthropic", "google", "azure", or "openai_compatible")
        api_key: API key (required)
        api_base: API base URL (optional, uses provider default if not specified)
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Configured LLM client instance
    """
    if not api_key:
        raise LLMError(f"API key is required for provider: {provider}")
    
    if provider == "openai":
        base = api_base or "https://api.openai.com/v1"
        return OpenAIClient(api_base=base, api_key=api_key)
    
    elif provider == "anthropic":
        base = api_base or "https://api.anthropic.com"
        return AnthropicClient(api_key=api_key, api_base=base)
    
    elif provider == "google":
        base = api_base or "https://generativelanguage.googleapis.com/v1beta"
        return GoogleAIClient(api_key=api_key, api_base=base)
    
    elif provider == "azure":
        deployment_name = kwargs.get("deployment_name")
        api_version = kwargs.get("api_version", "2024-02-01")
        
        if not api_base:
            raise LLMError("Azure OpenAI requires api_base")
        if not deployment_name:
            raise LLMError("Azure OpenAI requires deployment_name")
            
        return AzureOpenAIClient(
            api_base=api_base,
            deployment_name=deployment_name,
            api_key=api_key,
            api_version=api_version
        )
    
    else:
        # Fallback: treat as OpenAI-compatible
        if not api_base:
            raise LLMError(f"OpenAI-compatible provider '{provider}' requires api_base")
        return OpenAIClient(api_base=api_base, api_key=api_key)


# ==================== Legacy Compatibility ====================

class LLMClient(OpenAIClient):
    """Legacy LLMClient for backward compatibility."""
    pass
