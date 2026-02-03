"""
LLM Handlers - LLM 调用

Topics:
- llm.call: 调用 LLM
- llm.call_summary: 生成摘要

使用：
- task_queue.business.LLMBusiness 业务逻辑层
- task_queue.utils 广播
"""

import json
from typing import Dict, Any
from . import register_handler
from ..business import LLMBusiness
from ..utils import broadcast_log, BroadcastType


def _create_llm_client(provider: str, api_key: str, api_base: str):
    """
    根据 provider 创建 LLM client
    """
    from gateway.core.llm_client import OpenAIClient, AnthropicClient, GoogleAIClient
    
    if provider == "anthropic":
        return AnthropicClient(api_key=api_key, api_base=api_base)
    elif provider == "google":
        return GoogleAIClient(api_key=api_key, api_base=api_base)
    else:
        # openai 或其他兼容 API
        return OpenAIClient(api_base=api_base, api_key=api_key)


async def _fetch_llm_config_from_gateway(gateway_url: str, runtime_id: str) -> Dict[str, Any]:
    """Fetch LLM config by runtime_id from Gateway internal API."""
    import httpx
    url = f"{gateway_url.rstrip('/')}/internal/config/llm/runtime/{runtime_id}"
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


@register_handler("llm.call")
async def handle_llm_call(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    调用 LLM
    
    功能：
    1. Context 清理：确保 tool_results 紧跟 assistant+tool_calls
    2. 多模态处理：支持图片等多模态内容
    3. 广播功能：向前端广播 thinking 状态
    
    幂等性：LLM 调用是无状态的，天然幂等
    
    Payload:
        runtime_id: str
        round_id: str
        messages: list
        model: str (可选，默认使用 default_model)
        tools: list (可选)
        agent_id: str (可选，用于广播)
        provider: str (可选，openai/anthropic)
    """
    runtime_id = payload["runtime_id"]
    round_id = payload["round_id"]
    messages = payload["messages"]
    tools = payload.get("tools")
    provider = payload.get("provider", "openai")
    
    # 通过 Gateway 内部 API 获取 Runtime 对应的 LLM 配置
    gateway_url = ctx.get("gateway_url", "http://127.0.0.1:19999")
    llm_config = await _fetch_llm_config_from_gateway(gateway_url, runtime_id)
    
    if not llm_config.get("success"):
        return {
            "success": False,
            "runtime_id": runtime_id,
            "round_id": round_id,
            "error": llm_config.get("error", "Failed to get LLM config"),
        }
    
    model = llm_config["model"]
    agent_id = llm_config.get("agent_id")

    # Try to load MCP tools if not provided
    if not tools:
        try:
            from ..client import GatewayInternalClient
            gateway_client = GatewayInternalClient(gateway_url)
            runtime = await gateway_client.get_runtime(runtime_id)
            mcp_url = runtime.get("mcp_url") if runtime else None
            mcp_client = ctx.get("mcp_client")
            if mcp_client and mcp_url:
                mcp_tools = await mcp_client.list_tools(mcp_url, use_cache=True)
                raw_tools = mcp_tools.get("tools", mcp_tools) if isinstance(mcp_tools, dict) else mcp_tools
                tools = []
                for tool in raw_tools or []:
                    if isinstance(tool, dict) and tool.get("name"):
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.get("name"),
                                "description": tool.get("description", ""),
                                "parameters": tool.get("inputSchema", {}),
                            },
                        })
        except Exception:
            tools = tools or []
    llm_client = _create_llm_client(
        provider=llm_config["provider"],
        api_key=llm_config["api_key"],
        api_base=llm_config["api_base"],
    )
    
    # 1. 广播 thinking 状态
    if agent_id:
        await broadcast_log(ctx, agent_id, BroadcastType.STATUS, {
            "message": f"🧠 Thinking ({round_id})...",
        })
    
    # 2. 使用业务逻辑层调用 LLM
    biz = LLMBusiness(ctx["gateway_url"], llm_client, client=ctx.get("gateway_client"))
    
    result = await biz.call(
        messages=messages,
        model=model,
        tools=tools,
        provider=provider,
    )
    
    if not result.success:
        # 广播错误
        if agent_id:
            await broadcast_log(ctx, agent_id, BroadcastType.ERROR, {
                "message": result.error[:200],
            })
        
        return {
            "success": False,
            "runtime_id": runtime_id,
            "round_id": round_id,
            "error": result.error,
        }
    
    # 3. 广播 reasoning 和 tool_start
    if agent_id and result.response:
        # 广播 reasoning
        reasoning = biz.extract_reasoning(result.response)
        if reasoning:
            await broadcast_log(ctx, agent_id, BroadcastType.THINKING, {
                "content": reasoning[:500] + "..." if len(reasoning) > 500 else reasoning,
            })
        
        # 广播 tool_start
        tool_calls = biz.extract_tool_calls(result.response)
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "")
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            
            await broadcast_log(ctx, agent_id, BroadcastType.TOOL_START, {
                "tool": tool_name,
                "args": args,
            })
    
    return {
        "success": True,
        "runtime_id": runtime_id,
        "round_id": round_id,
        "response": result.response,
        "model": model,
    }


@register_handler("llm.call_summary")
async def handle_llm_call_summary(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    调用 LLM 生成摘要
    
    自动从 DB 读取 runtime 的对话历史（context），不需要在 payload 中传入。
    
    Payload:
        runtime_id: str
        agent_id: str (可选，用于获取 LLM 配置)
        model: str (可选，默认使用 agent 配置)
        system_prompt: str (可选，摘要提示词)
    """
    runtime_id = payload["runtime_id"]
    
    # 通过 Gateway 内部 API 获取 Runtime 对应的 LLM 配置
    gateway_url = ctx.get("gateway_url", "http://127.0.0.1:19999")
    llm_config = await _fetch_llm_config_from_gateway(gateway_url, runtime_id)
    
    if not llm_config.get("success"):
        return {
            "success": False,
            "runtime_id": runtime_id,
            "error": llm_config.get("error", "Failed to get LLM config"),
        }
    
    llm_client = _create_llm_client(
        provider=llm_config["provider"],
        api_key=llm_config["api_key"],
        api_base=llm_config["api_base"],
    )
    
    # 使用 payload 中的 model 或 runtime 的默认 model
    model = payload.get("model") or llm_config["model"]
    
    biz = LLMBusiness(ctx["gateway_url"], llm_client, client=ctx.get("gateway_client"))
    
    result = await biz.generate_summary(
        runtime_id=runtime_id,
        model=model,
        system_prompt=payload.get("system_prompt"),
    )
    
    response = {
        "success": result.success,
        "runtime_id": runtime_id,
    }
    
    if result.summary:
        response["summary"] = result.summary
    if result.cached:
        response["cached"] = result.cached
    if result.error:
        response["error"] = result.error
    
    return response
