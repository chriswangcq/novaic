"""
Memory & State Tools - 记忆与状态管理

提供持久化的工作记忆，让 AI 能够：
1. 保存和回忆工作上下文
2. 跟踪任务进度
3. 维护会话状态
"""

import json
import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime


class MemoryTools:
    """记忆与状态管理工具"""
    
    # 默认存储路径
    MEMORY_DIR = Path.home() / ".novaic" / "memory"
    
    def __init__(self):
        # 确保目录存在
        self.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._session_memory: Dict[str, Any] = {}
        self._task_history: List[Dict[str, Any]] = []
        self._current_goal: Optional[str] = None
        self._session_start = datetime.now().isoformat()
    
    def _get_memory_file(self, namespace: str = "default") -> Path:
        """获取记忆文件路径"""
        return self.MEMORY_DIR / f"{namespace}.json"
    
    def _load_persistent_memory(self, namespace: str = "default") -> Dict[str, Any]:
        """加载持久化记忆"""
        file_path = self._get_memory_file(namespace)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_persistent_memory(self, data: Dict[str, Any], namespace: str = "default"):
        """保存持久化记忆"""
        file_path = self._get_memory_file(namespace)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def memory_save(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        persistent: bool = True
    ) -> Dict[str, Any]:
        """
        保存记忆
        
        Args:
            key: 记忆键名
            value: 记忆内容（可以是任意 JSON 可序列化的值）
            namespace: 命名空间，用于分组记忆
            persistent: 是否持久化到磁盘
        
        Examples:
            - memory_save("current_task", "修复登录 bug")
            - memory_save("project_info", {"name": "myapp", "type": "python"})
            - memory_save("user_preference", {"theme": "dark"}, namespace="settings")
        """
        try:
            timestamp = datetime.now().isoformat()
            
            # 保存到会话内存
            if namespace not in self._session_memory:
                self._session_memory[namespace] = {}
            
            self._session_memory[namespace][key] = {
                "value": value,
                "updated_at": timestamp
            }
            
            # 持久化
            if persistent:
                memory = self._load_persistent_memory(namespace)
                memory[key] = {
                    "value": value,
                    "updated_at": timestamp
                }
                self._save_persistent_memory(memory, namespace)
            
            return {
                "success": True,
                "key": key,
                "namespace": namespace,
                "persistent": persistent,
                "message": f"已保存记忆: {key}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def memory_recall(
        self,
        key: Optional[str] = None,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        回忆记忆
        
        Args:
            key: 记忆键名，如果为空则返回该命名空间的所有记忆
            namespace: 命名空间
        
        Examples:
            - memory_recall("current_task")  # 获取特定记忆
            - memory_recall()  # 获取所有记忆
            - memory_recall(namespace="settings")  # 获取特定命名空间的所有记忆
        """
        try:
            # 优先从会话内存读取，然后从持久化存储读取
            session_data = self._session_memory.get(namespace, {})
            persistent_data = self._load_persistent_memory(namespace)
            
            # 合并，会话内存优先
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
                        "found": False,
                        "message": f"未找到记忆: {key}"
                    }
            else:
                # 返回所有记忆
                result = {}
                for k, v in merged.items():
                    result[k] = v["value"]
                return {
                    "success": True,
                    "namespace": namespace,
                    "memories": result,
                    "count": len(result)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def memory_delete(
        self,
        key: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        删除记忆
        
        Args:
            key: 要删除的记忆键名
            namespace: 命名空间
        """
        try:
            deleted = False
            
            # 从会话内存删除
            if namespace in self._session_memory and key in self._session_memory[namespace]:
                del self._session_memory[namespace][key]
                deleted = True
            
            # 从持久化存储删除
            memory = self._load_persistent_memory(namespace)
            if key in memory:
                del memory[key]
                self._save_persistent_memory(memory, namespace)
                deleted = True
            
            return {
                "success": True,
                "key": key,
                "deleted": deleted,
                "message": f"已删除记忆: {key}" if deleted else f"记忆不存在: {key}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def memory_list_namespaces(self) -> Dict[str, Any]:
        """列出所有记忆命名空间"""
        try:
            namespaces = set()
            
            # 会话内存的命名空间
            namespaces.update(self._session_memory.keys())
            
            # 持久化存储的命名空间
            if self.MEMORY_DIR.exists():
                for f in self.MEMORY_DIR.glob("*.json"):
                    namespaces.add(f.stem)
            
            return {
                "success": True,
                "namespaces": list(namespaces)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def task_log(
        self,
        action: str,
        details: Optional[str] = None,
        status: str = "completed"
    ) -> Dict[str, Any]:
        """
        记录任务/操作历史
        
        Args:
            action: 执行的操作描述
            details: 详细信息
            status: 状态 (completed, failed, in_progress)
        
        Examples:
            - task_log("打开 VSCode")
            - task_log("编辑 main.py", details="修改了第 42 行")
            - task_log("运行测试", status="failed", details="3 个测试失败")
        """
        try:
            entry = {
                "action": action,
                "details": details,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            self._task_history.append(entry)
            
            # 只保留最近 100 条
            if len(self._task_history) > 100:
                self._task_history = self._task_history[-100:]
            
            return {
                "success": True,
                "logged": entry,
                "history_count": len(self._task_history)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def task_history(
        self,
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取任务历史
        
        Args:
            limit: 返回的最大条数
            status_filter: 按状态过滤 (completed, failed, in_progress)
        """
        try:
            history = self._task_history
            
            if status_filter:
                history = [h for h in history if h["status"] == status_filter]
            
            # 返回最近的 N 条
            recent = history[-limit:] if limit else history
            
            return {
                "success": True,
                "history": recent,
                "total_count": len(self._task_history),
                "filtered_count": len(history)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def goal_set(self, goal: str, subtasks: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        设置当前目标
        
        Args:
            goal: 目标描述
            subtasks: 子任务列表
        
        Examples:
            - goal_set("修复登录 bug")
            - goal_set("重构用户模块", subtasks=["分析现有代码", "设计新架构", "实现", "测试"])
        """
        try:
            self._current_goal = {
                "goal": goal,
                "subtasks": subtasks or [],
                "completed_subtasks": [],
                "started_at": datetime.now().isoformat(),
                "status": "in_progress"
            }
            
            # 持久化
            await self.memory_save("_current_goal", self._current_goal, namespace="_system")
            
            return {
                "success": True,
                "goal": goal,
                "subtasks_count": len(subtasks or []),
                "message": f"已设置目标: {goal}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def goal_progress(
        self,
        completed_subtask: Optional[str] = None,
        progress_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新目标进度
        
        Args:
            completed_subtask: 完成的子任务
            progress_note: 进度备注
        """
        try:
            if not self._current_goal:
                # 尝试从持久化存储恢复
                result = await self.memory_recall("_current_goal", namespace="_system")
                if result.get("found"):
                    self._current_goal = result["value"]
                else:
                    return {"success": False, "error": "没有设置当前目标，请先调用 goal_set"}
            
            if completed_subtask and completed_subtask in self._current_goal["subtasks"]:
                if completed_subtask not in self._current_goal["completed_subtasks"]:
                    self._current_goal["completed_subtasks"].append(completed_subtask)
            
            if progress_note:
                if "notes" not in self._current_goal:
                    self._current_goal["notes"] = []
                self._current_goal["notes"].append({
                    "note": progress_note,
                    "timestamp": datetime.now().isoformat()
                })
            
            # 计算进度
            total = len(self._current_goal["subtasks"])
            completed = len(self._current_goal["completed_subtasks"])
            progress = (completed / total * 100) if total > 0 else 0
            
            # 持久化
            await self.memory_save("_current_goal", self._current_goal, namespace="_system")
            
            return {
                "success": True,
                "goal": self._current_goal["goal"],
                "progress_percent": round(progress, 1),
                "completed": completed,
                "total": total,
                "remaining_subtasks": [
                    s for s in self._current_goal["subtasks"] 
                    if s not in self._current_goal["completed_subtasks"]
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def goal_complete(self, summary: Optional[str] = None) -> Dict[str, Any]:
        """
        完成当前目标
        
        Args:
            summary: 完成总结
        """
        try:
            if not self._current_goal:
                return {"success": False, "error": "没有当前目标"}
            
            self._current_goal["status"] = "completed"
            self._current_goal["completed_at"] = datetime.now().isoformat()
            self._current_goal["summary"] = summary
            
            # 保存到历史
            await self.memory_save(
                f"goal_{int(time.time())}",
                self._current_goal,
                namespace="_goal_history"
            )
            
            result = {
                "success": True,
                "goal": self._current_goal["goal"],
                "message": "目标已完成！",
                "summary": summary
            }
            
            # 清除当前目标
            self._current_goal = None
            await self.memory_delete("_current_goal", namespace="_system")
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def session_state(self) -> Dict[str, Any]:
        """
        获取当前会话状态概览
        
        返回会话开始时间、任务历史摘要、当前目标等
        """
        try:
            # 获取当前目标
            current_goal = None
            if self._current_goal:
                total = len(self._current_goal.get("subtasks", []))
                completed = len(self._current_goal.get("completed_subtasks", []))
                current_goal = {
                    "goal": self._current_goal["goal"],
                    "progress": f"{completed}/{total}" if total > 0 else "N/A",
                    "status": self._current_goal.get("status", "in_progress")
                }
            
            # 最近操作
            recent_actions = [
                h["action"] for h in self._task_history[-5:]
            ] if self._task_history else []
            
            # 统计
            completed_count = len([h for h in self._task_history if h["status"] == "completed"])
            failed_count = len([h for h in self._task_history if h["status"] == "failed"])
            
            return {
                "success": True,
                "session_start": self._session_start,
                "current_goal": current_goal,
                "recent_actions": recent_actions,
                "task_stats": {
                    "total": len(self._task_history),
                    "completed": completed_count,
                    "failed": failed_count
                },
                "memory_namespaces": list(self._session_memory.keys())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 单例实例
_memory_tools = None

def get_memory_tools() -> MemoryTools:
    """获取 MemoryTools 单例"""
    global _memory_tools
    if _memory_tools is None:
        _memory_tools = MemoryTools()
    return _memory_tools
