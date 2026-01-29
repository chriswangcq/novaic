"""
Shell Tools - Execute commands and Python code
"""

import asyncio
import subprocess
import os
import uuid
import time
from typing import Dict, Any, Optional
from collections import deque

from ..config import settings


# Global task storage for background tasks
_background_tasks: Dict[str, Dict[str, Any]] = {}

# Max lines to keep in memory per task (for tail)
MAX_OUTPUT_LINES = 1000
# Default tail lines to return
DEFAULT_TAIL_LINES = 50
# TTL for completed tasks (seconds) - can still query within this time
TASK_TTL_SECONDS = 300  # 5 minutes


class ShellTools:
    """Shell execution tools"""
    
    # Default timeout before auto-backgrounding (seconds)
    AUTO_BACKGROUND_TIMEOUT = 3
    
    @staticmethod
    async def run_command(
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        visible: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a shell command. Always returns task_id + tail format.
        
        Args:
            command: Shell command to execute
            cwd: Working directory
            timeout: How long to WAIT (block) before returning, in seconds.
                     - None: wait 3s (default)
                     - timeout=10: wait up to 10s before returning
                     - timeout=60: wait up to 60s before returning
                     If task completes within timeout, returns status="completed"
                     If task still running after timeout, returns status="running"
                     Background task will continue running indefinitely (no kill)
            visible: If true, run in visible terminal (for GUI apps)
        
        Returns:
            Always returns { task_id, status, stdout_tail, stderr_tail, ... }
            Use query_task(task_id) to get more output or check status.
        """
        try:
            work_dir = cwd or settings.work_dir
            os.makedirs(work_dir, exist_ok=True)
            
            if visible:
                # Run in visible terminal using xterm
                result = await ShellTools._run_visible(command, work_dir, timeout or 60)
            else:
                # Run with unified task tracking (always return task_id + tail)
                result = await ShellTools._run_with_task_tracking(command, work_dir, timeout)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout_tail": "",
                "stderr_tail": "",
                "exit_code": -1
            }
    
    @staticmethod
    async def _run_with_task_tracking(
        command: str,
        cwd: str,
        timeout: Optional[int]
    ) -> Dict[str, Any]:
        """
        Run command with unified task tracking.
        Always returns task_id + tail, whether completed quickly or moved to background.
        
        Args:
            timeout: If provided, wait up to this many seconds for completion.
                     If None, use default AUTO_BACKGROUND_TIMEOUT (3s).
        """
        env = ShellTools._get_env_with_display()
        task_id = str(uuid.uuid4())[:8]
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )
        
        # Create task entry
        _background_tasks[task_id] = {
            "task_id": task_id,
            "command": command,
            "cwd": cwd,
            "status": "running",
            "started_at": time.time(),
            "process": process,
            "stdout_lines": deque(maxlen=MAX_OUTPUT_LINES),
            "stderr_lines": deque(maxlen=MAX_OUTPUT_LINES),
            "stdout_total": 0,
            "stderr_total": 0,
            "exit_code": None,
            "finished_at": None
        }
        
        # Use timeout parameter to control wait time
        # If timeout is provided by user, use it; otherwise use default 3s
        wait_timeout = timeout if timeout is not None else ShellTools.AUTO_BACKGROUND_TIMEOUT
        
        try:
            # Try to complete within wait_timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=wait_timeout
            )
            
            # Completed quickly - update task and return
            task = _background_tasks[task_id]
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # Store lines in deque
            for line in stdout_str.splitlines():
                task["stdout_lines"].append(line)
                task["stdout_total"] += 1
            for line in stderr_str.splitlines():
                task["stderr_lines"].append(line)
                task["stderr_total"] += 1
            
            task["status"] = "completed"
            task["exit_code"] = process.returncode
            task["finished_at"] = time.time()
            task["process"] = None
            
            # Return unified format
            return {
                "success": process.returncode == 0,
                "task_id": task_id,
                "status": "completed",
                "stdout_tail": ShellTools._tail_output(stdout_str, DEFAULT_TAIL_LINES),
                "stderr_tail": ShellTools._tail_output(stderr_str, DEFAULT_TAIL_LINES),
                "stdout_total_lines": task["stdout_total"],
                "stderr_total_lines": task["stderr_total"],
                "exit_code": process.returncode,
                "duration_seconds": round(task["finished_at"] - task["started_at"], 2)
            }
            
        except asyncio.TimeoutError:
            # Took too long, start background monitor
            # Pass None as timeout to let task run indefinitely in background
            asyncio.create_task(ShellTools._monitor_task_streaming(task_id, process, background_timeout=None))
            
            return {
                "success": True,
                "task_id": task_id,
                "status": "running",
                "stdout_tail": "",
                "stderr_tail": "",
                "stdout_total_lines": 0,
                "stderr_total_lines": 0,
                "message": f"Running in background (waited {wait_timeout}s). Use query_task('{task_id}') to check progress.",
            }
    
    @staticmethod
    def _tail_output(output: str, lines: int) -> str:
        """Get last N lines of output"""
        if not output:
            return ""
        output_lines = output.splitlines()
        if len(output_lines) <= lines:
            return output
        return '\n'.join(output_lines[-lines:])
    
    @staticmethod
    async def _read_stream(stream, lines_deque: deque, counter_key: str, task: dict):
        """Read stream line by line into deque"""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').rstrip('\n')
                lines_deque.append(decoded)
                task[counter_key] += 1
        except Exception:
            pass
    
    @staticmethod
    async def _monitor_task_streaming(task_id: str, process: asyncio.subprocess.Process, background_timeout: Optional[int]):
        """
        Monitor background task with streaming output.
        
        Args:
            background_timeout: Max time for background task to run (None = indefinite)
        """
        task = _background_tasks.get(task_id)
        if not task:
            return
        
        try:
            # Start reading stdout and stderr concurrently
            stdout_task = asyncio.create_task(
                ShellTools._read_stream(process.stdout, task["stdout_lines"], "stdout_total", task)
            )
            stderr_task = asyncio.create_task(
                ShellTools._read_stream(process.stderr, task["stderr_lines"], "stderr_total", task)
            )
            
            # Wait for process to complete (with optional timeout for background)
            if background_timeout is not None:
                try:
                    await asyncio.wait_for(process.wait(), timeout=background_timeout)
                except asyncio.TimeoutError:
                    process.terminate()
                    await asyncio.sleep(0.5)
                    if process.returncode is None:
                        process.kill()
                    task["status"] = "timeout"
                    task["exit_code"] = -1
                    task["finished_at"] = time.time()
                    # Cancel stream readers
                    stdout_task.cancel()
                    stderr_task.cancel()
                    task["process"] = None
                    return
            else:
                # No timeout, wait indefinitely
                await process.wait()
            
            # Wait for stream readers to finish
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            
            task["status"] = "completed"
            task["exit_code"] = process.returncode
            task["finished_at"] = time.time()
            
        except Exception as e:
            task["status"] = "error"
            task["stderr_lines"].append(f"Error: {str(e)}")
            task["stderr_total"] += 1
            task["exit_code"] = -1
            task["finished_at"] = time.time()
        
        # Remove process reference to allow GC
        task["process"] = None
    
    @staticmethod
    def _cleanup_expired_tasks():
        """Remove tasks that have exceeded TTL"""
        now = time.time()
        to_remove = []
        for task_id, task in _background_tasks.items():
            if task["status"] != "running" and task["finished_at"]:
                if now - task["finished_at"] > TASK_TTL_SECONDS:
                    to_remove.append(task_id)
        for tid in to_remove:
            del _background_tasks[tid]
        return len(to_remove)
    
    @staticmethod
    def query_task(task_id: str, tail_lines: int = DEFAULT_TAIL_LINES) -> Dict[str, Any]:
        """
        Query the status and result of a task (running or completed within TTL)
        
        Args:
            task_id: The task ID returned by run_command
            tail_lines: Number of lines to return (default 50)
        
        Returns:
            Task status and tail of stdout/stderr (last N lines)
        """
        # Cleanup expired tasks first
        ShellTools._cleanup_expired_tasks()
        
        task = _background_tasks.get(task_id)
        
        if not task:
            return {
                "success": False,
                "error": f"Task '{task_id}' not found. It may have expired (TTL={TASK_TTL_SECONDS}s) or never existed."
            }
        
        # Get tail of output
        stdout_list = list(task["stdout_lines"])
        stderr_list = list(task["stderr_lines"])
        
        result = {
            "success": True,
            "task_id": task_id,
            "command": task["command"],
            "status": task["status"],
            "started_at": task["started_at"],
            "stdout_tail": '\n'.join(stdout_list[-tail_lines:]) if stdout_list else "",
            "stderr_tail": '\n'.join(stderr_list[-tail_lines:]) if stderr_list else "",
            "stdout_total_lines": task["stdout_total"],
            "stderr_total_lines": task["stderr_total"],
        }
        
        if task["status"] == "running":
            elapsed = time.time() - task["started_at"]
            result["elapsed_seconds"] = round(elapsed, 1)
        else:
            result["exit_code"] = task["exit_code"]
            result["finished_at"] = task["finished_at"]
            if task["finished_at"]:
                result["duration_seconds"] = round(task["finished_at"] - task["started_at"], 1)
                # Show remaining TTL
                remaining_ttl = TASK_TTL_SECONDS - (time.time() - task["finished_at"])
                result["expires_in_seconds"] = round(max(0, remaining_ttl), 0)
        
        return result
    
    @staticmethod
    def list_tasks() -> Dict[str, Any]:
        """List all tracked tasks (running + completed within TTL)"""
        # Cleanup expired tasks first
        ShellTools._cleanup_expired_tasks()
        
        tasks = []
        now = time.time()
        for task_id, task in _background_tasks.items():
            task_info = {
                "task_id": task_id,
                "command": task["command"][:50] + "..." if len(task["command"]) > 50 else task["command"],
                "status": task["status"],
                "started_at": task["started_at"],
                "stdout_lines": task["stdout_total"],
                "stderr_lines": task["stderr_total"],
            }
            if task["status"] != "running" and task["finished_at"]:
                remaining_ttl = TASK_TTL_SECONDS - (now - task["finished_at"])
                task_info["expires_in_seconds"] = round(max(0, remaining_ttl), 0)
            tasks.append(task_info)
        
        return {
            "success": True,
            "tasks": tasks,
            "total": len(tasks),
            "ttl_seconds": TASK_TTL_SECONDS
        }
    
    @staticmethod
    def clear_completed_tasks() -> Dict[str, Any]:
        """Remove all completed/failed tasks immediately (ignore TTL)"""
        to_remove = [tid for tid, t in _background_tasks.items() if t["status"] != "running"]
        for tid in to_remove:
            del _background_tasks[tid]
        
        return {
            "success": True,
            "removed": len(to_remove),
            "remaining": len(_background_tasks)
        }
    
    @staticmethod
    def _get_env_with_display() -> Dict[str, str]:
        """Get environment variables with DISPLAY set for GUI apps"""
        env = os.environ.copy()
        # Ensure DISPLAY is set for GUI applications
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        # Set XAUTHORITY if not set
        if "XAUTHORITY" not in env:
            xauth_path = os.path.expanduser("~/.Xauthority.x0")
            if os.path.exists(xauth_path):
                env["XAUTHORITY"] = xauth_path
            else:
                xauth_default = os.path.expanduser("~/.Xauthority")
                if os.path.exists(xauth_default):
                    env["XAUTHORITY"] = xauth_default
        return env
    
    @staticmethod
    async def _run_visible(
        command: str, 
        cwd: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """Run command in visible terminal"""
        # Create a wrapper script
        script_content = f"""#!/bin/bash
cd {cwd}
{command}
echo ""
echo "=== Command finished (exit code: $?) ==="
sleep 3
"""
        script_path = f"/tmp/novaic_visible_{os.getpid()}.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # Run in xterm
        xterm_cmd = [
            "xterm",
            "-geometry", "120x40",
            "-title", f"NovAIC: {command[:50]}",
            "-e", script_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *xterm_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for terminal to close or timeout
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            process.terminate()
        
        # Cleanup
        if os.path.exists(script_path):
            os.unlink(script_path)
        
        return {
            "success": True,
            "stdout": "(Command ran in visible terminal)",
            "stderr": "",
            "exit_code": 0,
            "visible": True
        }
    
    @staticmethod
    async def run_python(
        code: str,
        visible: bool = False
    ) -> Dict[str, Any]:
        """
        Execute Python code
        
        Args:
            code: Python code to execute
            visible: If true, run in visible terminal
        """
        # Write code to temp file
        script_path = f"/tmp/novaic_python_{os.getpid()}.py"
        with open(script_path, 'w') as f:
            f.write(code)
        
        try:
            result = await ShellTools.run_command(
                f"python3 {script_path}",
                visible=visible
            )
            return result
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

