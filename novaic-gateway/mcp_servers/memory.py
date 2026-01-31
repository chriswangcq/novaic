"""
Memory MCP Server - 持久化存储和状态管理

提供键值存储、任务追踪、目标管理等功能。
每个 Agent 有独立的内存空间，通过 agent_id 隔离。
使用 SQLite 数据库进行持久化存储。
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import BaseMCPServer
from db.database import get_database
from db.repositories.memory import MemoryRepository

logger = logging.getLogger(__name__)


class MemoryMCPServer(BaseMCPServer):
    """
    Memory MCP Server (Database-backed)。
    
    每个 Agent 的数据存储在数据库中，通过 agent_id 隔离。
    
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
    
    def __init__(self, agent_id: Optional[str] = None, agent_index: int = 0):
        """
        初始化 Memory Server。
        
        Args:
            agent_id: Agent ID，用于隔离内存空间 (必填)
            agent_index: Agent index，用于端口分配
        """
        if not agent_id:
            raise ValueError("[MemoryMCPServer] agent_id is required")
        self._agent_id = agent_id
        
        # In-memory cache for current session (not persisted separately)
        self._current_goal: Optional[Dict[str, Any]] = None
        self._session_start = datetime.now().isoformat()
        
        super().__init__(agent_id=agent_id, agent_index=agent_index)
        
        logger.info(f"[MemoryMCPServer] Initialized for agent: {self._agent_id}")
    
    def _get_repo(self) -> MemoryRepository:
        """Get memory repository instance."""
        db = get_database()
        return MemoryRepository(db)
    
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
                persistent: Whether to persist (default: True, always persisted to DB)
            
            Returns:
                Dictionary with success status
            
            Examples:
                memory_save("current_task", "Fix login bug")
                memory_save("project", {"name": "myapp", "type": "python"})
                memory_save("theme", "dark", namespace="settings")
            """
            try:
                repo = server._get_repo()
                result = await repo.save(server._agent_id, key, value, namespace or "default")
                result["persistent"] = True  # Always persistent with DB
                return result
            except Exception as e:
                logger.error(f"[Memory] save error: {e}")
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
                repo = server._get_repo()
                return await repo.recall(server._agent_id, key, namespace or "default")
            except Exception as e:
                logger.error(f"[Memory] recall error: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def memory_delete(
            key: str,
            namespace: Optional[str] = "default"
        ) -> Dict[str, Any]:
            """
            Delete a memory value.
            
            Remove a stored value from persistent storage.
            
            Args:
                key: Memory key to delete
                namespace: Namespace (default: "default")
            
            Returns:
                Dictionary with deletion status
            """
            try:
                repo = server._get_repo()
                return await repo.delete(server._agent_id, key, namespace or "default")
            except Exception as e:
                logger.error(f"[Memory] delete error: {e}")
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
                repo = server._get_repo()
                namespaces = await repo.list_namespaces(server._agent_id)
                return {
                    "success": True,
                    "namespaces": sorted(namespaces)
                }
            except Exception as e:
                logger.error(f"[Memory] list_namespaces error: {e}")
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
                repo = server._get_repo()
                result = await repo.log_task(
                    server._agent_id,
                    action,
                    details,
                    status or "completed"
                )
                
                # Cleanup old entries if too many
                if result.get("history_count", 0) > 100:
                    await repo.cleanup_old_tasks(server._agent_id, 100)
                
                return result
            except Exception as e:
                logger.error(f"[Memory] task_log error: {e}")
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
                repo = server._get_repo()
                return await repo.get_task_history(
                    server._agent_id,
                    limit or 20,
                    status_filter
                )
            except Exception as e:
                logger.error(f"[Memory] task_history error: {e}")
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
                
                # Persist to DB
                await memory_save("_current_goal", server._current_goal, namespace="_system")
                
                return {
                    "success": True,
                    "goal": goal,
                    "subtasks_count": len(subtasks or [])
                }
            except Exception as e:
                logger.error(f"[Memory] goal_set error: {e}")
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
                # Load from DB if not in memory
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
                
                # Persist updated goal
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
                logger.error(f"[Memory] goal_progress error: {e}")
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
                    result = await memory_recall("_current_goal", namespace="_system")
                    if result.get("found"):
                        server._current_goal = result["value"]
                    else:
                        return {"success": False, "error": "No current goal"}
                
                server._current_goal["status"] = "completed"
                server._current_goal["completed_at"] = datetime.now().isoformat()
                server._current_goal["summary"] = summary
                
                # Archive to goal history
                import time
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
                
                # Clear current goal
                server._current_goal = None
                await memory_delete("_current_goal", namespace="_system")
                
                return result
            except Exception as e:
                logger.error(f"[Memory] goal_complete error: {e}")
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
                repo = server._get_repo()
                
                # Get current goal
                current_goal = None
                if server._current_goal:
                    total = len(server._current_goal.get("subtasks", []))
                    completed = len(server._current_goal.get("completed_subtasks", []))
                    current_goal = {
                        "goal": server._current_goal["goal"],
                        "progress": f"{completed}/{total}" if total > 0 else "N/A",
                        "status": server._current_goal.get("status", "in_progress")
                    }
                else:
                    # Try loading from DB
                    result = await memory_recall("_current_goal", namespace="_system")
                    if result.get("found"):
                        g = result["value"]
                        total = len(g.get("subtasks", []))
                        completed = len(g.get("completed_subtasks", []))
                        current_goal = {
                            "goal": g["goal"],
                            "progress": f"{completed}/{total}" if total > 0 else "N/A",
                            "status": g.get("status", "in_progress")
                        }
                
                # Get task history stats
                history_result = await repo.get_task_history(server._agent_id, limit=100)
                history = history_result.get("history", [])
                
                recent_actions = [h["action"] for h in history[-5:]] if history else []
                completed_count = len([h for h in history if h["status"] == "completed"])
                failed_count = len([h for h in history if h["status"] == "failed"])
                
                # Get namespaces
                namespaces = await repo.list_namespaces(server._agent_id)
                
                return {
                    "success": True,
                    "agent_id": server._agent_id,
                    "session_start": server._session_start,
                    "current_goal": current_goal,
                    "recent_actions": recent_actions,
                    "task_stats": {
                        "total": history_result.get("total_count", 0),
                        "completed": completed_count,
                        "failed": failed_count
                    },
                    "memory_namespaces": namespaces
                }
            except Exception as e:
                logger.error(f"[Memory] session_state error: {e}")
                return {"success": False, "error": str(e)}
        
        logger.info(f"[{self.name}] Registered 10 tools for agent: {server._agent_id}")
