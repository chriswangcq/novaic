"""
Result Utils - 结果摘要和处理

用于生成工具执行结果的摘要（隐藏敏感数据如图片）。
"""

from typing import Dict, Any, List

# 尝试导入多模态处理工具
try:
    from utils import multimodal
    HAS_MULTIMODAL = True
    IMAGE_FIELD_NAMES = multimodal.IMAGE_FIELD_NAMES
except ImportError:
    HAS_MULTIMODAL = False
    IMAGE_FIELD_NAMES = [
        "screenshot", "image_base64", "image_data", 
        "base64_image", "image", "png_data", "jpeg_data"
    ]


def has_images(result: Dict[str, Any]) -> bool:
    """
    检查结果是否包含图片
    
    Args:
        result: 工具执行结果
        
    Returns:
        是否包含图片
        
    Example:
        >>> from task_queue.utils import has_images
        >>> has_images({"screenshot": "base64..."})
        True
        >>> has_images({"message": "hello"})
        False
    """
    if HAS_MULTIMODAL:
        return multimodal.has_images(result)
    
    # 回退检测
    for field_name in IMAGE_FIELD_NAMES:
        value = result.get(field_name)
        if isinstance(value, str) and len(value) > 100:
            return True
    
    return False


def summarize_result(
    result: Dict[str, Any],
    *,
    max_string_length: int = 100,
    max_keys: int = 5,
) -> Dict[str, Any]:
    """
    生成工具执行结果的摘要（用于广播到前端）
    
    隐藏图片数据，只显示关键信息。
    
    Args:
        result: 工具执行结果
        max_string_length: 字符串最大长度
        max_keys: 最大显示的键数
        
    Returns:
        摘要字典
        
    Example:
        >>> from task_queue.utils import summarize_result
        >>> summarize_result({"screenshot": "base64...", "message": "OK"})
        {'has_image': True, 'message': 'OK'}
    """
    summary = {}
    
    # 基本状态
    if result.get("success") is not None:
        summary["success"] = result["success"]
    
    # 错误信息优先
    if result.get("error"):
        summary["error"] = _truncate(str(result["error"]), max_string_length)
        return summary
    
    # 获取内层结果
    inner = result.get("result", result)
    
    if isinstance(inner, dict):
        # 检查是否有图片
        if has_images(inner):
            summary["has_image"] = True
        
        # 优先提取的关键字段
        priority_keys = ["message", "url", "output", "content", "status", "id", "success"]
        
        for key in priority_keys:
            if key in inner:
                val = inner[key]
                summary[key] = _format_value(val, max_string_length)
        
        # 如果没有优先字段，提取前几个非图片字段
        if len(summary) <= 2:  # 只有 success 和可能的 has_image
            count = 0
            for key in inner.keys():
                if count >= max_keys:
                    break
                # 跳过图片字段和内部字段
                if key in IMAGE_FIELD_NAMES or key == "_mcp_content" or key in priority_keys:
                    continue
                
                val = inner[key]
                summary[key] = _format_value(val, max_string_length // 2)
                count += 1
                
    elif isinstance(inner, str):
        summary["output"] = _truncate(inner, max_string_length)
    
    return summary if summary else {"done": True}


def _truncate(s: str, max_length: int) -> str:
    """截断字符串"""
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s


def _format_value(val: Any, max_length: int) -> Any:
    """格式化值"""
    if isinstance(val, str):
        return _truncate(val, max_length)
    elif isinstance(val, (dict, list)):
        return f"({type(val).__name__})"
    return val


def clean_context_for_summary(context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    清理 context 用于摘要生成
    
    移除内部元数据和过长的内容。
    
    Args:
        context: 原始对话历史
        
    Returns:
        清理后的对话历史
    """
    clean = []
    
    for msg in context:
        clean_msg = {}
        for k, v in msg.items():
            # 跳过内部字段
            if k.startswith("_"):
                continue
            # 截断过长内容
            if isinstance(v, str) and len(v) > 5000:
                clean_msg[k] = v[:100] + "...[truncated]"
            else:
                clean_msg[k] = v
        
        if clean_msg:
            clean.append(clean_msg)
    
    return clean
