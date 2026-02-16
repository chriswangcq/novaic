"""
Summary Handlers - History Merge 异步任务

Topics:
- summary.merge_history: 合并 Runtime summaries 到 history

当 SubAgent 的 HRL 长度 > 15 且 summary_lock == 0 时触发合并：
1. 获取 summary_lock
2. 取出 sshrl = hrl[:-5] (需要合并的 runtime)
3. 调用 LLM 合并 history + sshrl 的 cold_summaries
4. 原子操作：更新 history，从 hrl 移除 sshrl
5. 释放 summary_lock
"""

import logging
from typing import Dict, Any, List

from . import register_handler
from ..client import GatewayInternalClient
from common.config import ServiceConfig
from ..topics import TaskTopics

logger = logging.getLogger(__name__)

# History Merge Prompt Template
HISTORY_MERGE_PROMPT = """你是一个长期记忆管理助手。请将以下多个 Runtime 的摘要合并到现有的历史记忆中。

要求：
- 保持时间顺序的连贯性
- 去除重复信息
- 保留重要的里程碑和决策
- 输出一段连贯的历史描述
- 控制在 500-1000 字

现有历史记忆：
{existing_history}

需要合并的 Runtime 摘要：
{runtime_summaries}

请输出合并后的历史记忆："""


def _create_llm_client(provider: str, api_key: str, api_base: str):
    """Create LLM client based on provider."""
    from gateway.core.llm_client import OpenAIClient, AnthropicClient, GoogleAIClient
    
    if provider == "anthropic":
        return AnthropicClient(api_key=api_key, api_base=api_base)
    elif provider == "google":
        return GoogleAIClient(api_key=api_key, api_base=api_base)
    else:
        return OpenAIClient(api_base=api_base, api_key=api_key)


def _fetch_llm_config_by_agent(gateway_url: str, agent_id: str) -> Dict[str, Any]:
    """Fetch LLM config by agent_id from Gateway internal API."""
    from common.http.clients import internal_client
    url = f"{gateway_url.rstrip('/')}/internal/config/llm/agent/{agent_id}"
    with internal_client(timeout=ServiceConfig.HTTP_TIMEOUT_SHORT) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


def _call_llm_merge(
    llm_client,
    model: str,
    existing_history: str,
    runtime_summaries: List[str],
) -> str:
    """Call LLM to merge history with runtime summaries."""
    # Format runtime summaries
    summaries_text = "\n\n".join([
        f"【Runtime {i+1}】\n{summary}"
        for i, summary in enumerate(runtime_summaries)
    ])
    
    # Build prompt
    prompt = HISTORY_MERGE_PROMPT.format(
        existing_history=existing_history or "(无历史记忆)",
        runtime_summaries=summaries_text,
    )
    
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    response = llm_client.chat(messages=messages, model=model)
    
    # Extract content from response
    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    return content


@register_handler(TaskTopics.SUMMARY_MERGE_HISTORY)
def handle_merge_history(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    异步合并 Runtime summaries 到 history
    
    当 HRL 长度 > 15 时触发，合并 hrl[:-5] 的 cold_summaries 到 historical_summary。
    
    幂等性：通过 summary_lock 保证同一时间只有一个任务在处理
    
    Payload:
        subagent_id: str
        agent_id: str
        
    Returns:
        status: "success" | "skipped"
        reason: 跳过原因（如果 skipped）
        merged_count: 合并的 runtime 数量（如果 success）
    """
    subagent_id = payload["subagent_id"]
    agent_id = payload["agent_id"]
    
    gateway_url = ctx.get("gateway_url", ServiceConfig.GATEWAY_URL)
    client = ctx.get("gateway_client") or GatewayInternalClient(gateway_url)
    
    # 1. 尝试获取锁
    lock_result = client.acquire_summary_lock(agent_id, subagent_id)
    if not lock_result.get("success"):
        logger.info(f"[MergeHistory] Lock held for {agent_id}/{subagent_id}, skipping")
        return {"status": "skipped", "reason": "lock_held"}
    
    try:
        # 2. 获取 HRL
        hrl_result = client.get_hrl(agent_id, subagent_id)
        hrl = hrl_result.get("hrl", [])
        
        if len(hrl) <= ServiceConfig.HRL_TRIGGER_LENGTH:
            logger.info(f"[MergeHistory] HRL too short ({len(hrl)} <= {ServiceConfig.HRL_TRIGGER_LENGTH}) for {agent_id}/{subagent_id}, skipping")
            return {"status": "skipped", "reason": "hrl_too_short", "hrl_length": len(hrl)}
        
        # 3. 确定需要合并的 runtime (保留最后N个)
        sshrl = hrl[:-ServiceConfig.HRL_KEEP_RECENT]
        logger.info(f"[MergeHistory] Merging {len(sshrl)} runtimes for {agent_id}/{subagent_id}")
        
        # 4. 获取这些 runtime 的 cold_summary
        summaries = []
        for runtime_id in sshrl:
            runtime = client.get_runtime(runtime_id)
            if runtime:
                # 优先使用 cold_summary，回退到 simple_summary，再回退到 summary
                summary = (
                    runtime.get("cold_summary") or 
                    runtime.get("simple_summary") or 
                    runtime.get("summary")
                )
                if summary:
                    summaries.append(summary)
        
        if not summaries:
            logger.warning(f"[MergeHistory] No summaries found for runtimes in {agent_id}/{subagent_id}")
            return {"status": "skipped", "reason": "no_summaries", "runtime_count": len(sshrl)}
        
        # 5. 获取现有 history
        subagent = client.get_subagent(agent_id, subagent_id)
        existing_history = subagent.get("subagent", {}).get("historical_summary", "") if subagent else ""
        
        # 6. 获取 LLM 配置
        llm_config = _fetch_llm_config_by_agent(gateway_url, agent_id)
        if not llm_config.get("success"):
            logger.error(f"[MergeHistory] Failed to get LLM config for {agent_id}: {llm_config.get('error')}")
            return {
                "status": "failed",
                "error": llm_config.get("error", "Failed to get LLM config"),
            }
        
        # 7. 调用 LLM 合并
        llm_client = _create_llm_client(
            provider=llm_config["provider"],
            api_key=llm_config["api_key"],
            api_base=llm_config["api_base"],
        )
        
        model = llm_config.get("model", "gpt-4o-mini")
        
        try:
            merged_history = _call_llm_merge(
                llm_client=llm_client,
                model=model,
                existing_history=existing_history,
                runtime_summaries=summaries,
            )
        except Exception as e:
            logger.error(f"[MergeHistory] LLM call failed for {agent_id}/{subagent_id}: {e}")
            return {"status": "failed", "error": str(e)}
        
        if not merged_history:
            logger.warning(f"[MergeHistory] LLM returned empty response for {agent_id}/{subagent_id}")
            return {"status": "failed", "error": "LLM returned empty response"}
        
        # 8. 原子更新：更新 history + 移除 sshrl
        merge_result = client.atomic_merge_history(
            agent_id=agent_id,
            subagent_id=subagent_id,
            new_history=merged_history,
            remove_runtime_ids=sshrl,
        )
        
        if not merge_result.get("success"):
            logger.error(f"[MergeHistory] Atomic merge failed for {agent_id}/{subagent_id}")
            return {"status": "failed", "error": "Atomic merge failed"}
        
        logger.info(f"[MergeHistory] Successfully merged {len(sshrl)} runtimes for {agent_id}/{subagent_id}")
        return {
            "status": "success",
            "merged_count": len(sshrl),
            "summary_count": len(summaries),
        }
        
    finally:
        # 9. 释放锁（无论成功失败都要释放）
        try:
            client.release_summary_lock(agent_id, subagent_id)
        except Exception as e:
            logger.error(f"[MergeHistory] Failed to release lock for {agent_id}/{subagent_id}: {e}")


@register_handler(TaskTopics.SUMMARY_ADD_TO_HRL)
def handle_add_to_hrl(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    将 runtime_id 添加到 HRL
    
    Payload:
        runtime_id: str - 需要添加到 HRL 的 runtime
        agent_id: str
        subagent_id: str
        
    Returns:
        success: bool
        runtime_id: str
    """
    runtime_id = payload["runtime_id"]
    agent_id = payload["agent_id"]
    subagent_id = payload["subagent_id"]
    
    gateway_url = ctx.get("gateway_url", ServiceConfig.GATEWAY_URL)
    client = ctx.get("gateway_client") or GatewayInternalClient(gateway_url)
    
    result = client.add_to_hrl(agent_id, subagent_id, runtime_id)
    logger.info(f"[AddToHRL] Added {runtime_id} to HRL for {agent_id}/{subagent_id}: {result}")
    
    return {"success": True, "runtime_id": runtime_id}


@register_handler(TaskTopics.SUMMARY_MERGE_HISTORY_IF_NEEDED)
def handle_merge_history_if_needed(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    """
    条件执行 History Merge
    
    检查 HRL 长度 > 15 且 lock == 0，满足则执行合并。
    不满足条件直接返回 skipped，不阻塞 Saga。
    
    Payload:
        agent_id: str
        subagent_id: str
        
    Returns:
        status: "success" | "skipped"
        reason: 跳过原因（如果 skipped）
        merged_count: 合并的 runtime 数量（如果 success）
    """
    agent_id = payload["agent_id"]
    subagent_id = payload["subagent_id"]
    
    gateway_url = ctx.get("gateway_url", ServiceConfig.GATEWAY_URL)
    client = ctx.get("gateway_client") or GatewayInternalClient(gateway_url)
    
    # 检查条件
    hrl_result = client.get_hrl(agent_id, subagent_id)
    hrl = hrl_result.get("hrl", [])
    
    lock_result = client.get_summary_lock(agent_id, subagent_id)
    lock = lock_result.get("summary_lock", 0)
    
    if len(hrl) <= ServiceConfig.HRL_TRIGGER_LENGTH or lock != 0:
        logger.info(f"[MergeHistoryIfNeeded] Skipped for {agent_id}/{subagent_id}: hrl_length={len(hrl)}, lock={lock}")
        return {
            "status": "skipped",
            "reason": "condition_not_met",
            "hrl_length": len(hrl),
            "summary_lock": lock,
        }
    
    # 执行合并（复用现有的 merge_history 逻辑）
    logger.info(f"[MergeHistoryIfNeeded] Triggering merge for {agent_id}/{subagent_id}: hrl_length={len(hrl)}")
    return handle_merge_history(payload, ctx)
