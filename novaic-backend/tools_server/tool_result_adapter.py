"""
工具结果适配层：按 tool_name 将 raw_result 中的 base64 转为 File Service URL

新增工具时在 TOOL_ADAPTER_REGISTRY 中追加一行即可。
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx

from common.config import ServiceConfig
from common.http.clients import internal_async_client

logger = logging.getLogger(__name__)

FILE_SERVICE_URL = ServiceConfig.FILE_SERVICE_URL.rstrip("/")
MIN_B64_LEN = 100


def filename_from_url(url: str) -> str:
    """从 File Service URL 提取文件名（方案 C：由 File Service 生成，此处仅解析）"""
    if not url:
        return "file"
    return url.rsplit("/", 1)[-1].split("?")[0] or "file"


def tool_result(
    text: str,
    files_created: Optional[List[Dict[str, Any]]] = None,
    display_files: Optional[List[Dict[str, Any]]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    统一工具结果格式。

    Args:
        text: 文本说明
        files_created: 本次创建的文件 [{url, filename, modality}]，仅元数据
        display_files: 需要展示给 LLM 的文件 [{url, filename, modality}]，会进入上下文
        extra: 额外字段

    Examples:
        screenshot: files_created=[{...}], display_files=[{...}]  # LLM 要看
        file_pull:  files_created=[{...}], display_files=[]       # 只传输
        display:    files_created=[],      display_files=[{...}]  # 显式展示
    """
    out: Dict[str, Any] = {"success": True, "text": text}
    out["files_created"] = files_created or []
    out["display_files"] = display_files or []
    if extra:
        out.update(extra)
    # 便捷字段：单文件时设置 file_url
    if files_created and len(files_created) == 1:
        out.setdefault("file_url", files_created[0]["url"])
    return out


async def _upload_base64_to_file_service(
    base64_data: str,
    agent_id: str,
    category: str = "images",
    mime_type: str = "image/png",
) -> Optional[str]:
    try:
        async with internal_async_client(timeout=30.0) as client:
            resp = await client.post(
                f"{FILE_SERVICE_URL}/api/files/from-base64",
                json={"data": base64_data, "agent_id": agent_id, "category": category, "mime_type": mime_type},
            )
            resp.raise_for_status()
            return resp.json().get("url")
    except Exception as e:
        logger.warning(f"[ToolResultAdapter] upload to File Service failed: {e}")
        return None


# 提取函数类型：(raw_result) -> List[Tuple[base64_str, mime_type]]
ExtractFn = Callable[[Dict[str, Any]], List[Tuple[str, str]]]


def _extract_screenshot_fields(raw: Dict[str, Any], fields: Tuple[str, ...] = ("screenshot", "data")) -> List[Tuple[str, str]]:
    """从顶层字段提取 base64 截图"""
    for f in fields:
        val = raw.get(f)
        if isinstance(val, str) and len(val) > MIN_B64_LEN:
            return [(val, "image/png")]
    return []


def _extract_content_images(raw: Dict[str, Any]) -> List[Tuple[str, str]]:
    """从 content / _mcp_content 数组中提取 type=image 的 data"""
    out: List[Tuple[str, str]] = []
    content = raw.get("content") or raw.get("_mcp_content") or []
    if not isinstance(content, list):
        return out
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "image":
            data = item.get("data")
            if isinstance(data, str) and len(data) > MIN_B64_LEN:
                mime = item.get("mimeType") or item.get("mime_type") or "image/png"
                out.append((data, mime))
    return out


# 工具适配配置：(extract_fn, display, text_fn)
# text_fn: (tool_name, file_refs) -> str
ToolAdapterConfig = Tuple[ExtractFn, bool, Callable[[str, List[Dict]], str]]


def _text_screenshot(tool_name: str, file_refs: List[Dict]) -> str:
    if tool_name == "mouse":
        return "Mouse aim screenshot captured."
    return f"{tool_name} captured."


def _text_mobile_screenshot(tool_name: str, file_refs: List[Dict]) -> str:
    if tool_name == "mobile_touch":
        return "Touch aim screenshot captured."
    return "Mobile screenshot captured."


def _text_content_image(tool_name: str, file_refs: List[Dict]) -> str:
    return f"Content includes {len(file_refs)} image(s)."


def _replace_base64_with_urls(raw_result: Dict[str, Any], file_refs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    将原始结果中的 base64 字段替换为 file_url 占位符，保持 JSON 结构不变。
    """
    import copy
    result = copy.deepcopy(raw_result)
    url_idx = 0
    
    # 替换顶层 screenshot / data 字段
    for field in ("screenshot", "data"):
        if field in result and isinstance(result[field], str) and len(result[field]) > MIN_B64_LEN:
            if url_idx < len(file_refs):
                result[field] = f"file_url: {file_refs[url_idx]['url']}"
                url_idx += 1
    
    # 替换 content / _mcp_content 数组中的 type=image
    for content_field in ("content", "_mcp_content"):
        content = result.get(content_field)
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image":
                    data = item.get("data")
                    if isinstance(data, str) and len(data) > MIN_B64_LEN:
                        if url_idx < len(file_refs):
                            item["data"] = f"file_url: {file_refs[url_idx]['url']}"
                            url_idx += 1
    
    return result


TOOL_ADAPTER_REGISTRY: Dict[str, ToolAdapterConfig] = {
    # VM 截图：screenshot / data 字段
    "screenshot": (_extract_screenshot_fields, True, _text_screenshot),
    "browser_screenshot": (_extract_screenshot_fields, True, _text_screenshot),
    "mouse": (_extract_screenshot_fields, True, _text_screenshot),
    # Mobile 截图
    "mobile_screenshot": (_extract_screenshot_fields, True, _text_mobile_screenshot),
    "mobile_touch": (_extract_screenshot_fields, True, _text_mobile_screenshot),
    # content / _mcp_content 数组中 type=image
    "browser_content": (_extract_content_images, True, _text_content_image),
    "clipboard_get": (_extract_content_images, False, _text_content_image),
}


async def _upload_items(
    items: List[Tuple[str, str]],
    agent_id: str,
    category: str,
) -> List[Dict[str, Any]]:
    """上传 base64 列表，返回 file_ref 列表"""
    file_refs: List[Dict[str, Any]] = []
    for b64, mime_type in items:
        url = await _upload_base64_to_file_service(b64, agent_id, category=category, mime_type=mime_type)
        if url:
            fn = filename_from_url(url)
            file_refs.append({"url": url, "filename": fn, "modality": "image"})
    return file_refs


async def adapt_tool_result(
    tool_name: str,
    raw_result: Dict[str, Any],
    agent_id: str,
    category: str = "images",
) -> Optional[Dict[str, Any]]:
    """
    按 tool_name 将 raw_result 中的 base64 转为 File Service URL，返回统一格式。

    1. 若 tool_name 在 TOOL_ADAPTER_REGISTRY 中，使用对应配置提取并转换
    2. 否则尝试 content / _mcp_content 中的 type=image（MCP 等外部工具兜底）

    Returns:
        转换后的结果 dict，或 None（无 base64 / 上传失败时保持原样）
    """
    if tool_name in TOOL_ADAPTER_REGISTRY:
        extract_fn, display, text_fn = TOOL_ADAPTER_REGISTRY[tool_name]
        items = extract_fn(raw_result)
    else:
        # MCP/外部工具兜底：content/_mcp_content 中的 type=image
        items = _extract_content_images(raw_result)
        if not items:
            return None
        display, text_fn = True, lambda tn, fr: f"{tn}: content includes {len(fr)} image(s)."

    if not items:
        return None

    file_refs = await _upload_items(items, agent_id, category)
    if not file_refs:
        return None

    # 构建替换后的结果：将 base64 替换为 URL 占位符
    replaced_result = _replace_base64_with_urls(raw_result, file_refs)
    
    # 将替换后的 JSON 作为 text（保持原始结构）
    import json
    text = json.dumps(replaced_result, ensure_ascii=False, indent=2)
    
    return tool_result(
        text=text,
        files_created=file_refs,
        display_files=file_refs if display else [],
    )
