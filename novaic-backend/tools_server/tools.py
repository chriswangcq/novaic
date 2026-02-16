"""
Tools Server - 工具定义（精简版）

优化后的工具集，去除冗余和低频工具。

工具分类：
- runtime: 8 个工具（Agent/SubAgent 管理）
- chat: 3 个工具（用户交互）
- memory: 4 个工具（键值存储）
- task: 7 个工具（任务管理）
- notebook: 4 个工具（笔记记录）
- qemu: 2 个工具（VM 状态管理）
- vm: 25 个工具（Desktop 自动化）
  - Browser (9): navigate, click, type, screenshot, scroll, evaluate, get_tabs, switch_tab, close_tab
  - Desktop (3): screenshot, mouse, keyboard
  - Shell (1): shell_exec
  - File (4): read, write, list, info
  - Window (3): list_windows, focus_window, launch_app
  - Context (4): system_snapshot, directory_snapshot, clipboard_get, clipboard_set
- mobile: 12 个工具（Android 设备控制）
  - Core (4): screenshot, touch, input, shell
  - App (3): install, launch, list
  - UI (2): dump, find
  - File (3): push, pull, list

总计: 65 个工具（从 102 精简）

Tool definitions live in common.tools.definitions; this module re-exports and adds helpers.
"""

from typing import Dict, List, Any, Optional

from common.tools.definitions import (
    BUILTIN_TOOLS,
    VM_TOOLS,
)

# Re-export for backward compatibility (executor, api, etc. may import from tools_server.tools)
__all__ = [
    "BUILTIN_TOOLS",
    "VM_TOOLS",
    "get_all_tools",
    "get_tool_by_name",
    "get_tools_by_category",
    "get_tool_category",
    "get_tool_count",
    "format_tools_for_openai",
    "get_stats",
]

# Tool name to category mapping (for quick lookup)
_TOOL_NAME_TO_CATEGORY: Dict[str, str] = {}
_TOOL_BY_NAME: Dict[str, Dict[str, Any]] = {}


def _build_indexes():
    """Build tool indexes for quick lookup."""
    global _TOOL_NAME_TO_CATEGORY, _TOOL_BY_NAME
    for category, tools in BUILTIN_TOOLS.items():
        for tool in tools:
            name = tool.get("name")
            if name:
                _TOOL_NAME_TO_CATEGORY[name] = category
                _TOOL_BY_NAME[name] = tool


def get_all_tools() -> List[Dict[str, Any]]:
    """
    Get all built-in tools as a flat list.

    Returns:
        List of all tool definitions
    """
    all_tools = []
    for tools in BUILTIN_TOOLS.values():
        all_tools.extend(tools)
    return all_tools


def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a tool definition by name.

    Args:
        name: Tool name

    Returns:
        Tool definition dict or None if not found
    """
    if not _TOOL_BY_NAME:
        _build_indexes()
    return _TOOL_BY_NAME.get(name)


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all tools in a category.

    Args:
        category: Category name (e.g., "memory", "runtime", "chat", "web", "vm", "mobile")

    Returns:
        List of tool definitions in that category
    """
    return BUILTIN_TOOLS.get(category, [])


def get_tool_category(tool_name: str) -> Optional[str]:
    """
    Get the category of a tool by its name.

    Args:
        tool_name: Tool name

    Returns:
        Category name or None if not found
    """
    if not _TOOL_NAME_TO_CATEGORY:
        _build_indexes()
    return _TOOL_NAME_TO_CATEGORY.get(tool_name)


def get_tool_count() -> Dict[str, int]:
    """Get tool count by category."""
    return {cat: len(tools) for cat, tools in BUILTIN_TOOLS.items() if tools}


def format_tools_for_openai() -> List[Dict[str, Any]]:
    """
    Format all tools for OpenAI function calling API.

    Returns:
        List of tools in OpenAI format
    """
    tools = []
    for tool in get_all_tools():
        # Convert inputSchema to parameters
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {})
            }
        }
        tools.append(openai_tool)
    return tools


def get_stats() -> Dict[str, Any]:
    """
    Get comprehensive statistics about the tool set.

    Returns:
        Dict with statistics
    """
    return {
        "total": sum(len(tools) for tools in BUILTIN_TOOLS.values()),
        "by_category": get_tool_count(),
        "categories": list(BUILTIN_TOOLS.keys()),
    }


# Build indexes on module import
_build_indexes()
