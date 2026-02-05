"""
Simple Summary - Runtime Context 简化摘要生成

生成 Runtime 完成时的纯文本摘要：
- 除最后N轮外：保留 think + tools + [task_result:xxx_id]
- 最后N轮：保留 think + tools + full_result

一轮 = assistant (think/tool_calls) + tool_results
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from common.config import ServiceConfig


@dataclass
class Round:
    """表示一轮对话"""
    index: int  # 轮次索引（0-based）
    think: str = ""  # 思考内容 (assistant content or reasoning_content)
    tools: List[Dict[str, Any]] = field(default_factory=list)  # 工具调用列表
    # 每个 tool: {"id": str, "name": str, "args": str, "result": str, "result_id": str}


def split_into_rounds(context: List[Dict[str, Any]]) -> List[Round]:
    """
    将 context 分割为轮次
    
    一轮 = assistant message (可能有 content/reasoning_content + tool_calls) + 对应的 tool results
    
    Args:
        context: runtime 的完整 context（消息列表）
    
    Returns:
        Round 列表
    """
    if not context:
        return []
    
    rounds = []
    current_round: Optional[Round] = None
    pending_tool_calls: Dict[str, Dict[str, Any]] = {}  # tool_call_id -> tool info
    
    for msg in context:
        if not isinstance(msg, dict):
            continue
        
        role = msg.get("role", "")
        
        if role == "assistant":
            # 新的 assistant 消息，开始新的轮次
            if current_round is not None:
                # 保存之前的轮次
                rounds.append(current_round)
            
            current_round = Round(index=len(rounds))
            
            # 提取 think 内容 (content 或 reasoning_content)
            think_content = msg.get("reasoning_content", "") or msg.get("content", "") or ""
            if isinstance(think_content, str):
                current_round.think = think_content.strip()
            
            # 提取 tool_calls
            tool_calls = msg.get("tool_calls", [])
            for tc in tool_calls:
                tc_id = tc.get("id", "")
                func = tc.get("function", {})
                tool_name = func.get("name", "unknown")
                tool_args = func.get("arguments", "{}")
                
                # 格式化参数（尝试美化 JSON）
                if isinstance(tool_args, str):
                    try:
                        parsed = json.loads(tool_args)
                        tool_args = json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                tool_info = {
                    "id": tc_id,
                    "name": tool_name,
                    "args": tool_args,
                    "result": "",
                    "result_id": tc_id,  # 使用 tool_call_id 作为 result_id
                }
                
                if current_round:
                    current_round.tools.append(tool_info)
                pending_tool_calls[tc_id] = tool_info
        
        elif role in ("tool", "tool_result"):
            # tool result 消息
            tc_id = msg.get("tool_call_id", "")
            content = msg.get("content", "")
            
            # 将 content 转换为字符串
            if not isinstance(content, str):
                try:
                    content = json.dumps(content, ensure_ascii=False)
                except (TypeError, ValueError):
                    content = str(content)
            
            # 更新对应的 tool_call 结果
            if tc_id in pending_tool_calls:
                pending_tool_calls[tc_id]["result"] = content
        
        # user 消息不开始新轮次，只是 context 的一部分
    
    # 保存最后一个轮次
    if current_round is not None:
        rounds.append(current_round)
    
    return rounds


def format_round_compressed(round: Round) -> str:
    """
    格式化压缩的轮次
    
    保留 think + tools + [task_result:xxx_id]
    
    Args:
        round: Round 对象
    
    Returns:
        格式化的字符串
    """
    parts = []
    
    # Think 部分
    if round.think:
        # 截断过长的 think
        think_text = round.think
        if len(think_text) > ServiceConfig.TEXT_TRUNCATE_THINK:
            think_text = think_text[:ServiceConfig.TEXT_TRUNCATE_THINK] + "..."
        parts.append(f"[Think] {think_text}")
    
    # Tools 部分
    for tool in round.tools:
        # 工具调用
        args_display = tool["args"]
        if len(args_display) > ServiceConfig.TEXT_TRUNCATE_ARGS:
            args_display = args_display[:ServiceConfig.TEXT_TRUNCATE_ARGS] + "..."
        parts.append(f"[Tool] {tool['name']}({args_display})")
        
        # 结果引用（使用 id 替代完整结果）
        parts.append(f"[Result] → [task_result:{tool['result_id']}]")
    
    return "\n".join(parts)


def format_round_full(round: Round) -> str:
    """
    格式化完整的轮次
    
    保留 think + tools + full_result
    
    Args:
        round: Round 对象
    
    Returns:
        格式化的字符串
    """
    parts = []
    
    # Think 部分
    if round.think:
        parts.append(f"[Think] {round.think}")
    
    # Tools 部分
    for tool in round.tools:
        # 工具调用
        parts.append(f"[Tool] {tool['name']}({tool['args']})")
        
        # 完整结果
        result = tool["result"]
        if result:
            # 对于非常长的结果，适当截断
            if len(result) > ServiceConfig.TEXT_TRUNCATE_RESULT:
                result = result[:ServiceConfig.TEXT_TRUNCATE_RESULT] + "\n... [truncated]"
            parts.append(f"[Result] {result}")
        else:
            parts.append(f"[Result] (empty)")
    
    return "\n".join(parts)


def generate_simple_summary(
    runtime_context: List[Dict[str, Any]], 
    recent_rounds: int = None
) -> str:
    """
    生成 Simple Summary
    
    Args:
        runtime_context: runtime 的完整 context（消息列表）
        recent_rounds: 保留完整结果的最近轮次数（默认从配置读取）
    
    Returns:
        纯文本的 simple summary
    """
    if recent_rounds is None:
        recent_rounds = ServiceConfig.SUMMARY_LAST_ROUNDS_FULL
    # 处理空 context
    if not runtime_context:
        return "[No context]"
    
    # 1. 识别轮次边界
    rounds = split_into_rounds(runtime_context)
    
    if not rounds:
        return "[No rounds found]"
    
    # 2. 处理每一轮
    result_parts = []
    total_rounds = len(rounds)
    
    for round in rounds:
        # 判断是否是最后 N 轮
        is_recent = (total_rounds - round.index) <= recent_rounds
        
        # 添加轮次标题
        round_header = f"=== Round {round.index + 1}/{total_rounds} ==="
        
        if is_recent:
            # 完整保留
            formatted = format_round_full(round)
        else:
            # 压缩结果
            formatted = format_round_compressed(round)
        
        if formatted:
            result_parts.append(f"{round_header}\n{formatted}")
    
    return "\n\n".join(result_parts)


def format_rounds_for_llm(rounds: List[Round]) -> str:
    """
    将轮次列表格式化为供 LLM 摘要使用的文本
    
    Args:
        rounds: Round 列表
    
    Returns:
        格式化的文本
    """
    if not rounds:
        return "[No rounds]"
    
    result_parts = []
    
    for round in rounds:
        round_parts = []
        round_parts.append(f"=== Round {round.index + 1} ===")
        
        if round.think:
            # 截断过长的 think
            think_text = round.think
            if len(think_text) > ServiceConfig.TEXT_TRUNCATE_LLM_INPUT:
                think_text = think_text[:ServiceConfig.TEXT_TRUNCATE_LLM_INPUT] + "..."
            round_parts.append(f"思考: {think_text}")
        
        for tool in round.tools:
            # 工具调用
            args_display = tool["args"]
            if len(args_display) > ServiceConfig.TEXT_TRUNCATE_REASONING:
                args_display = args_display[:ServiceConfig.TEXT_TRUNCATE_REASONING] + "..."
            round_parts.append(f"工具调用: {tool['name']}({args_display})")
            
            # 结果
            result = tool["result"]
            if result:
                if len(result) > ServiceConfig.TEXT_TRUNCATE_LLM_INPUT:
                    result = result[:ServiceConfig.TEXT_TRUNCATE_LLM_INPUT] + "..."
                round_parts.append(f"结果: {result}")
        
        result_parts.append("\n".join(round_parts))
    
    return "\n\n".join(result_parts)


# ==============================
# Hot/Cold Summary Prompts
# ==============================

HOT_SUMMARY_PROMPT = """你是一个对话历史总结助手。请将以下 Agent 对话的前面部分总结成简洁的一段话。

要求：
- 保留关键的决策、发现和结论
- 保留重要的工具调用结果（如文件路径、错误信息、关键数据）
- 忽略重复的尝试和中间过程
- 用第三人称描述 Agent 的行为
- 控制在 200-500 字

对话内容（需要总结的部分）：
{content}

请输出总结："""


COLD_SUMMARY_PROMPT = """你是一个对话历史总结助手。请将以下 Agent Runtime 的完整对话总结成简洁的一段话。

要求：
- 概述 Agent 完成了什么任务
- 保留最终结果和关键发现
- 忽略中间的尝试和调试过程
- 用第三人称描述
- 控制在 100-300 字

完整对话内容：
{content}

请输出总结："""


def prepare_hot_summary_parts(
    context: List[Dict[str, Any]], 
    recent_rounds: int = None
) -> tuple:
    """
    准备 Hot Summary 的两部分内容
    
    Args:
        context: runtime 的完整 context
        recent_rounds: 保留完整内容的最近轮次数（默认从配置读取）
    
    Returns:
        (earlier_rounds_text, recent_rounds_text)
        - earlier_rounds_text: 需要 LLM 总结的前面轮次文本，如果不需要则为 None
        - recent_rounds_text: 保留完整内容的最近轮次文本
    """
    if recent_rounds is None:
        recent_rounds = ServiceConfig.SUMMARY_LAST_ROUNDS_FULL
    rounds = split_into_rounds(context)
    
    if not rounds:
        return None, "[No rounds found]"
    
    total = len(rounds)
    
    if total <= recent_rounds:
        # 轮次不超过 recent_rounds，不需要 LLM 总结
        result_parts = []
        for round in rounds:
            round_header = f"=== Round {round.index + 1}/{total} ==="
            formatted = format_round_full(round)
            if formatted:
                result_parts.append(f"{round_header}\n{formatted}")
        return None, "\n\n".join(result_parts)
    
    # 分离前面轮次和最近轮次
    earlier_rounds = rounds[:-recent_rounds]
    recent_rounds_list = rounds[-recent_rounds:]
    
    # 格式化前面轮次（供 LLM 摘要）
    earlier_text = format_rounds_for_llm(earlier_rounds)
    
    # 格式化最近轮次（完整保留）
    recent_parts = []
    for round in recent_rounds_list:
        round_header = f"=== Round {round.index + 1}/{total} ==="
        formatted = format_round_full(round)
        if formatted:
            recent_parts.append(f"{round_header}\n{formatted}")
    recent_text = "\n\n".join(recent_parts)
    
    return earlier_text, recent_text


def prepare_cold_summary_text(context: List[Dict[str, Any]]) -> str:
    """
    准备 Cold Summary 需要的文本内容
    
    Args:
        context: runtime 的完整 context
    
    Returns:
        供 LLM 摘要的完整对话文本
    """
    rounds = split_into_rounds(context)
    
    if not rounds:
        return "[No rounds found]"
    
    return format_rounds_for_llm(rounds)
