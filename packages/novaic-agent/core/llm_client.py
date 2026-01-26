"""
LLM Client - Supports both OpenAI chat/completions and Doubao responses API
"""

import httpx
from typing import AsyncGenerator, Optional, List, Dict, Any
import json

from config import settings


class LLMClient:
    """
    LLM Client that supports two API styles:
    - chat/completions: OpenAI-compatible API
    - responses: Doubao responses.create API with previous_response_id
    """
    
    def __init__(self, api_base: str, api_key: str):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=settings.llm_timeout,
            write=10.0,
            pool=10.0
        )
        # For responses API: track response chain
        self.last_response_id: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _convert_tools(self, tools: List[Dict[str, Any]], flatten: bool = False) -> List[Dict[str, Any]]:
        """
        Convert tools format based on API requirements.
        
        OpenAI/Doubao format (nested):
            {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}
        
        Flat format (some APIs):
            {"type": "function", "name": "...", "description": "...", "parameters": {...}}
        """
        if not flatten:
            # Keep original nested format (for OpenAI, Doubao, etc.)
            return tools
        
        # Flatten for APIs that don't support nested 'function' field
        converted = []
        for tool in tools:
            if tool.get("type") == "function" and "function" in tool:
                func = tool["function"]
                converted.append({
                    "type": "function",
                    "name": func.get("name"),
                    "description": func.get("description"),
                    "parameters": func.get("parameters", {})
                })
            else:
                converted.append(tool)
        return converted
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to the LLM."""
        payload = {
            "model": model or settings.default_model,
            "messages": messages,
            "max_tokens": max_tokens or settings.max_tokens,
            "stream": stream
        }
        
        if tools:
            payload["tools"] = self._convert_tools(tools, flatten=False)
        
        url = f"{self.api_base}/chat/completions"
        print(f"[LLM] Calling {url} with model {payload['model']}")
        
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
            print(f"[LLM] Timeout error: {e}")
            raise LLMError(f"Request timeout: {e}")
        except Exception as e:
            print(f"[LLM] Request error: {e}")
            raise LLMError(f"Request failed: {e}")
        
        print(f"[LLM] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[LLM] Error response: {response.text}")
            raise LLMError(f"API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response from LLM."""
        payload = {
            "model": model or settings.default_model,
            "messages": messages,
            "max_tokens": max_tokens or settings.max_tokens,
            "stream": True
        }
        
        if tools:
            payload["tools"] = self._convert_tools(tools, flatten=False)
        
        url = f"{self.api_base}/chat/completions"
        print(f"[LLM] Streaming from {url} with model {payload['model']}")
        
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
        """
        Call Doubao responses.create API.
        
        This API supports:
        - previous_response_id: Chain responses for conversation continuity
        - caching: Prefix caching for reduced token costs
        - thinking: Control thinking mode
        """
        payload = {
            "model": model or settings.default_model,
            "input": input,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if tools:
            payload["tools"] = self._convert_tools(tools, flatten=False)
        
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        
        # Note: Doubao caching/thinking features require specific API versions
        # Skip these for now to avoid compatibility issues
        # if "volces.com" in self.api_base:
        #     if settings.enable_prefix_caching:
        #         payload["caching"] = {"type": "enabled"}
        #     if not settings.enable_thinking:
        #         payload["thinking"] = {"type": "disabled"}
        
        url = f"{self.api_base}/responses"
        print(f"[LLM] Calling responses API: {url} with model {payload['model']}")
        if previous_response_id:
            print(f"[LLM] Using previous_response_id: {previous_response_id}")
        
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
            print(f"[LLM] Timeout error: {e}")
            raise LLMError(f"Request timeout: {e}")
        except Exception as e:
            print(f"[LLM] Request error: {e}")
            raise LLMError(f"Request failed: {e}")
        
        print(f"[LLM] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[LLM] Error response: {response.text}")
            raise LLMError(f"API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # Save response_id for chaining
        self.last_response_id = result.get("id")
        print(f"[LLM] Got response_id: {self.last_response_id}")
        
        return result
    
    def reset_response_chain(self) -> None:
        """Reset response chain (call when clearing conversation)."""
        self.last_response_id = None
        print("[LLM] Response chain reset")


class LLMError(Exception):
    """LLM API Error"""
    pass
