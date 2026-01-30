"""
Memory MCP Server - 持久化存储和状态管理

提供键值存储、任务追踪、目标管理等功能。
每个 Agent 有独立的内存空间，通过 agent_id 隔离。
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from .base import BaseMCPServer

logger = logging.getLogger(__name__)

# Global configuration
_base_memory_dir: Optional[Path] = None


def init_memory_dir(data_dir: Path):
    """Initialize base memory directory. Called by Gateway on startup."""
    global _base_memory_dir
    _base_memory_dir = data_dir / "memory"
    _base_memory_dir.mkdir(parents=True, exist_ok=True)


class MemoryMCPServer(BaseMCPServer):
    """
    Memory MCP Server。
    
    每个 Agent 的数据存储在独立目录中，通过 agent_id 隔离。
    
    提供工具：
    - memory_save: 保存内存值
    - memory_recall: 读取内存值
    - memory_delete: 删除内存值
    - memory_list_namespaces: 列出命名空间
    - task_log: 记录任务
    - task_history: 获取任务历史
    - goal_set: 设置目标
    - goal_progress: 更新目标进度
    - goal_complete: 完成目标
    - session_state: 获取会话状态
    """
    
    name = "memory"
    description = "持久化存储和状态管理工具"
    
    def __init__(self, agent_id: Optional[str] = None):
        """
        初始化 Memory Server。
        
        Args:
            agent_id: Agent ID，用于隔离内存空间
        """
        # Agent 隔离的内存空间
        self._agent_id = agent_id or "default"
        self._session_memory: Dict[str, Dict[str, Any]] = {}
        self._task_history: List[Dict[str, Any]] = []
        self._current_goal: Optional[Dict[str, Any]] = None
        self._session_start = datetime.now().isoformat()
        
        super().__init__(agent_id=agent_id)
        
        logger.info(f"[MemoryMCPServer] Initialized for agent: {self._agent_id}")
    
    def _get_memory_dir(self) -> Path:
        """获取当前 agent 的内存目录。"""
        if _base_memory_dir:
            agent_dir = _base_memory_dir / self._agent_id
        elif os.environ.get("NOVAIC_DATA_DIR"):
            agent_dir = Path(os.environ["NOVAIC_DATA_DIR"]) / "memory" / self._agent_id
        else:
            agent_dir = Path.home() / ".novaic" / "memory" / self._agent_id
        
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir
    
    def _get_memory_file(self, namespace: str = "default") -> Path:
        """获取指定命名空间的内存文件路径。"""
        return self._get_memory_dir() / f"{namespace}.json"
    
    def _load_persistent_memory(self, namespace: str = "default") -> Dict[str, Any]:
        """从磁盘加载持久化内存。"""
        file_path = self._get_memory_file(namespace)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_persistent_memory(self, data: Dict[str, Any], namespace: str = "default"):
        """保存持久化内存到磁盘。"""
        file_path = self._get_memory_file(namespace)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _build_instructions(self) -> str:
        return """Memory MCP - 持久化存储和状态管理

## 工具列表

| 工具 | 用途 |
|------|------|
| memory_save | 保存键值对 |
| memory_recall | 读取键值对 |
| memory_delete | 删除键值对 |
| memory_list_namespaces | 列出所有命名空间 |
| task_log | 记录任务操作 |
| task_history | 获取任务历史 |
| goal_set | 设置目标和子任务 |
| goal_progress | 更新目标进度 |
| goal_complete | 完成当前目标 |
| session_state | 获取会话状态概览 |

## 使用场景

- **memory_***: 跨会话持久化存储
- **task_***: 记录和追踪操作历史
- **goal_***: 管理复杂任务的进度
"""
    
    def _register_tools(self) -> None:
        """注册所有 Memory 工具。"""
        server = self  # Capture for closures
        
        @self.mcp.tool()
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
                memory_save("current_task", "Fix login bug")
                memory_save("project", {"name": "myapp", "type": "python"})
                memory_save("theme", "dark", namespace="settings")
            """
            try:
                timestamp = datetime.now().isoformat()
                
                if namespace not in server._session_memory:
                    server._session_memory[namespace] = {}
                
                server._session_memory[namespace][key] = {
                    "value": value,
                    "updated_at": timestamp
                }
                
                if persistent:
                    memory = server._load_persistent_memory(namespace)
                    memory[key] = {
                        "value": value,
                        "updated_at": timestamp
                    }
                    server._save_persistent_memory(memory, namespace)
                
                return {
                    "success": True,
                    "key": key,
                    "namespace": namespace,
                    "persistent": persistent
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
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
            """
            try:
                session_data = server._session_memory.get(namespace, {})
                persistent_data = server._load_persistent_memory(namespace)
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
                    result = {k: v["value"] for k, v in merged.items()}
                    return {
                        "success": True,
                        "namespace": namespace,
                        "memories": result,
                        "count": len(result)
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
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
                
                if namespace in server._session_memory and key in server._session_memory[namespace]:
                    del server._session_memory[namespace][key]
                    deleted = True
                
                memory = server._load_persistent_memory(namespace)
                if key in memory:
                    del memory[key]
                    server._save_persistent_memory(memory, namespace)
                    deleted = True
                
                return {
                    "success": True,
                    "key": key,
                    "deleted": deleted
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def memory_list_namespaces() -> Dict[str, Any]:
            """
            List all memory namespaces.
            
            Returns all namespaces that have stored data.
            
            Returns:
                Dictionary with list of namespace names
            """
            try:
                namespaces = set()
                namespaces.update(server._session_memory.keys())
                
                mem_dir = server._get_memory_dir()
                if mem_dir.exists():
                    for f in mem_dir.glob("*.json"):
                        namespaces.add(f.stem)
                
                return {
                    "success": True,
                    "namespaces": sorted(list(namespaces))
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
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
            """
            try:
                entry = {
                    "action": action,
                    "details": details,
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
                
                server._task_history.append(entry)
                
                if len(server._task_history) > 100:
                    server._task_history = server._task_history[-100:]
                
                return {
                    "success": True,
                    "logged": entry,
                    "history_count": len(server._task_history)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
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
                history = server._task_history
                
                if status_filter:
                    history = [h for h in history if h["status"] == status_filter]
                
                recent = history[-limit:] if limit else history
                
                return {
                    "success": True,
                    "history": recent,
                    "total_count": len(server._task_history),
                    "filtered_count": len(history)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
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
            """
            try:
                server._current_goal = {
                    "goal": goal,
                    "subtasks": subtasks or [],
                    "completed_subtasks": [],
                    "started_at": datetime.now().isoformat(),
                    "status": "in_progress"
                }
                
                await memory_save("_current_goal", server._current_goal, namespace="_system")
                
                return {
                    "success": True,
                    "goal": goal,
                    "subtasks_count": len(subtasks or [])
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
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
            try:
                if not server._current_goal:
                    result = await memory_recall("_current_goal", namespace="_system")
                    if result.get("found"):
                        server._current_goal = result["value"]
                    else:
                        return {"success": False, "error": "No goal set. Use goal_set first."}
                
                if completed_subtask and completed_subtask in server._current_goal["subtasks"]:
                    if completed_subtask not in server._current_goal["completed_subtasks"]:
                        server._current_goal["completed_subtasks"].append(completed_subtask)
                
                if progress_note:
                    if "notes" not in server._current_goal:
                        server._current_goal["notes"] = []
                    server._current_goal["notes"].append({
                        "note": progress_note,
                        "timestamp": datetime.now().isoformat()
                    })
                
                total = len(server._current_goal["subtasks"])
                completed = len(server._current_goal["completed_subtasks"])
                progress = (completed / total * 100) if total > 0 else 0
                
                await memory_save("_current_goal", server._current_goal, namespace="_system")
                
                return {
                    "success": True,
                    "goal": server._current_goal["goal"],
                    "progress_percent": round(progress, 1),
                    "completed": completed,
                    "total": total,
                    "remaining_subtasks": [
                        s for s in server._current_goal["subtasks"]
                        if s not in server._current_goal["completed_subtasks"]
                    ]
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
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
            try:
                if not server._current_goal:
                    return {"success": False, "error": "No current goal"}
                
                server._current_goal["status"] = "completed"
                server._current_goal["completed_at"] = datetime.now().isoformat()
                server._current_goal["summary"] = summary
                
                await memory_save(
                    f"goal_{int(time.time())}",
                    server._current_goal,
                    namespace="_goal_history"
                )
                
                result = {
                    "success": True,
                    "goal": server._current_goal["goal"],
                    "summary": summary
                }
                
                server._current_goal = None
                await memory_delete("_current_goal", namespace="_system")
                
                return result
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def session_state() -> Dict[str, Any]:
            """
            Get current session state overview.
            
            Returns a summary of the current session including goal,
            recent actions, and statistics.
            
            Returns:
                Dictionary with session overview
            """
            try:
                current_goal = None
                if server._current_goal:
                    total = len(server._current_goal.get("subtasks", []))
                    completed = len(server._current_goal.get("completed_subtasks", []))
                    current_goal = {
                        "goal": server._current_goal["goal"],
                        "progress": f"{completed}/{total}" if total > 0 else "N/A",
                        "status": server._current_goal.get("status", "in_progress")
                    }
                
                recent_actions = [h["action"] for h in server._task_history[-5:]] if server._task_history else []
                
                completed_count = len([h for h in server._task_history if h["status"] == "completed"])
                failed_count = len([h for h in server._task_history if h["status"] == "failed"])
                
                return {
                    "success": True,
                    "agent_id": server._agent_id,
                    "session_start": server._session_start,
                    "current_goal": current_goal,
                    "recent_actions": recent_actions,
                    "task_stats": {
                        "total": len(server._task_history),
                        "completed": completed_count,
                        "failed": failed_count
                    },
                    "memory_namespaces": list(server._session_memory.keys())
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        logger.info(f"[{self.name}] Registered 10 tools for agent: {server._agent_id}")
