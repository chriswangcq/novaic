"""
多模态内容处理工具

基于 MCP 协议的 content 数组格式，提供通用的多模态内容提取和转换功能。
同时支持检测和提取常见的非标准图片字段格式（向后兼容）。

MCP content 格式 (标准):
[
    {"type": "text", "text": "..."},
    {"type": "image", "data": "base64...", "mimeType": "image/png"},
    {"type": "resource", "uri": "...", "mimeType": "...", "text": "..."}
]

常见非标准图片字段 (兼容):
- screenshot: base64 字符串
- image_base64: base64 字符串
- image_data: base64 字符串
- image: base64 字符串
"""

from typing import Any, Dict, List, Tuple, Optional
import json
import re

# 常见的图片字段名（用于检测非 MCP 标准格式的工具返回）
IMAGE_FIELD_NAMES = [
    "screenshot",      # desktop.screenshot, vnc screenshot
    "image_base64",    # 通用
    "image_data",      # 通用
    "base64_image",    # 通用
    "image",           # 简写
    "png_data",        # 特定格式
    "jpeg_data",       # 特定格式
]

# Base64 字符集正则（用于快速验证）
_BASE64_PATTERN = re.compile(r'^[A-Za-z0-9+/=]+$')


def _is_likely_base64_image(value: Any, min_length: int = 100) -> bool:
    """
    检查值是否可能是 base64 编码的图片数据
    
    Args:
        value: 要检查的值
        min_length: 最小长度（过短的字符串不太可能是图片）
        
    Returns:
        bool: 是否可能是 base64 图片
    """
    if not isinstance(value, str):
        return False
    if len(value) < min_length:
        return False
    # 检查是否符合 base64 字符集（只检查前 100 个字符以提高性能）
    sample = value[:100].replace('\n', '').replace('\r', '')
    return bool(_BASE64_PATTERN.match(sample))


def _parse_content_array(content: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, str]]]:
    """
    解析 MCP 标准 content 数组格式
    
    支持格式:
    - {"type": "text", "text": "..."}
    - {"type": "image", "data": "base64...", "mimeType": "image/png"}
    - {"type": "resource", "resource": {"blob": "base64...", "mimeType": "..."}}
    
    Args:
        content: MCP 标准 content 数组
    
    Returns:
        (text_content, images_list)
    """
    text_parts = []
    images = []
    
    for item in content:
        if not isinstance(item, dict):
            continue
            
        item_type = item.get("type", "")
        
        if item_type == "text":
            text = item.get("text", "")
            if text:
                text_parts.append(text)
        
        elif item_type == "image":
            data = item.get("data", "")
            if data and _is_likely_base64_image(data):
                images.append({
                    "data": data,
                    "mime_type": item.get("mimeType", item.get("mime_type", "image/png"))
                })
        
        elif item_type == "resource":
            # Embedded resource with binary data
            resource = item.get("resource", {})
            mime_type = resource.get("mimeType", resource.get("mime_type", ""))
            blob = resource.get("blob", "")
            
            if mime_type.startswith("image/") and blob and _is_likely_base64_image(blob):
                images.append({
                    "data": blob,
                    "mime_type": mime_type
                })
    
    return "\n".join(text_parts), images


def extract_from_result(result: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    """
    从工具结果中提取文本和图片列表
    
    优先级:
    1. _mcp_content (MCP 客户端转换后的标准格式)
    2. content 数组 (MCP 标准格式)
    3. 传统字段 (IMAGE_FIELD_NAMES)
    
    Args:
        result: 工具执行结果
        
    Returns:
        (text_content, images) 元组
        - text_content: 合并后的文本内容
        - images: 图片列表 [{"data": "base64...", "mime_type": "image/png"}, ...]
    """
    text_parts = []
    images = []
    
    # 1. 优先检查 _mcp_content
    if "_mcp_content" in result:
        mcp_content = result["_mcp_content"]
        if isinstance(mcp_content, list):
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
            
            # 如果找到了 _mcp_content，直接返回（不再检查其他字段）
            if text_parts or images:
                return "\n".join(text_parts) if text_parts else "", images
    
    # 2. 检查 content 数组（MCP 标准）
    if "content" in result:
        content = result["content"]
        if isinstance(content, list) and content:
            # 检查是否是 MCP 标准格式（包含 type 字段）
            has_type_field = any(
                isinstance(item, dict) and "type" in item 
                for item in content
            )
            if has_type_field:
                return _parse_content_array(content)
    
    # 3. 从常见图片字段提取（向后兼容非 MCP 标准格式）
    for field_name in IMAGE_FIELD_NAMES:
        value = result.get(field_name)
        if _is_likely_base64_image(value):
            # 推断 MIME 类型
            mime_type = "image/png"  # 默认 PNG
            if "jpeg" in field_name or "jpg" in field_name:
                mime_type = "image/jpeg"
            images.append({
                "data": value,
                "mime_type": mime_type
            })
    
    # 3. 生成文本描述（从非图片字段）
    if not text_parts:
        for key, value in result.items():
            if key == "_mcp_content":
                continue
            if key in IMAGE_FIELD_NAMES:
                continue
            # 跳过过长的值（可能是误识别的二进制数据）
            if isinstance(value, str) and len(value) > 1000:
                continue
            text_parts.append(f"{key}: {value}")
    
    return "\n".join(text_parts), images


def has_images(result: Dict[str, Any]) -> bool:
    """
    检查结果是否包含图片
    
    支持三种检测:
    1. MCP 标准格式: _mcp_content 数组中的 image 类型
    2. MCP 标准格式: content 数组中的 image 类型（新格式）
    3. 常见字段格式: screenshot, image_base64 等字段
    
    Args:
        result: 工具执行结果
        
    Returns:
        bool: 是否包含图片
    """
    # 1. 检查 _mcp_content（MCP 客户端转换格式）
    mcp_content = result.get("_mcp_content", [])
    for item in mcp_content:
        if isinstance(item, dict):
            if item.get("type") == "image" and item.get("data"):
                return True
            if item.get("type") == "resource":
                mime_type = item.get("mimeType", "")
                if mime_type.startswith("image/") and item.get("blob"):
                    return True
    
    # 2. 检查 content 数组（MCP 标准格式 - 新格式）
    content = result.get("content", [])
    if isinstance(content, list):
        # 检查是否是 MCP 标准格式（包含 type 字段）
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type == "image":
                    data = item.get("data", "")
                    if data and _is_likely_base64_image(data):
                        return True
                if item_type == "resource":
                    resource = item.get("resource", {})
                    mime_type = resource.get("mimeType", "")
                    blob = resource.get("blob", "")
                    if mime_type.startswith("image/") and blob and _is_likely_base64_image(blob):
                        return True
    
    # 3. 检查常见图片字段（向后兼容）
    for field_name in IMAGE_FIELD_NAMES:
        value = result.get(field_name)
        if _is_likely_base64_image(value):
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
    
    处理三种图片来源:
    1. _mcp_content 数组中的 image 类型 → 替换为占位符
    2. content 数组中的 image 类型 → 替换为占位符（MCP 标准格式）
    3. 常见图片字段 (screenshot 等) → 替换为占位符
    
    Args:
        result: 工具执行结果
        
    Returns:
        JSON 字符串，图片被替换为占位符
    """
    output = {}
    
    def sanitize_content_array(content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将 content 数组中的图片替换为占位符"""
        sanitized = []
        for item in content:
            if item.get("type") == "image":
                sanitized.append({
                    "type": "image",
                    "_placeholder": True,
                    "mimeType": item.get("mimeType", item.get("mime_type", "image/png")),
                    "_note": "Image data provided separately to LLM"
                })
            else:
                sanitized.append(item)
        return sanitized
    
    for key, value in result.items():
        if key == "_mcp_content" or key == "content":
            # 替换 content 数组中的图片数据为占位符
            if isinstance(value, list):
                output[key] = sanitize_content_array(value)
            else:
                output[key] = value
        elif key in IMAGE_FIELD_NAMES and _is_likely_base64_image(value):
            # 替换常见图片字段为占位符
            output[key] = "[IMAGE DATA PROVIDED SEPARATELY TO LLM]"
        else:
            output[key] = value
    
    return json.dumps(output)
