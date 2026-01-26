"""
Shell Tools - Execute commands and Python code
"""

import asyncio
import subprocess
import os
from typing import Dict, Any, Optional

from ..config import settings


class ShellTools:
    """Shell execution tools"""
    
    @staticmethod
    async def run_command(
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
        visible: bool = False,
        background: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a shell command
        
        Args:
            command: Shell command to execute
            cwd: Working directory
            timeout: Timeout in seconds
            visible: If true, run in visible terminal (for GUI apps)
            background: If true, run command in background and return immediately.
                       Use this for launching GUI apps or long-running processes.
                       The command will be detached from the shell session.
        """
        try:
            work_dir = cwd or settings.work_dir
            os.makedirs(work_dir, exist_ok=True)
            
            if background:
                # Run truly in background (detached), return immediately
                result = await ShellTools._run_detached(command, work_dir)
            elif visible:
                # Run in visible terminal using xterm
                result = await ShellTools._run_visible(command, work_dir, timeout)
            else:
                # Run and wait for completion
                result = await ShellTools._run_foreground(command, work_dir, timeout)
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command timed out after {timeout}s",
                "stdout": "",
                "stderr": "",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "exit_code": -1
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
    async def _run_foreground(
        command: str, 
        cwd: str, 
        timeout: int
    ) -> Dict[str, Any]:
        """Run command and wait for completion"""
        env = ShellTools._get_env_with_display()
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env  # Pass environment with DISPLAY
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        return {
            "success": process.returncode == 0,
            "stdout": stdout.decode('utf-8', errors='replace'),
            "stderr": stderr.decode('utf-8', errors='replace'),
            "exit_code": process.returncode
        }
    
    @staticmethod
    async def _run_detached(
        command: str, 
        cwd: str
    ) -> Dict[str, Any]:
        """
        Run command truly in background (detached from shell session).
        Returns immediately without waiting for the command to complete.
        Use for GUI apps or long-running processes.
        """
        env = ShellTools._get_env_with_display()
        
        # Use setsid to create a new session, nohup to ignore hangup signals
        # Redirect output to /dev/null to prevent blocking
        # The & at the end runs it in background
        detached_cmd = f"nohup {command} > /dev/null 2>&1 &"
        
        process = await asyncio.create_subprocess_shell(
            detached_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,  # Pass environment with DISPLAY
            start_new_session=True  # Detach from parent session
        )
        
        # Wait briefly for the shell to spawn the background process
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=5  # Short timeout, the shell command should return quickly
            )
        except asyncio.TimeoutError:
            # This shouldn't happen with nohup &, but handle it gracefully
            stdout, stderr = b"", b""
        
        return {
            "success": True,
            "stdout": f"Command launched in background: {command}",
            "stderr": stderr.decode('utf-8', errors='replace') if stderr else "",
            "exit_code": 0,
            "background": True,
            "note": "Command is running in background. Use list_windows or screenshot to check its status."
        }
    
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
        script_path = f"/tmp/linux2mcp_visible_{os.getpid()}.sh"
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
        script_path = f"/tmp/linux2mcp_python_{os.getpid()}.py"
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

