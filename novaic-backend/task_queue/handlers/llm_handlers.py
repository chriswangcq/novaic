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
import os
from typing import Dict, Any
from . import register_handler
from ..business import LLMBusiness
from ..utils import sync_broadcast_log, BroadcastType
from common.config import ServiceConfig
from common.exceptions import ValidationError
from ..topics import TaskTopics


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


def _fetch_llm_config_from_gateway(gateway_url: str, runtime_id: str) -> Dict[str, Any]:
    """Fetch LLM config by runtime_id from Gateway internal API."""
    import httpx
    url = f"{gateway_url.rstrip('/')}/internal/config/llm/runtime/{runtime_id}"
    with httpx.Client(timeout=ServiceConfig.HTTP_TIMEOUT_SHORT, trust_env=False) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


@register_handler(TaskTopics.LLM_CALL)
def handle_llm_call(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
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
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    # 验证必填字段
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    if not payload.get("round_id"):
        raise ValidationError("Missing required field: round_id")
    if not payload.get("messages"):
        raise ValidationError("Missing required field: messages")
    
    runtime_id = payload["runtime_id"]
    round_id = payload["round_id"]
    messages = payload["messages"]
    tools = payload.get("tools")
    provider = payload.get("provider", "openai")
    
    # 通过 Gateway 内部 API 获取 Runtime 对应的 LLM 配置
    gateway_url = ctx.get("gateway_url", ServiceConfig.GATEWAY_URL)
    llm_config = _fetch_llm_config_from_gateway(gateway_url, runtime_id)
    
    if not llm_config.get("success"):
        return {
            "success": False,
            "runtime_id": runtime_id,
            "round_id": round_id,
            "error": llm_config.get("error", "Failed to get LLM config"),
        }
    
    model = llm_config["model"]
    # 优先从 payload 获取（与 tool_handlers.py 保持一致）
    agent_id = payload.get("agent_id") or llm_config.get("agent_id")
    subagent_id = payload.get("subagent_id") or llm_config.get("subagent_id", "main")

    # 通过 Tools Server HTTP API 获取工具列表
    if not tools:
        try:
            tools_server_url = os.environ.get("NOVAIC_TOOLS_SERVER_URL", ServiceConfig.TOOLS_SERVER_URL)
            import httpx
            with httpx.Client(timeout=ServiceConfig.HTTP_TIMEOUT_SHORT, trust_env=False) as client:
                resp = client.get(f"{tools_server_url}/internal/runtimes/{runtime_id}/tools")
                if resp.status_code == 200:
                    tools_data = resp.json()
                    raw_tools = tools_data.get("tools", [])
                    tools = []
                    for tool in raw_tools:
                        if isinstance(tool, dict) and tool.get("name"):
                            # API 返回 input_schema，兼容 inputSchema
                            schema = tool.get("input_schema") or tool.get("inputSchema") or {}
                            tools.append({
                                "type": "function",
                                "function": {
                                    "name": tool.get("name"),
                                    "description": tool.get("description", ""),
                                    "parameters": schema,
                                },
                            })
        except Exception as e:
            # 如果获取工具失败，记录警告并继续
            import logging
            logging.getLogger(__name__).warning(f"Failed to get tools from Tools Server: {e}")
            tools = tools or []
    
    llm_client = _create_llm_client(
        provider=llm_config["provider"],
        api_key=llm_config["api_key"],
        api_base=llm_config["api_base"],
    )
    
    # 事件标识
    think_event_key = f"think:{runtime_id}:{round_id}"
    
    # 按需展开：仅对 tool 消息的 result_id 拉取 LLM 需要的完整 content（仅用于 LLM 调用）
    from ..utils.trs_client import expand_messages_for_llm
    from ..utils import sanitize_context, process_multimodal_messages
    messages_for_llm = expand_messages_for_llm(messages, provider=provider)
    sanitized_messages = sanitize_context(messages_for_llm)
    processed_messages = process_multimodal_messages(sanitized_messages, provider)
    
    # 广播 think running 事件（LLM 调用前）
    # 不展开 result_id，前端通过 TRS 客户端按需拉取；保持 result_id 以便前端渲染
    if agent_id:
        sync_broadcast_log(
            ctx,
            agent_id,
            subagent_id=subagent_id,
            kind="think",
            status="running",
            event_key=think_event_key,
            data={"type": "think"},
            input_data={
                "messages": messages,  # 原始 messages（含 result_id），前端用 TRS 展开
                "model": model,
                "tools": tools,
                "provider": llm_config.get("provider", "openai"),
            },
        )
    
    # 使用业务逻辑层调用 LLM（传入已展开的 messages）
    biz = LLMBusiness(ctx["gateway_url"], llm_client, client=ctx.get("gateway_client"))
    
    result = biz.call(
        messages=messages_for_llm,
        model=model,
        tools=tools,
        provider=provider,
    )
    
    if not result.success:
        # 广播错误（think failed）
        if agent_id:
            sync_broadcast_log(
                ctx,
                agent_id,
                subagent_id=subagent_id,
                kind="think",
                status="failed",
                event_key=think_event_key,
                data={"type": "think"},
                result_data={"error": result.error[:ServiceConfig.TEXT_TRUNCATE_ERROR]},
            )
        
        return {
            "success": False,
            "runtime_id": runtime_id,
            "round_id": round_id,
            "error": result.error,
        }
    
    # 广播 think complete 事件（LLM 返回后）
    if agent_id and result.response:
        reasoning = biz.extract_reasoning(result.response)
        result_content = {}
        if reasoning:
            truncate_len = ServiceConfig.TEXT_TRUNCATE_REASONING
            result_content["content"] = reasoning[:truncate_len] + "..." if len(reasoning) > truncate_len else reasoning
        
        sync_broadcast_log(
            ctx,
            agent_id,
            subagent_id=subagent_id,
            kind="think",
            status="complete",
            event_key=think_event_key,
            data={"type": "think"},
            result_data=result_content if result_content else None,
        )
    
    return {
        "success": True,
        "runtime_id": runtime_id,
        "round_id": round_id,
        "response": result.response,
        "model": model,
    }


@register_handler(TaskTopics.LLM_CALL_SUMMARY)
def handle_llm_call_summary(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    调用 LLM 生成摘要
    
    自动从 DB 读取 runtime 的对话历史（context），不需要在 payload 中传入。
    
    Payload:
        runtime_id: str
        agent_id: str (可选，用于获取 LLM 配置)
        model: str (可选，默认使用 agent 配置)
        system_prompt: str (可选，摘要提示词)
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    runtime_id = payload["runtime_id"]
    
    # 通过 Gateway 内部 API 获取 Runtime 对应的 LLM 配置
    gateway_url = ctx.get("gateway_url", ServiceConfig.GATEWAY_URL)
    llm_config = _fetch_llm_config_from_gateway(gateway_url, runtime_id)
    
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
    
    result = biz.generate_summary(
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


@register_handler(TaskTopics.LLM_CALL_HOT_COLD_SUMMARY)
def handle_llm_call_hot_cold_summary(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    生成 Hot Summary 和 Cold Summary
    
    Hot Summary:
    - 除最后3轮外：LLM 总结成一段话
    - 最后3轮：保留 think + tools + full_result
    
    Cold Summary:
    - 所有轮次：LLM 总结成一段话
    
    Payload:
        runtime_id: str
        model: str (可选，默认使用 agent 配置)
        
    Raises:
        ValidationError: 当必填字段缺失时
    """
    if not payload.get("runtime_id"):
        raise ValidationError("Missing required field: runtime_id")
    
    runtime_id = payload["runtime_id"]
    
    # 通过 Gateway 内部 API 获取 Runtime 对应的 LLM 配置
    gateway_url = ctx.get("gateway_url", ServiceConfig.GATEWAY_URL)
    llm_config = _fetch_llm_config_from_gateway(gateway_url, runtime_id)
    
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
    
    result = biz.generate_hot_cold_summary(
        runtime_id=runtime_id,
        model=model,
    )
    
    response = {
        "success": result.success,
        "runtime_id": runtime_id,
    }
    
    if result.hot_summary:
        response["hot_summary"] = result.hot_summary
    if result.cold_summary:
        response["cold_summary"] = result.cold_summary
    if result.error:
        response["error"] = result.error
    
    return response
