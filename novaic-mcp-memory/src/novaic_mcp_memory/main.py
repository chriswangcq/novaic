"""
NovAIC MCP Server for Memory & State Management.

Provides persistent memory and state tracking tools:
- memory_save/recall/delete - Key-value storage with namespaces
- memory_list_namespaces - List all namespaces
- task_log/history - Action logging
- goal_set/progress/complete - Goal tracking
- session_state - Session overview
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP

# Configuration
MEMORY_DIR = Path(os.environ.get(
    "NOVAIC_MEMORY_DIR",
    os.path.expanduser("~/.novaic/memory")
))
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

mcp = FastMCP(
    name="novaic-memory",
    instructions="""NovAIC Memory - 记忆与状态管理

10 个工具用于持久化记忆、任务追踪和目标管理。

## 工具一览

### 记忆存储 (4)
| 工具 | 用途 |
|------|------|
| memory_save | 保存记忆 (key-value) |
| memory_recall | 读取记忆 |
| memory_delete | 删除记忆 |
| memory_list_namespaces | 列出所有命名空间 |

### 任务追踪 (2)
| 工具 | 用途 |
|------|------|
| task_log | 记录执行动作 |
| task_history | 查看动作历史 |

### 目标管理 (3)
| 工具 | 用途 |
|------|------|
| goal_set | 设定目标和子任务 |
| goal_progress | 更新进度 |
| goal_complete | 完成目标 |

### 状态总览 (1)
| 工具 | 用途 |
|------|------|
| session_state | 获取当前会话状态概览 |

## 使用场景

### 1. 跨会话记忆
保存用户偏好、项目信息等长期记忆：
```
memory_save("user_name", "张三")
memory_save("project", {"name": "myapp", "lang": "python"}, namespace="work")

# 后续会话中读取
memory_recall("user_name")
memory_recall(namespace="work")  # 获取 work 命名空间所有记忆
```

### 2. 任务追踪
记录执行过程，便于回顾：
```
task_log("打开浏览器", status="completed")
task_log("搜索 Python 文档", details="找到 5 个结果")
task_history(limit=10)  # 查看最近 10 条
```

### 3. 目标管理
跟踪复杂任务进度：
```
goal_set("完成用户模块", subtasks=["设计 API", "实现 CRUD", "编写测试", "文档"])
goal_progress(completed_subtask="设计 API")
goal_progress(progress_note="CRUD 实现 50%")
goal_complete(summary="所有功能已完成并测试通过")
```

### 4. 会话状态检查
快速了解当前状态：
```
session_state()
# 返回: 当前目标、最近动作、任务统计
```

## 命名空间建议

| 命名空间 | 用途 |
|---------|------|
| default | 通用记忆 |
| settings | 用户偏好设置 |
| work | 工作/项目相关 |
| context | 上下文信息 |

## 注意事项

- persistent=True (默认) 会保存到磁盘
- 记忆存储在 ~/.novaic/memory/
- task_history 最多保留 100 条
"""
)

# Session state (in-memory, not persisted)
_session_memory: Dict[str, Dict[str, Any]] = {}
_task_history: List[Dict[str, Any]] = []
_current_goal: Optional[Dict[str, Any]] = None
_session_start = datetime.now().isoformat()


def _get_memory_file(namespace: str = "default") -> Path:
    """Get memory file path for namespace."""
    return MEMORY_DIR / f"{namespace}.json"


def _load_persistent_memory(namespace: str = "default") -> Dict[str, Any]:
    """Load persistent memory from disk."""
    file_path = _get_memory_file(namespace)
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_persistent_memory(data: Dict[str, Any], namespace: str = "default"):
    """Save persistent memory to disk."""
    file_path = _get_memory_file(namespace)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@mcp.tool()
async def memory_save(
    key: str,
    value: Any,
    namespace: Optional[str] = "default",
    persistent: Optional[bool] = True
) -> Dict[str, Any]:
    """
    Save a memory value.
    
    Store information that persists across sessions. Use namespaces
    to organize related data.
    
    Args:
        key: Memory key name
        value: Value to store (any JSON-serializable value)
        namespace: Namespace for grouping (default: "default")
        persistent: Whether to persist to disk (default: True)
    
    Returns:
        Dictionary with success status
    
    Examples:
        - memory_save("current_task", "Fix login bug")
        - memory_save("project", {"name": "myapp", "type": "python"})
        - memory_save("theme", "dark", namespace="settings")
    """
    try:
        timestamp = datetime.now().isoformat()
        
        # Save to session memory
        if namespace not in _session_memory:
            _session_memory[namespace] = {}
        
        _session_memory[namespace][key] = {
            "value": value,
            "updated_at": timestamp
        }
        
        # Persist to disk
        if persistent:
            memory = _load_persistent_memory(namespace)
            memory[key] = {
                "value": value,
                "updated_at": timestamp
            }
            _save_persistent_memory(memory, namespace)
        
        return {
            "success": True,
            "key": key,
            "namespace": namespace,
            "persistent": persistent
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def memory_recall(
    key: Optional[str] = None,
    namespace: Optional[str] = "default"
) -> Dict[str, Any]:
    """
    Recall a memory value.
    
    Retrieve stored information. If key is omitted, returns all
    memories in the namespace.
    
    Args:
        key: Memory key name (optional - omit to get all)
        namespace: Namespace to search (default: "default")
    
    Returns:
        Dictionary with value or all memories
    
    Examples:
        - memory_recall("current_task")
        - memory_recall()  # Get all in default namespace
        - memory_recall(namespace="settings")
    """
    try:
        # Merge session and persistent memory (session takes priority)
        session_data = _session_memory.get(namespace, {})
        persistent_data = _load_persistent_memory(namespace)
        merged = {**persistent_data, **session_data}
        
        if key:
            if key in merged:
                item = merged[key]
                return {
                    "success": True,
                    "key": key,
                    "value": item["value"],
                    "updated_at": item.get("updated_at"),
                    "found": True
                }
            else:
                return {
                    "success": True,
                    "key": key,
                    "value": None,
                    "found": False
                }
        else:
            # Return all memories
            result = {k: v["value"] for k, v in merged.items()}
            return {
                "success": True,
                "namespace": namespace,
                "memories": result,
                "count": len(result)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def memory_delete(
    key: str,
    namespace: Optional[str] = "default"
) -> Dict[str, Any]:
    """
    Delete a memory value.
    
    Remove a stored value from both session and persistent storage.
    
    Args:
        key: Memory key to delete
        namespace: Namespace (default: "default")
    
    Returns:
        Dictionary with deletion status
    """
    try:
        deleted = False
        
        # Delete from session memory
        if namespace in _session_memory and key in _session_memory[namespace]:
            del _session_memory[namespace][key]
            deleted = True
        
        # Delete from persistent storage
        memory = _load_persistent_memory(namespace)
        if key in memory:
            del memory[key]
            _save_persistent_memory(memory, namespace)
            deleted = True
        
        return {
            "success": True,
            "key": key,
            "deleted": deleted
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def memory_list_namespaces() -> Dict[str, Any]:
    """
    List all memory namespaces.
    
    Returns all namespaces that have stored data.
    
    Returns:
        Dictionary with list of namespace names
    """
    try:
        namespaces = set()
        
        # Session namespaces
        namespaces.update(_session_memory.keys())
        
        # Persistent namespaces
        if MEMORY_DIR.exists():
            for f in MEMORY_DIR.glob("*.json"):
                namespaces.add(f.stem)
        
        return {
            "success": True,
            "namespaces": sorted(list(namespaces))
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def task_log(
    action: str,
    details: Optional[str] = None,
    status: Optional[str] = "completed"
) -> Dict[str, Any]:
    """
    Log a task or action.
    
    Record actions for history tracking. Useful for maintaining
    a log of what has been done.
    
    Args:
        action: Description of the action
        details: Additional details (optional)
        status: Status - "completed", "failed", or "in_progress"
    
    Returns:
        Dictionary with logged entry
    
    Examples:
        - task_log("Opened VSCode")
        - task_log("Edited main.py", details="Modified line 42")
        - task_log("Running tests", status="in_progress")
    """
    global _task_history
    try:
        entry = {
            "action": action,
            "details": details,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        _task_history.append(entry)
        
        # Keep only last 100 entries
        if len(_task_history) > 100:
            _task_history = _task_history[-100:]
        
        return {
            "success": True,
            "logged": entry,
            "history_count": len(_task_history)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def task_history(
    limit: Optional[int] = 20,
    status_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get task history.
    
    Retrieve logged actions with optional filtering.
    
    Args:
        limit: Maximum entries to return (default: 20)
        status_filter: Filter by status (optional)
    
    Returns:
        Dictionary with history entries
    """
    try:
        history = _task_history
        
        if status_filter:
            history = [h for h in history if h["status"] == status_filter]
        
        recent = history[-limit:] if limit else history
        
        return {
            "success": True,
            "history": recent,
            "total_count": len(_task_history),
            "filtered_count": len(history)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def goal_set(
    goal: str,
    subtasks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Set a goal to track.
    
    Define a goal with optional subtasks to track progress.
    
    Args:
        goal: Goal description
        subtasks: List of subtask descriptions (optional)
    
    Returns:
        Dictionary with goal info
    
    Examples:
        - goal_set("Fix login bug")
        - goal_set("Refactor user module", subtasks=["Analyze code", "Design", "Implement", "Test"])
    """
    global _current_goal
    try:
        _current_goal = {
            "goal": goal,
            "subtasks": subtasks or [],
            "completed_subtasks": [],
            "started_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        # Persist goal
        await memory_save("_current_goal", _current_goal, namespace="_system")
        
        return {
            "success": True,
            "goal": goal,
            "subtasks_count": len(subtasks or [])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def goal_progress(
    completed_subtask: Optional[str] = None,
    progress_note: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update goal progress.
    
    Mark subtasks as complete or add progress notes.
    
    Args:
        completed_subtask: Subtask that was completed (optional)
        progress_note: Note about progress (optional)
    
    Returns:
        Dictionary with progress info
    """
    global _current_goal
    try:
        if not _current_goal:
            # Try to restore from persistent storage
            result = await memory_recall("_current_goal", namespace="_system")
            if result.get("found"):
                _current_goal = result["value"]
            else:
                return {"success": False, "error": "No goal set. Use goal_set first."}
        
        if completed_subtask and completed_subtask in _current_goal["subtasks"]:
            if completed_subtask not in _current_goal["completed_subtasks"]:
                _current_goal["completed_subtasks"].append(completed_subtask)
        
        if progress_note:
            if "notes" not in _current_goal:
                _current_goal["notes"] = []
            _current_goal["notes"].append({
                "note": progress_note,
                "timestamp": datetime.now().isoformat()
            })
        
        # Calculate progress
        total = len(_current_goal["subtasks"])
        completed = len(_current_goal["completed_subtasks"])
        progress = (completed / total * 100) if total > 0 else 0
        
        # Persist
        await memory_save("_current_goal", _current_goal, namespace="_system")
        
        return {
            "success": True,
            "goal": _current_goal["goal"],
            "progress_percent": round(progress, 1),
            "completed": completed,
            "total": total,
            "remaining_subtasks": [
                s for s in _current_goal["subtasks"]
                if s not in _current_goal["completed_subtasks"]
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def goal_complete(
    summary: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mark current goal as complete.
    
    Finalize the current goal and archive it.
    
    Args:
        summary: Completion summary (optional)
    
    Returns:
        Dictionary with completion info
    """
    global _current_goal
    try:
        if not _current_goal:
            return {"success": False, "error": "No current goal"}
        
        _current_goal["status"] = "completed"
        _current_goal["completed_at"] = datetime.now().isoformat()
        _current_goal["summary"] = summary
        
        # Archive to history
        await memory_save(
            f"goal_{int(time.time())}",
            _current_goal,
            namespace="_goal_history"
        )
        
        result = {
            "success": True,
            "goal": _current_goal["goal"],
            "summary": summary
        }
        
        # Clear current goal
        _current_goal = None
        await memory_delete("_current_goal", namespace="_system")
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def session_state() -> Dict[str, Any]:
    """
    Get current session state overview.
    
    Returns a summary of the current session including goal,
    recent actions, and statistics.
    
    Returns:
        Dictionary with session overview
    """
    try:
        # Current goal info
        current_goal = None
        if _current_goal:
            total = len(_current_goal.get("subtasks", []))
            completed = len(_current_goal.get("completed_subtasks", []))
            current_goal = {
                "goal": _current_goal["goal"],
                "progress": f"{completed}/{total}" if total > 0 else "N/A",
                "status": _current_goal.get("status", "in_progress")
            }
        
        # Recent actions
        recent_actions = [h["action"] for h in _task_history[-5:]] if _task_history else []
        
        # Statistics
        completed_count = len([h for h in _task_history if h["status"] == "completed"])
        failed_count = len([h for h in _task_history if h["status"] == "failed"])
        
        return {
            "success": True,
            "session_start": _session_start,
            "current_goal": current_goal,
            "recent_actions": recent_actions,
            "task_stats": {
                "total": len(_task_history),
                "completed": completed_count,
                "failed": failed_count
            },
            "memory_namespaces": list(_session_memory.keys())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Run the MCP server."""
    import sys
    
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8084"))
    
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=host, port=port)
    elif transport == "stdio":
        mcp.run(transport="stdio")
    else:
        print(f"Unknown transport: {transport}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
