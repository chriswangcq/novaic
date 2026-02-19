"""
Context Builder - 构建新 Runtime 启动时的初始 Context

Context 构建规则：
1. historical_summary: SubAgent 的合并历史摘要
2. hrl[:-N] 的 cold_summary: 较早的 runtime（有 cold 用 cold，无 cold 用 simple）
3. hrl[-N:] 的 hot_summary: 最近的 runtime（有 hot 用 hot，无 hot 用 simple）
"""

from typing import List, Dict, Any, Optional, Union

from common.config import ServiceConfig


def build_initial_context(
    agent_id: str,
    subagent_id: str,
    ro_client=None,
    *,
    client=None,
) -> List[Dict[str, Any]]:
    """
    为新 Runtime 构建初始 Context
    
    Context 构建规则：
    context = (
        subagent.historical_summary            # 合并后的历史摘要
        + hrl[:-5] 的 cold_summary             # 较早的 runtime
        + hrl[-5:] 的 hot_summary              # 最近的 runtime
    )
    
    Args:
        agent_id: Agent ID
        subagent_id: SubAgent ID
        ro_client: RuntimeOrchestratorClient (preferred) - has get_subagent, get_hrl, get_runtimes_by_ids
        client: Legacy/fallback - object with get_subagent, get_hrl, get_runtimes_by_ids (e.g. GatewayInternalClient)
        
    Returns:
        消息列表，作为 LLM 的历史上下文
    """
    c = ro_client if ro_client is not None else client
    if c is None:
        return []
    context_parts = []
    
    # 1. 获取 SubAgent 信息（包含 historical_summary）
    try:
        subagent = c.get_subagent(agent_id, subagent_id)
    except Exception as e:
        print(f"[context_builder] Failed to get subagent {subagent_id}: {e}")
        return []
    
    historical_summary = subagent.get("historical_summary")
    if historical_summary:
        context_parts.append({
            "role": "system",
            "content": f"[历史记忆]\n{historical_summary}"
        })
    
    # 2. 获取 HRL
    try:
        hrl_resp = c.get_hrl(agent_id, subagent_id)
        hrl = hrl_resp.get("hrl", [])
    except Exception as e:
        print(f"[context_builder] Failed to get HRL for {subagent_id}: {e}")
        hrl = []
    
    if not hrl:
        # 没有历史 runtime，直接返回（可能只有 historical_summary）
        return context_parts
    
    # 3. 获取所有 runtime 的 summary 信息
    try:
        runtimes = c.get_runtimes_by_ids(hrl)
    except Exception as e:
        print(f"[context_builder] Failed to get runtimes by ids: {e}")
        return context_parts
    
    # 构建 runtime_id -> runtime 映射
    runtime_map = {rt["runtime_id"]: rt for rt in runtimes}
    
    # 4. 分割 HRL: older (hrl[:-N]) 和 recent (hrl[-N:])
    keep_recent = ServiceConfig.HRL_KEEP_RECENT
    if len(hrl) > keep_recent:
        older_ids = hrl[:-keep_recent]
        recent_ids = hrl[-keep_recent:]
    else:
        older_ids = []
        recent_ids = hrl
    
    # 5. 构建较早 runtime 的 context（使用 cold_summary）
    older_summaries = []
    for rid in older_ids:
        rt = runtime_map.get(rid)
        if not rt:
            continue
        # 优先使用 cold_summary，没有则用 simple_summary
        summary = rt.get("cold_summary") or rt.get("simple_summary")
        if summary:
            older_summaries.append(summary)
    
    if older_summaries:
        context_parts.append({
            "role": "system",
            "content": "[较早的工作记录]\n" + "\n\n---\n\n".join(older_summaries)
        })
    
    # 6. 构建最近 runtime 的 context（使用 hot_summary）
    recent_summaries = []
    for rid in recent_ids:
        rt = runtime_map.get(rid)
        if not rt:
            continue
        # 优先使用 hot_summary，没有则用 simple_summary
        summary = rt.get("hot_summary") or rt.get("simple_summary")
        if summary:
            recent_summaries.append(summary)
    
    if recent_summaries:
        context_parts.append({
            "role": "system",
            "content": "[最近的工作记录]\n" + "\n\n---\n\n".join(recent_summaries)
        })
    
    return context_parts


def build_context_summary(
    agent_id: str,
    subagent_id: str,
    ro_client=None,
    *,
    client=None,
) -> Dict[str, Any]:
    """
    构建 Context 并返回统计信息
    
    用于调试和日志记录。
    
    Args:
        agent_id: Agent ID
        subagent_id: SubAgent ID
        ro_client: RuntimeOrchestratorClient (preferred)
        client: Legacy fallback
        
    Returns:
        {
            "context": List[Dict],  # 构建的 context
            "stats": {
                "has_historical_summary": bool,
                "hrl_length": int,
                "older_count": int,
                "recent_count": int,
                "total_parts": int,
            }
        }
    """
    context = build_initial_context(agent_id, subagent_id, ro_client=ro_client, client=client)
    
    stats = {
        "has_historical_summary": False,
        "hrl_length": 0,
        "older_count": 0,
        "recent_count": 0,
        "total_parts": len(context),
    }
    
    # 解析 context 计算统计
    for part in context:
        content = part.get("content", "")
        if content.startswith("[历史记忆]"):
            stats["has_historical_summary"] = True
        elif content.startswith("[较早的工作记录]"):
            stats["older_count"] = content.count("---") + 1
        elif content.startswith("[最近的工作记录]"):
            stats["recent_count"] = content.count("---") + 1
    
    return {
        "context": context,
        "stats": stats,
    }
