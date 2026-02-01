"""
多模态内容处理工具

基于 MCP 协议的 content 数组格式，提供通用的多模态内容提取和转换功能。

MCP content 格式:
[
    {"type": "text", "text": "..."},
    {"type": "image", "data": "base64...", "mimeType": "image/png"},
    {"type": "resource", "uri": "...", "mimeType": "...", "text": "..."}
]
"""

from typing import Any, Dict, List, Tuple, Optional
import json


def extract_from_result(result: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """
    从工具结果中提取文本和图片列表
    
    Args:
        result: 工具执行结果，包含 _mcp_content 数组
        
    Returns:
        (text_content, images) 元组
        - text_content: 合并后的文本内容
        - images: 图片列表 [{"data": "base64...", "mime_type": "image/png"}, ...]
    """
    mcp_content = result.get("_mcp_content", [])
    
    text_parts = []
    images = []
    
    for item in mcp_content:
        item_type = item.get("type", "")
        
        if item_type == "text":
            text = item.get("text", "")
            if text:
                text_parts.append(text)
                
        elif item_type == "image":
            data = item.get("data", "")
            if data:
                images.append({
                    "data": data,
                    "mime_type": item.get("mimeType", "image/png")
                })
                
        elif item_type == "resource":
            # 资源可能包含内嵌文本或二进制数据
            text = item.get("text", "")
            if text:
                text_parts.append(text)
            # 如果是图片资源
            mime_type = item.get("mimeType", "")
            if mime_type.startswith("image/") and item.get("blob"):
                images.append({
                    "data": item.get("blob", ""),
                    "mime_type": mime_type
                })
    
    return "\n".join(text_parts), images


def has_images(result: Dict[str, Any]) -> bool:
    """检查结果是否包含图片"""
    mcp_content = result.get("_mcp_content", [])
    for item in mcp_content:
        if item.get("type") == "image" and item.get("data"):
            return True
        if item.get("type") == "resource":
            mime_type = item.get("mimeType", "")
            if mime_type.startswith("image/") and item.get("blob"):
                return True
    return False


def to_openai_content(images: List[Dict[str, str]], text: str = "") -> List[Dict[str, Any]]:
    """
    转换为 OpenAI 多模态 content 格式
    
    Args:
        images: 图片列表
        text: 附加的文本说明
        
    Returns:
        OpenAI content 数组 [{"type": "image_url", ...}, {"type": "text", ...}]
    """
    content = []
    
    for img in images:
        data_url = f"data:{img['mime_type']};base64,{img['data']}"
        content.append({
            "type": "image_url",
            "image_url": {"url": data_url}
        })
    
    if text:
        content.append({"type": "text", "text": text})
    
    return content


def to_anthropic_content(images: List[Dict[str, str]], text: str = "") -> List[Dict[str, Any]]:
    """
    转换为 Anthropic 多模态 content 格式
    
    Args:
        images: 图片列表
        text: 附加的文本说明
        
    Returns:
        Anthropic content 数组 [{"type": "image", ...}, {"type": "text", ...}]
    """
    content = []
    
    for img in images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img["mime_type"],
                "data": img["data"]
            }
        })
    
    if text:
        content.append({"type": "text", "text": text})
    
    return content


def result_to_text_only(result: Dict[str, Any]) -> str:
    """
    将结果转换为纯文本格式（用于存储到 context，不含图片 base64）
    
    Args:
        result: 工具执行结果
        
    Returns:
        JSON 字符串，图片被替换为占位符
    """
    # 复制结果，处理 _mcp_content
    output = {}
    
    for key, value in result.items():
        if key == "_mcp_content":
            # 替换图片数据为占位符
            sanitized_content = []
            for item in value:
                if item.get("type") == "image":
                    sanitized_content.append({
                        "type": "image",
                        "_placeholder": True,
                        "mimeType": item.get("mimeType", "image/png"),
                        "_note": "Image data provided separately to LLM"
                    })
                else:
                    sanitized_content.append(item)
            output["_mcp_content"] = sanitized_content
        else:
            output[key] = value
    
    return json.dumps(output)
