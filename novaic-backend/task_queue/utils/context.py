"""
Context Utils - Context 清理和处理

用于 LLM 调用前的消息预处理：
1. sanitize_context: 确保 tool_results 紧跟 assistant+tool_calls
2. process_multimodal_messages: 处理多模态内容（图片等）
"""

import json
from typing import Dict, Any, List

# 导入多模态处理工具
from . import multimodal
HAS_MULTIMODAL = True


def sanitize_context(context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    清理 context，确保 tool_results 紧跟在对应的 assistant+tool_calls 之后
    
    这对 LLM 调用很重要，否则 LLM 可能报错。
    
    处理：
    1. 过滤无效消息（空 role、空 content）
    2. 移除内部元数据字段（_round_id、_message_type 等）
    3. assistant message with tool_calls 后面必须紧跟对应的 tool_result
    4. 为缺失的 tool_result 添加占位符
    5. 移除孤立的 tool_result
    
    Args:
        context: 原始消息列表
        
    Returns:
        清理后的消息列表
        
    Example:
        >>> from task_queue.utils import sanitize_context
        >>> messages = [
        ...     {"role": "user", "content": "Hello"},
        ...     {"role": "assistant", "tool_calls": [{"id": "call_1", "function": {"name": "test"}}]},
        ...     {"role": "user", "content": "OK"},  # 乱序
        ...     {"role": "tool", "tool_call_id": "call_1", "content": "result"},
        ... ]
        >>> sanitized = sanitize_context(messages)
        >>> # tool_result 现在紧跟 assistant message
    """
    if not context:
        return []
    
    # 预处理：过滤和清理消息
    cleaned_context = []
    for msg in context:
        if not isinstance(msg, dict):
            continue
        
        role = msg.get("role", "")
        
        # 跳过内部元数据消息（没有 role 但有 _round_id 等字段）
        if not role and (msg.get("_round_id") or msg.get("_message_type") or msg.get("_idempotency_key")):
            continue
        
        # 跳过空 role 的消息
        if not role:
            continue
        
        # 对于非 tool 消息，检查 content 是否有效
        if role not in ("tool", "tool_result"):
            content = msg.get("content")
            tool_calls = msg.get("tool_calls")
            # assistant 可以只有 tool_calls 没有 content
            if role == "assistant" and tool_calls:
                pass
            elif not content and content != "":  # 允许空字符串
                continue
        
        # 移除内部字段，只保留 LLM 需要的字段
        cleaned_msg = {}
        for key in ("role", "content", "tool_calls", "tool_call_id", "name", "reasoning_content"):
            if key in msg:
                cleaned_msg[key] = msg[key]
        
        # 某些模型要求 tool_calls 的 assistant message 携带 reasoning_content
        if cleaned_msg.get("role") == "assistant" and cleaned_msg.get("tool_calls"):
            cleaned_msg.setdefault("reasoning_content", "")
        
        cleaned_context.append(cleaned_msg)
    
    context = cleaned_context
    
    # 第一遍：收集所有消息并跟踪 tool_calls
    assistant_tool_calls = {}  # tc_id -> {"assistant_idx": int, "name": str}
    tool_results = {}  # tc_id -> msg
    other_messages = []  # (original_idx, msg)
    assistant_messages_with_tools = {}  # idx -> msg
    
    for idx, msg in enumerate(context):
        role = msg.get("role")
        
        if role == "assistant" and msg.get("tool_calls"):
            assistant_messages_with_tools[idx] = msg
            for tc in msg["tool_calls"]:
                tc_id = tc.get("id")
                if tc_id:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "unknown")
                    assistant_tool_calls[tc_id] = {"assistant_idx": idx, "name": tool_name}
                    
        elif role == "tool_result" or role == "tool":
            tc_id = msg.get("tool_call_id")
            if tc_id and tc_id in assistant_tool_calls:
                tool_results[tc_id] = msg
            elif tc_id:
                # 孤立的 tool_result，忽略
                pass
            else:
                other_messages.append((idx, msg))
        else:
            other_messages.append((idx, msg))
    
    # 第二遍：按正确顺序构建结果
    result = []
    processed_assistant_indices = set()
    
    for orig_idx, msg in other_messages:
        # 插入之前的 assistant+tool_calls+tool_results
        for asst_idx in sorted(assistant_messages_with_tools.keys()):
            if asst_idx < orig_idx and asst_idx not in processed_assistant_indices:
                asst_msg = assistant_messages_with_tools[asst_idx]
                result.append(asst_msg)
                processed_assistant_indices.add(asst_idx)
                
                # 添加对应的 tool_results
                for tc in asst_msg.get("tool_calls", []):
                    tc_id = tc.get("id")
                    if tc_id:
                        if tc_id in tool_results:
                            result.append(tool_results[tc_id])
                        else:
                            # 缺失的 tool_result，添加占位符
                            func = tc.get("function", {})
                            tool_name = func.get("name", "unknown")
                            result.append({
                                "role": "tool",
                                "tool_call_id": tc_id,
                                "name": tool_name,
                                "content": "[Execution was interrupted. Please retry if needed.]"
                            })
        
        result.append(msg)
    
    # 添加末尾剩余的 assistant+tool_results
    for asst_idx in sorted(assistant_messages_with_tools.keys()):
        if asst_idx not in processed_assistant_indices:
            asst_msg = assistant_messages_with_tools[asst_idx]
            result.append(asst_msg)
            
            for tc in asst_msg.get("tool_calls", []):
                tc_id = tc.get("id")
                if tc_id:
                    if tc_id in tool_results:
                        result.append(tool_results[tc_id])
                    else:
                        func = tc.get("function", {})
                        tool_name = func.get("name", "unknown")
                        result.append({
                            "role": "tool",
                            "tool_call_id": tc_id,
                            "name": tool_name,
                            "content": "[Execution was interrupted. Please retry if needed.]"
                        })
    
    return result


def process_multimodal_messages(
    messages: List[Dict[str, Any]], 
    provider: str = "openai"
) -> List[Dict[str, Any]]:
    """
    处理消息中的多模态内容
    
    将 tool_result 中的图片提取出来，作为单独的 user message 添加
    （因为 LLM API 不支持在 tool result 中放图片）
    
    Args:
        messages: 原始消息列表
        provider: LLM 提供商 ("openai" 或 "anthropic")
        
    Returns:
        处理后的消息列表
        
    Example:
        >>> from task_queue.utils import process_multimodal_messages
        >>> messages = [
        ...     {"role": "tool", "content": '{"screenshot": "base64..."}'}
        ... ]
        >>> processed = process_multimodal_messages(messages, provider="openai")
        >>> # 图片被提取为单独的 user message
    """
    if not HAS_MULTIMODAL:
        return messages
    
    processed = []
    
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role in ("tool_result", "tool"):
            # 检查是否有图片
            try:
                result = json.loads(content) if isinstance(content, str) else content
            except (json.JSONDecodeError, TypeError):
                result = {"content": content}
            
            # 解包嵌套的 result 字段（工具返回格式：{success, result}）
            if isinstance(result, dict) and "result" in result and isinstance(result["result"], dict):
                inner_result = result["result"]
            else:
                inner_result = result
            
            if isinstance(inner_result, dict) and multimodal.has_images(inner_result):
                _, images = multimodal.extract_from_result(inner_result)
                
                # 生成纯文本版本（使用解包后的数据）
                inner_text_only = multimodal.result_to_text_only(inner_result)
                
                # 如果原始 result 有嵌套结构，重新包装
                if isinstance(result, dict) and "result" in result:
                    # 重新包装：{success: ..., result: {image_data: "[PLACEHOLDER]", ...}}
                    sanitized_result = {**result, "result": json.loads(inner_text_only)}
                    text_only = json.dumps(sanitized_result)
                else:
                    text_only = inner_text_only
                
                # 添加文本版本的 tool result
                processed.append({
                    **msg,
                    "content": text_only,
                })
                
                # 添加图片作为 user message
                if images:
                    tool_name = msg.get("name", "tool")
                    description = f"[Image from {tool_name}]"
                    
                    if provider == "anthropic":
                        img_content = multimodal.to_anthropic_content(images, description)
                    else:
                        img_content = multimodal.to_openai_content(images, description)
                    
                    processed.append({
                        "role": "user",
                        "content": img_content,
                    })
            else:
                processed.append(msg)
        else:
            processed.append(msg)
    
    return processed
