"""
TaskManager - Unified Task Management System

Manages async tasks of various types:
- agent: v12: Use Master.create_sub_runtime() instead
- shell: Shell command execution
- browser: Browser automation (future)
- custom: Custom task types

All tasks are persisted to SQLite for recovery and querying.
"""

import asyncio
import time
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field

import aiofiles

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Type of task."""
    AGENT = "agent"
    SHELL = "shell"
    BROWSER = "browser"
    TOOL = "tool"  # Generic MCP tool execution
    SYNC_OUTPUT = "sync_output"  # Truncated output from sync tool call
    CUSTOM = "custom"


@dataclass
class TaskConfig:
    """Configuration for a task."""
    # Agent task config
    prompt: Optional[str] = None
    model: Optional[str] = None
    max_iterations: int = 20
    tools_allowlist: Optional[List[str]] = None
    tools_denylist: Optional[List[str]] = None
    context: Optional[str] = None
    
    # Shell task config
    command: Optional[str] = None
    working_dir: Optional[str] = None
    
    # Browser task config
    url: Optional[str] = None
    actions: Optional[List[Dict[str, Any]]] = None
    
    # Tool task config (generic MCP tool execution)
    tool: Optional[str] = None  # Name of the MCP tool to execute
    args: Optional[Dict[str, Any]] = None  # Arguments for the tool
    registry: Optional[str] = None  # Registry source ("gateway", "vmuse", etc.)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding None values)."""
        return {k: v for k, v in {
            "prompt": self.prompt,
            "model": self.model,
            "max_iterations": self.max_iterations,
            "tools_allowlist": self.tools_allowlist,
            "tools_denylist": self.tools_denylist,
            "context": self.context,
            "command": self.command,
            "working_dir": self.working_dir,
            "url": self.url,
            "actions": self.actions,
            "tool": self.tool,
            "args": self.args,
            "registry": self.registry,
        }.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConfig":
        """Create from dictionary."""
        return cls(
            prompt=data.get("prompt"),
            model=data.get("model"),
            max_iterations=data.get("max_iterations", 20),
            tools_allowlist=data.get("tools_allowlist"),
            tools_denylist=data.get("tools_denylist"),
            context=data.get("context"),
            command=data.get("command"),
            working_dir=data.get("working_dir"),
            url=data.get("url"),
            actions=data.get("actions"),
            tool=data.get("tool"),
            args=data.get("args"),
            registry=data.get("registry"),
        )


@dataclass
class Task:
    """A task instance."""
    id: str
    type: TaskType
    label: Optional[str]
    config: TaskConfig
    status: TaskStatus = TaskStatus.PENDING
    
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    result: Optional[Any] = None
    result_summary: Optional[str] = None
    error: Optional[str] = None
    
    # Large output storage
    output_file: Optional[str] = None  # Path to full output file
    ttl_hours: int = 168  # Default: 7 days
    expires_at: Optional[datetime] = None
    
    parent_session_key: Optional[str] = None
    agent_id: str = "default"
    notify_on: List[str] = field(default_factory=lambda: ["complete", "error"])
    
    # Runtime only (not persisted)
    _task: Optional[asyncio.Task] = field(default=None, repr=False)
    _process: Optional[asyncio.subprocess.Process] = field(default=None, repr=False)
    
    def to_dict(self, include_result: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "task_id": self.id,
            "type": self.type.value,
            "label": self.label,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parent_session_key": self.parent_session_key,
            "agent_id": self.agent_id,
            "error": self.error,
        }
        
        if self.started_at and not self.completed_at:
            data["running_seconds"] = (datetime.now() - self.started_at).total_seconds()
        elif self.started_at and self.completed_at:
            data["duration_seconds"] = (self.completed_at - self.started_at).total_seconds()
        
        # Include output file info if present
        if self.output_file:
            data["has_output_file"] = True
        
        # Include expiration info
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        
        if include_result:
            data["result"] = self.result
            data["result_summary"] = self.result_summary
            data["config"] = self.config.to_dict()
        
        return data


class TaskManager:
    """
    Unified task manager for all async task types.
    
    Responsibilities:
    - Create and track tasks of various types
    - Persist task state to SQLite
    - Execute tasks (shell directly, agent via Master/inbox)
    - Generate result summaries
    
    v12: SubAgentManager removed - agent tasks use Master architecture.
    """
    
    def __init__(
        self,
        db=None,
        subagent_manager=None,  # v12: Deprecated, kept for signature compatibility
        llm_factory: Optional[Callable[[str, str, str], Any]] = None,
        tool_registry=None,
    ):
        """
        Initialize the task manager.
        
        Args:
            db: Database instance for persistence
            subagent_manager: Unused, kept for compatibility
            llm_factory: Factory to create LLM clients for summary generation
            tool_registry: ToolRegistry for executing tool tasks
        """
        if db is None:
            from gateway.db.access import get_db
            db = get_db()
        self.db = db
        self.subagent_manager = None  # Unused
        self.llm_factory = llm_factory
        self.tool_registry = tool_registry
        
        # In-memory task cache (for running tasks)
        self._tasks: Dict[str, Task] = {}
        
        # Statistics
        self._stats = {
            "spawned": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
    
    def spawn(
        self,
        task_type: str,
        config: Dict[str, Any],
        label: Optional[str] = None,
        timeout_seconds: int = 0,
        notify_on: Optional[List[str]] = None,
        parent_session_key: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create and start a new task.
        
        Args:
            task_type: Type of task (agent, shell, browser, custom)
            config: Task configuration dictionary
            label: Human-readable label
            timeout_seconds: Timeout (0 = no timeout)
            notify_on: Events to notify on (default: ["complete", "error"])
            parent_session_key: Session that created this task
            agent_id: Agent that owns this task (required)
        
        Returns:
            Dictionary with task_id and status
        
        Raises:
            ValueError: If agent_id is not provided
        """
        if not agent_id:
            raise ValueError("agent_id is required for spawn()")
        # Generate task ID
        task_id = str(uuid.uuid4())[:8]
        
        # Parse task type
        try:
            task_type_enum = TaskType(task_type)
        except ValueError:
            return {"success": False, "error": f"Invalid task type: {task_type}"}
        
        # Create task
        task = Task(
            id=task_id,
            type=task_type_enum,
            label=label or f"{task_type} task",
            config=TaskConfig.from_dict(config),
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            parent_session_key=parent_session_key,
            agent_id=agent_id,
            notify_on=notify_on or ["complete", "error"],
        )
        
        # Store in memory
        self._tasks[task_id] = task
        self._stats["spawned"] += 1
        
        # Persist to database
        self._save_task(task)
        
        logger.info(f"[TaskManager] Spawned task {task_id} ({task_type}): {label}")
        
        # Start execution based on type
        if task_type_enum == TaskType.AGENT:
            task._task = asyncio.create_task(
                self._execute_agent_task(task, timeout_seconds)
            )
        elif task_type_enum == TaskType.SHELL:
            task._task = asyncio.create_task(
                self._execute_shell_task(task, timeout_seconds)
            )
        elif task_type_enum == TaskType.TOOL:
            task._task = asyncio.create_task(
                self._execute_tool_task(task, timeout_seconds)
            )
        else:
            # Mark as failed for unsupported types
            task.status = TaskStatus.FAILED
            task.error = f"Task type '{task_type}' not yet implemented"
            self._save_task(task)
            return {
                "success": False,
                "task_id": task_id,
                "status": task.status.value,
                "error": task.error,
            }
        
        return {
            "success": True,
            "task_id": task_id,
            "status": task.status.value,
        }
    
    def create_completed(
        self,
        tool_name: str,
        truncated_result: str,
        full_output: str,
        ttl_hours: int = 24,
        agent_id: Optional[str] = None,
    ) -> str:
        """
        Create an immediately completed task for storing truncated output.
        
        This is used by _auto_truncate_result to store long outputs as
        sync_output tasks that can be queried later via task_query.
        
        Args:
            tool_name: Name of the tool that produced this output
            truncated_result: The truncated version of the output
            full_output: The complete output to store
            ttl_hours: Time-to-live in hours (default: 24 for sync outputs)
            agent_id: Agent that owns this task (required)
        
        Returns:
            task_id: The unique ID for querying this output
        
        Raises:
            ValueError: If agent_id is not provided
        """
        if not agent_id:
            raise ValueError("agent_id is required for create_completed()")
        # Generate task ID
        task_id = f"so_{str(uuid.uuid4())[:8]}"  # so_ prefix for sync_output
        
        now = datetime.now()
        expires_at = now + timedelta(hours=ttl_hours)
        
        # Ensure output directory exists
        data_dir = os.environ.get("NOVAIC_DATA_DIR", os.path.expanduser("~/.novaic"))
        output_dir = Path(data_dir) / "task_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write full output to file
        output_file = output_dir / f"{task_id}.txt"
        with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_output)
        
        # Create task
        task = Task(
            id=task_id,
            type=TaskType.SYNC_OUTPUT,
            label=f"Output: {tool_name}",
            config=TaskConfig(tool=tool_name),
            status=TaskStatus.COMPLETED,
            created_at=now,
            started_at=now,
            completed_at=now,
            result=truncated_result,
            output_file=str(output_file),
            ttl_hours=ttl_hours,
            expires_at=expires_at,
            agent_id=agent_id,
            notify_on=[],  # No notifications for sync outputs
        )
        
        # Store in memory (briefly)
        self._tasks[task_id] = task
        
        # Persist to database
        self._save_task(task)
        
        logger.info(f"[TaskManager] Created sync_output task {task_id} for {tool_name}")
        
        return task_id
    
    def get_status(
        self,
        task_id: Optional[str] = None,
        include_outputs: bool = False,
        output_limit: int = 50,
        status_filter: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        # Pagination for full output retrieval
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        tail_lines: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get task status or list tasks.
        
        Args:
            task_id: Specific task ID (if None, list all tasks)
            include_outputs: Whether to include intermediate outputs
            output_limit: Maximum number of outputs to return
            status_filter: Filter by status (for listing)
            agent_id: Filter by agent ID (for listing)
            start_line: Starting line number for paginated output (1-based)
            end_line: Ending line number for paginated output (inclusive)
            tail_lines: Get last N lines of output
        
        Returns:
            Task status or list of tasks
        """
        if task_id:
            # Get specific task
            task = self._tasks.get(task_id)
            if not task:
                # Try loading from database
                task = self._load_task(task_id)
            
            if not task:
                return {"success": False, "error": f"Task '{task_id}' not found"}
            
            result = task.to_dict(include_result=True)
            
            # Handle paginated output retrieval from output_file
            if task.output_file and (start_line or end_line or tail_lines):
                output_content = self._read_output_file(
                    task.output_file,
                    start_line,
                    end_line,
                    tail_lines,
                )
                if output_content:
                    result["full_output"] = output_content["content"]
                    result["output_range"] = output_content["range"]
                    result["output_total_lines"] = output_content["total_lines"]
                    result["output_has_more"] = output_content["has_more"]
            
            if include_outputs:
                outputs = self._get_task_outputs(task_id, output_limit)
                result["outputs"] = outputs
                result["output_count"] = len(outputs)
                result["truncated"] = len(outputs) >= output_limit
            
            return {"success": True, **result}
        else:
            # List tasks
            tasks = self._list_tasks(status_filter, agent_id)
            return {
                "success": True,
                "tasks": tasks,
                "total": len(tasks),
            }
    
    def get_result(
        self,
        task_id: str,
        format: str = "summary",
    ) -> Dict[str, Any]:
        """
        Get the result of a completed task.
        
        Args:
            task_id: Task ID
            format: "summary" or "full"
        
        Returns:
            Task result
        """
        task = self._tasks.get(task_id)
        if not task:
            task = self._load_task(task_id)
        
        if not task:
            return {"success": False, "error": f"Task '{task_id}' not found"}
        
        if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            return {
                "success": False,
                "task_id": task_id,
                "status": task.status.value,
                "error": "Task has not completed yet",
            }
        
        result = {
            "success": True,
            "task_id": task_id,
            "status": task.status.value,
            "summary": task.result_summary,
        }
        
        if format == "full":
            result["result"] = task.result
            result["error"] = task.error
            result["config"] = task.config.to_dict()
        
        return result
    
    def cancel(
        self,
        task_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel a running task.
        
        Args:
            task_id: Task ID
            reason: Cancellation reason
        
        Returns:
            Result dictionary
        """
        task = self._tasks.get(task_id)
        if not task:
            return {"success": False, "error": f"Task '{task_id}' not found"}
        
        if task.status != TaskStatus.RUNNING:
            return {
                "success": False,
                "error": f"Task is not running (status: {task.status.value})",
            }
        
        # Cancel the async task
        if task._task:
            task._task.cancel()
            try:
                task._task
            except asyncio.CancelledError:
                pass
        
        # Kill process if shell task
        if task._process:
            try:
                task._process.terminate()
                time.sleep(0.5)
                if task._process.returncode is None:
                    task._process.kill()
            except Exception:
                pass
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        task.error = reason or "Cancelled by user"
        
        self._save_task(task)
        self._stats["cancelled"] += 1
        
        logger.info(f"[TaskManager] Cancelled task {task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "status": task.status.value,
        }
    
    # ==================== Internal Methods ====================
    
    def _execute_agent_task(self, task: Task, timeout_seconds: int):
        """
        Execute an agent task.
        
        Agent tasks should be submitted via Master.create_sub_runtime() instead.
        """
        task.status = TaskStatus.FAILED
        task.started_at = datetime.now()
        task.completed_at = datetime.now()
        task.error = "Agent tasks should use Master.create_sub_runtime() or POST /api/inbox"
        task.result_summary = "Use Master architecture"
        self._stats["failed"] += 1
        self._save_task(task)
        
        logger.warning(f"[TaskManager] Agent task {task.id} rejected - use Master architecture")
        self._notify_completion(task)
    
    def _execute_shell_task(self, task: Task, timeout_seconds: int):
        """Execute a shell task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._save_task(task)
        
        command = task.config.command
        if not command:
            task.status = TaskStatus.FAILED
            task.error = "No command specified"
            task.completed_at = datetime.now()
            self._save_task(task)
            return
        
        try:
            import os
            
            cwd = task.config.working_dir or os.getcwd()
            
            # Start process
            process = asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            task._process = process
            
            # Collect output with streaming to task_outputs
            stdout_lines = []
            stderr_lines = []
            
            def read_stream(stream, lines_list, output_type):
                while True:
                    line = stream.readline()
                    if not line:
                        break
                    decoded = line.decode('utf-8', errors='replace').rstrip('\n')
                    lines_list.append(decoded)
                    # Save to outputs
                    self._add_task_output(task.id, output_type, decoded)
            
            # Read stdout and stderr concurrently
            stdout_task = asyncio.create_task(
                read_stream(process.stdout, stdout_lines, "stdout")
            )
            stderr_task = asyncio.create_task(
                read_stream(process.stderr, stderr_lines, "stderr")
            )
            
            # Wait for process with optional timeout
            if timeout_seconds > 0:
                try:
                    asyncio.wait_for(process.wait(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    process.terminate()
                    time.sleep(0.5)
                    if process.returncode is None:
                        process.kill()
                    task.status = TaskStatus.FAILED
                    task.error = f"Command timed out after {timeout_seconds}s"
                    self._stats["failed"] += 1
                    stdout_task.cancel()
                    stderr_task.cancel()
                    task.completed_at = datetime.now()
                    self._save_task(task)
                    self._notify_completion(task)
                    return
            else:
                process.wait()
            
            # Wait for stream readers
            asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            
            # Set result
            task.result = {
                "exit_code": process.returncode,
                "stdout": "\n".join(stdout_lines),
                "stderr": "\n".join(stderr_lines),
                "stdout_lines": len(stdout_lines),
                "stderr_lines": len(stderr_lines),
            }
            
            if process.returncode == 0:
                task.status = TaskStatus.COMPLETED
                self._stats["completed"] += 1
            else:
                task.status = TaskStatus.FAILED
                task.error = f"Command exited with code {process.returncode}"
                self._stats["failed"] += 1
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            self._stats["cancelled"] += 1
            raise
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._stats["failed"] += 1
            logger.error(f"[TaskManager] Shell task {task.id} failed: {e}")
        finally:
            task._process = None
            task.completed_at = datetime.now()
            
            # Generate summary
            if task.result:
                result_str = task.result if isinstance(task.result, str) else json.dumps(task.result)
                task.result_summary = self._generate_summary(result_str)
            elif task.error:
                task.result_summary = f"Failed: {task.error[:100]}"
            
            self._save_task(task)
            self._notify_completion(task)
    
    def _execute_tool_task(self, task: Task, timeout_seconds: int):
        """Execute a generic MCP tool task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._save_task(task)
        
        tool_name = task.config.tool
        tool_args = task.config.args or {}
        
        if not tool_name:
            task.status = TaskStatus.FAILED
            task.error = "No tool name specified"
            task.completed_at = datetime.now()
            self._save_task(task)
            return
        
        try:
            # Get the tool registry
            registry = self.tool_registry
            if not registry:
                # v2.8: Try to get from MCPManager's aggregate gateways
                try:
                    from mcp_gateway.manager import get_mcp_manager
                    mcp_mgr = get_mcp_manager()
                    if mcp_mgr and mcp_mgr._aggregate_gateways:
                        # Use the first available gateway's registry
                        first_gateway = next(iter(mcp_mgr._aggregate_gateways.values()))
                        registry = first_gateway.registry
                except Exception:
                    pass
            
            if not registry:
                raise RuntimeError("ToolRegistry not available")
            
            # Add intermediate output
            self._add_task_output(task.id, "info", f"Executing tool: {tool_name}")
            
            # Execute the tool with optional timeout
            if timeout_seconds > 0:
                result = asyncio.wait_for(
                    registry.execute(tool_name, tool_args),
                    timeout=timeout_seconds
                )
            else:
                result = registry.execute(tool_name, tool_args)
            
            # Store result
            task.result = result
            
            # Check if the result indicates success
            if isinstance(result, dict):
                is_success = result.get("success", True)
                if not is_success and "error" in result:
                    task.status = TaskStatus.FAILED
                    task.error = result.get("error", "Tool execution failed")
                    self._stats["failed"] += 1
                else:
                    task.status = TaskStatus.COMPLETED
                    self._stats["completed"] += 1
            else:
                task.status = TaskStatus.COMPLETED
                self._stats["completed"] += 1
            
            # Add result to outputs
            result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
            self._add_task_output(task.id, "result", result_str[:2000])
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = f"Tool execution timed out after {timeout_seconds}s"
            self._stats["failed"] += 1
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            self._stats["cancelled"] += 1
            raise
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._stats["failed"] += 1
            logger.error(f"[TaskManager] Tool task {task.id} failed: {e}")
        finally:
            task.completed_at = datetime.now()
            
            # Generate summary
            if task.result and task.status == TaskStatus.COMPLETED:
                result_str = json.dumps(task.result) if isinstance(task.result, (dict, list)) else str(task.result)
                task.result_summary = self._generate_summary(result_str)
            elif task.error:
                task.result_summary = f"Failed: {task.error[:100]}"
            
            self._save_task(task)
            self._notify_completion(task)
    
    def _generate_summary(self, result: Any) -> str:
        """Generate a summary of the task result using LLM."""
        if not result:
            return "No result"
        
        # Truncate if too long
        result_str = str(result)[:3000] if isinstance(result, str) else json.dumps(result)[:3000]
        
        # Try to use LLM for summary
        if self.llm_factory:
            try:
                # Get a lightweight LLM client
                from config import get_config_manager
                config = get_config_manager().load()
                
                # Find an API key
                api_key = None
                api_base = None
                provider = "openai"
                
                if config.api_keys:
                    entry = next((e for e in config.api_keys if e.api_key), None)
                    if entry:
                        api_key = entry.api_key
                        api_base = entry.get_effective_base_url()
                        provider = entry.provider.value
                
                if api_key:
                    client = self.llm_factory(provider, api_base, api_key)
                    
                    # Use a light model for summaries
                    summary_model = "gpt-4o-mini" if provider == "openai" else config.default_model
                    
                    messages = [
                        {"role": "user", "content": f"用1-2句话简洁概括以下任务结果，重点说明完成了什么：\n\n{result_str}"}
                    ]
                    
                    response = client.chat(messages, model=summary_model)
                    return response.strip()[:500]
            except Exception as e:
                logger.warning(f"[TaskManager] Failed to generate LLM summary: {e}")
        
        # Fallback: simple truncation
        if len(result_str) > 200:
            return result_str[:200] + "..."
        return result_str
    
    def _notify_completion(self, task: Task):
        """Log task completion."""
        # Determine if notification is requested
        if task.status == TaskStatus.COMPLETED and "complete" in task.notify_on:
            logger.info(f"[TaskManager] Task {task.id} completed (type={task.type.value})")
        elif task.status == TaskStatus.FAILED and "error" in task.notify_on:
            logger.info(f"[TaskManager] Task {task.id} failed (type={task.type.value})")
    
    # ==================== Persistence Methods ====================
    
    def _save_task(self, task: Task):
        """Save task to database."""
        if not self.db:
            return
        
        try:
            with self.db.transaction(lock_type="agent", resource_id=task.agent_id):
                self.db.execute(
                    """INSERT INTO tasks 
                       (id, type, label, config, status, created_at, started_at, completed_at,
                        result, result_summary, error, output_file, ttl_hours, expires_at,
                        parent_session_key, agent_id, notify_on)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                           status = excluded.status,
                           started_at = excluded.started_at,
                           completed_at = excluded.completed_at,
                           result = excluded.result,
                           result_summary = excluded.result_summary,
                           error = excluded.error,
                           output_file = excluded.output_file,
                           expires_at = excluded.expires_at""",
                    (
                        task.id,
                        task.type.value,
                        task.label,
                        json.dumps(task.config.to_dict()),
                        task.status.value,
                        task.created_at.isoformat() if task.created_at else None,
                        task.started_at.isoformat() if task.started_at else None,
                        task.completed_at.isoformat() if task.completed_at else None,
                        json.dumps(task.result) if task.result else None,
                        task.result_summary,
                        task.error,
                        task.output_file,
                        task.ttl_hours,
                        task.expires_at.isoformat() if task.expires_at else None,
                        task.parent_session_key,
                        task.agent_id,
                        json.dumps(task.notify_on),
                    )
                )
        except Exception as e:
            logger.error(f"[TaskManager] Failed to save task {task.id}: {e}")
    
    def _load_task(self, task_id: str) -> Optional[Task]:
        """Load task from database."""
        if not self.db:
            return None
        
        try:
            row = self.db.fetchone(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            )
            
            if not row:
                return None
            
            return Task(
                id=row["id"],
                type=TaskType(row["type"]),
                label=row["label"],
                config=TaskConfig.from_dict(json.loads(row["config"]) if row["config"] else {}),
                status=TaskStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                result=json.loads(row["result"]) if row["result"] else None,
                result_summary=row["result_summary"],
                error=row["error"],
                output_file=row.get("output_file"),
                ttl_hours=row.get("ttl_hours", 168),
                expires_at=datetime.fromisoformat(row["expires_at"]) if row.get("expires_at") else None,
                parent_session_key=row["parent_session_key"],
                agent_id=row["agent_id"],
                notify_on=json.loads(row["notify_on"]) if row["notify_on"] else ["complete", "error"],
            )
        except Exception as e:
            logger.error(f"[TaskManager] Failed to load task {task_id}: {e}")
            return None
    
    def _list_tasks(
        self,
        status_filter: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List tasks from database."""
        tasks = []
        
        # First, add running tasks from memory
        for task in self._tasks.values():
            if status_filter and task.status.value not in status_filter:
                continue
            if agent_id and task.agent_id != agent_id:
                continue
            tasks.append(task.to_dict())
        
        # Then, query database for completed tasks
        if self.db:
            try:
                conditions = []
                params = []
                
                if status_filter:
                    placeholders = ",".join(["?"] * len(status_filter))
                    conditions.append(f"status IN ({placeholders})")
                    params.extend(status_filter)
                
                if agent_id:
                    conditions.append("agent_id = ?")
                    params.append(agent_id)
                
                where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
                
                rows = self.db.fetchall(
                    f"SELECT * FROM tasks {where} ORDER BY created_at DESC LIMIT 100",
                    tuple(params)
                )
                
                # Add tasks not already in memory
                memory_ids = {t["task_id"] for t in tasks}
                for row in rows:
                    if row["id"] not in memory_ids:
                        task = Task(
                            id=row["id"],
                            type=TaskType(row["type"]),
                            label=row["label"],
                            config=TaskConfig.from_dict(json.loads(row["config"]) if row["config"] else {}),
                            status=TaskStatus(row["status"]),
                            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
                            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                            result=json.loads(row["result"]) if row["result"] else None,
                            result_summary=row["result_summary"],
                            error=row["error"],
                            parent_session_key=row["parent_session_key"],
                            agent_id=row["agent_id"],
                        )
                        tasks.append(task.to_dict())
            except Exception as e:
                logger.error(f"[TaskManager] Failed to list tasks: {e}")
        
        return tasks
    
    def _add_task_output(self, task_id: str, output_type: str, content: str):
        """Add output to task_outputs table."""
        if not self.db:
            return
        
        # Get agent_id from memory cache or database
        agent_id = None
        if task_id in self._tasks:
            agent_id = self._tasks[task_id].agent_id
        else:
            # Query database for agent_id
            try:
                row = self.db.fetchone(
                    "SELECT agent_id FROM tasks WHERE id = ?",
                    (task_id,)
                )
                if row:
                    agent_id = row["agent_id"]
            except Exception:
                pass
        
        if not agent_id:
            # Fallback to default agent_id if not found
            agent_id = "default"
        
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    "INSERT INTO task_outputs (task_id, type, content) VALUES (?, ?, ?)",
                    (task_id, output_type, content)
                )
        except Exception as e:
            logger.warning(f"[TaskManager] Failed to add task output: {e}")
    
    def _get_task_outputs(self, task_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task outputs from database."""
        if not self.db:
            return []
        
        try:
            rows = self.db.fetchall(
                "SELECT ts, type, content FROM task_outputs WHERE task_id = ? ORDER BY ts DESC LIMIT ?",
                (task_id, limit)
            )
            return [{"ts": row["ts"], "type": row["type"], "content": row["content"]} for row in rows]
        except Exception as e:
            logger.error(f"[TaskManager] Failed to get task outputs: {e}")
            return []
    
    def _read_output_file(
        self,
        output_file: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        tail_lines: Optional[int] = None,
        max_lines: int = 100,
    ) -> Optional[Dict[str, Any]]:
        """
        Read output from file with pagination support.
        
        Args:
            output_file: Path to the output file
            start_line: Starting line number (1-based)
            end_line: Ending line number (inclusive)
            tail_lines: Get last N lines
            max_lines: Maximum lines to return
        
        Returns:
            Dictionary with content, range info, and more flag
        """
        if not output_file or not os.path.exists(output_file):
            return None
        
        try:
            with aiofiles.open(output_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            if tail_lines:
                # Get last N lines
                n = min(tail_lines, total_lines, max_lines)
                selected = all_lines[-n:]
                start_idx = total_lines - n
                end_idx = total_lines
            elif start_line:
                # Get from start_line to end_line
                start_idx = max(0, start_line - 1)
                if end_line:
                    end_idx = min(end_line, total_lines, start_idx + max_lines)
                else:
                    end_idx = min(start_idx + max_lines, total_lines)
                selected = all_lines[start_idx:end_idx]
            else:
                # Default: get first max_lines
                selected = all_lines[:max_lines]
                start_idx = 0
                end_idx = min(max_lines, total_lines)
            
            return {
                "content": ''.join(selected),
                "range": f"{start_idx + 1}-{end_idx}",
                "total_lines": total_lines,
                "lines_returned": len(selected),
                "has_more": end_idx < total_lines,
                "next_start": end_idx + 1 if end_idx < total_lines else None,
            }
        except Exception as e:
            logger.error(f"[TaskManager] Failed to read output file: {e}")
            return None
    
    # ==================== Stats and Cleanup ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        
        return {
            **self._stats,
            "in_memory": len(self._tasks),
            "running": running,
        }
    
    def cleanup_completed(self, max_age_hours: int = 24):
        """Clean up old completed tasks from memory."""
        cutoff = datetime.now()
        to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                if task.completed_at:
                    age_hours = (cutoff - task.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
        
        if to_remove:
            logger.info(f"[TaskManager] Cleaned up {len(to_remove)} old tasks from memory")
        
        return len(to_remove)
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired tasks from database and delete their output files.
        
        This should be called periodically (e.g., hourly) to remove old tasks.
        
        Returns:
            Number of tasks cleaned up
        """
        if not self.db:
            return 0
        
        now = datetime.now().isoformat()
        cleaned = 0
        
        try:
            # First, get expired tasks with output files
            rows = self.db.fetchall(
                "SELECT id, output_file FROM tasks WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,)
            )
            
            # Delete output files
            for row in rows:
                task_id = row["id"]
                output_file = row["output_file"]
                
                # Remove from memory if present
                if task_id in self._tasks:
                    del self._tasks[task_id]
                
                # Delete output file
                if output_file and os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                        logger.debug(f"[TaskManager] Deleted output file: {output_file}")
                    except Exception as e:
                        logger.warning(f"[TaskManager] Failed to delete output file {output_file}: {e}")
            
            # Delete from database
            with self.db.transaction(lock_type="global"):
                result = self.db.execute(
                    "DELETE FROM tasks WHERE expires_at IS NOT NULL AND expires_at < ?",
                    (now,)
                )
            
            # Get rowcount - handle different database backends
            if hasattr(result, 'rowcount'):
                cleaned = result.rowcount
            else:
                cleaned = len(rows)
            
            if cleaned > 0:
                logger.info(f"[TaskManager] Cleaned up {cleaned} expired tasks")
            
        except Exception as e:
            logger.error(f"[TaskManager] Failed to cleanup expired tasks: {e}")
        
        return cleaned


# Global instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> Optional[TaskManager]:
    """Get the global TaskManager instance."""
    return _task_manager


def set_task_manager(manager: TaskManager):
    """Set the global TaskManager instance."""
    global _task_manager
    _task_manager = manager
