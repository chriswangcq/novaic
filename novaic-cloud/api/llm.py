"""
LLM Proxy API

Proxies requests to LLM API (via 中转站) while:
- Validating user authentication
- Checking subscription quotas
- Tracking usage for billing
- Keeping API keys secure
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Any
import json
import httpx

from .auth import get_current_user
from .subscription import check_quota
from config import settings

router = APIRouter()


# ==================== Schemas ====================

class Message(BaseModel):
    role: str
    content: Any  # Can be string or list of content blocks


class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict


class ChatRequest(BaseModel):
    model: str = settings.default_model
    messages: List[Message]
    tools: Optional[List[Tool]] = None
    max_tokens: int = settings.max_tokens
    stream: bool = False


class UsageInfo(BaseModel):
    input_tokens: int
    output_tokens: int


class ChatResponse(BaseModel):
    id: str
    type: str = "message"
    role: str = "assistant"
    content: List[dict]
    stop_reason: Optional[str]
    usage: UsageInfo


# ==================== Helper Functions ====================

def convert_tools_to_openai_format(tools: List[Tool]) -> List[dict]:
    """Convert Anthropic-style tools to OpenAI function format"""
    if not tools:
        return []
    
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
        })
    return openai_tools


def convert_messages_to_openai_format(messages: List[Message]) -> List[dict]:
    """Convert messages to OpenAI format"""
    openai_messages = []
    
    for msg in messages:
        content = msg.content
        
        # Handle Anthropic-style content blocks
        if isinstance(content, list):
            # Convert content blocks to text
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_result":
                        text_parts.append(f"Tool result: {block.get('content', '')}")
                else:
                    text_parts.append(str(block))
            content = "\n".join(text_parts)
        
        openai_messages.append({
            "role": msg.role,
            "content": content
        })
    
    return openai_messages


def convert_openai_response_to_anthropic(response: dict) -> dict:
    """Convert OpenAI response format to Anthropic format"""
    choice = response.get("choices", [{}])[0]
    message = choice.get("message", {})
    
    content = []
    
    # Handle text content
    if message.get("content"):
        content.append({
            "type": "text",
            "text": message["content"]
        })
    
    # Handle tool calls
    tool_calls = message.get("tool_calls", [])
    for tc in tool_calls:
        if tc.get("type") == "function":
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except:
                args = {}
            content.append({
                "type": "tool_use",
                "id": tc.get("id", ""),
                "name": func.get("name", ""),
                "input": args
            })
    
    # Determine stop reason
    finish_reason = choice.get("finish_reason", "")
    if tool_calls:
        stop_reason = "tool_use"
    elif finish_reason == "stop":
        stop_reason = "end_turn"
    else:
        stop_reason = finish_reason
    
    usage = response.get("usage", {})
    
    return {
        "id": response.get("id", ""),
        "type": "message",
        "role": "assistant",
        "content": content,
        "stop_reason": stop_reason,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0)
        }
    }


# ==================== Endpoints ====================

@router.post("/chat")
async def chat(
    request: ChatRequest,
    authorization: str = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Proxy chat request to LLM API.
    """
    
    # Check user quota
    quota_info = await check_quota(current_user["user_id"])
    
    # Convert to OpenAI format
    openai_messages = convert_messages_to_openai_format(request.messages)
    openai_tools = convert_tools_to_openai_format(request.tools) if request.tools else None
    
    if not settings.llm_api_key:
        raise HTTPException(
            status_code=503,
            detail="Cloud LLM proxy is not configured. Set NBCC_LLM_API_KEY."
        )
    
    # Build request payload
    payload = {
        "model": request.model,
        "messages": openai_messages,
        "max_tokens": request.max_tokens,
        "stream": request.stream
    }
    
    if openai_tools:
        payload["tools"] = openai_tools
    
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if request.stream:
                # Streaming response
                return StreamingResponse(
                    stream_chat_response(client, payload, headers, current_user["user_id"]),
                    media_type="text/event-stream"
                )
            else:
                # Non-streaming response
                response = await client.post(
                    f"{settings.llm_api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    print(f"[LLM Error] {response.status_code}: {error_text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"LLM API error: {error_text}"
                    )
                
                result = response.json()
                
                # Record usage
                usage = result.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)
                await record_usage(current_user["user_id"], tokens_used)
                
                # Convert to Anthropic format
                anthropic_response = convert_openai_response_to_anthropic(result)
                
                return anthropic_response
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="LLM API timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"LLM API connection error: {str(e)}")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


async def stream_chat_response(client: httpx.AsyncClient, payload: dict, headers: dict, user_id: str):
    """Stream chat response using SSE format"""
    try:
        async with client.stream(
            "POST",
            f"{settings.llm_api_base}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                yield f"data: {json.dumps({'type': 'error', 'data': {'error': error_text.decode()}})}\n\n"
                return
            
            collected_content = ""
            collected_tool_calls = []
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        
                        # Handle content
                        if delta.get("content"):
                            collected_content += delta["content"]
                            yield f"data: {json.dumps({'type': 'content_block_delta', 'data': {'text': delta['content']}})}\n\n"
                        
                        # Handle tool calls
                        if delta.get("tool_calls"):
                            for tc in delta["tool_calls"]:
                                yield f"data: {json.dumps({'type': 'tool_use', 'data': tc})}\n\n"
                    except json.JSONDecodeError:
                        continue
            
            # Record usage (estimate for streaming)
            await record_usage(user_id, len(collected_content) // 4)
            
            yield "data: [DONE]\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"


async def record_usage(user_id: str, tokens: int):
    """Record token usage for billing"""
    print(f"[Usage] User {user_id} used {tokens} tokens")
    # TODO: Update database
