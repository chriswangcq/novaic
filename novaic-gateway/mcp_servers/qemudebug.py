"""
QEMU Debug MCP Server - 虚拟机调试工具 (Fallback)

提供 Hypervisor 层面的 VM 调试工具。
仅在 VM 内 MCP Server 无响应时使用。

启用方式: export NOVAIC_MCP_QEMUDEBUG_ENABLED=true
"""

import os
import base64
import asyncio
import socket
import tempfile
import time
import logging
from typing import Optional, Dict, Any

from .base import BaseMCPServer

logger = logging.getLogger(__name__)


class QemuDebugMCPServer(BaseMCPServer):
    """
    QEMU Debug MCP Server。
    
    提供工具：
    - qemu_ssh_exec: 通过 SSH 执行命令
    - qemu_vnc_screenshot: 获取 VNC 显示截图
    - qemu_send_keys: 发送键盘输入 (绕过 Guest)
    - qemu_send_mouse: 发送鼠标输入 (绕过 Guest)
    - qemu_status: 检查 VM 状态
    - qemu_restart: 重启 VM
    """
    
    name = "qemudebug"
    description = "QEMU 虚拟机调试工具 (Fallback)"
    
    def __init__(self):
        # QEMU configuration (via environment)
        self.ssh_host = os.environ.get("QEMU_SSH_HOST", "127.0.0.1")
        self.ssh_port = int(os.environ.get("QEMU_SSH_PORT", "20008"))
        self.ssh_user = os.environ.get("QEMU_SSH_USER", "ubuntu")
        self.ssh_key = os.environ.get("QEMU_SSH_KEY", os.path.expanduser("~/.ssh/novaic_vm"))
        
        self.vnc_host = os.environ.get("QEMU_VNC_HOST", "127.0.0.1")
        self.vnc_port = int(os.environ.get("QEMU_VNC_PORT", "20006"))
        
        self.monitor_socket = os.environ.get("QEMU_MONITOR_SOCKET", "/tmp/novaic-qemudebug-monitor.sock")
        self.mcp_port = int(os.environ.get("QEMU_MCP_PORT", "20000"))
        
        super().__init__()
    
    def _build_instructions(self) -> str:
        return """QEMU Debug MCP - 虚拟机调试工具 (Fallback)

## ⚠️ 重要：这是 Fallback 工具

**优先使用 VM 内的工具 (novaic-mcp-vmuse)**
仅在以下情况使用本工具：
- VM 内 MCP Server 无响应
- 需要 Hypervisor 层面的操作
- 调试 VM 启动/崩溃问题

## 工具列表

| 工具 | 用途 |
|------|------|
| qemu_ssh_exec | 通过 SSH 执行命令 |
| qemu_vnc_screenshot | 获取 VNC 显示截图 |
| qemu_send_keys | 发送键盘输入 (绕过 Guest) |
| qemu_send_mouse | 发送鼠标输入 (绕过 Guest) |
| qemu_status | 检查 VM 状态 |
| qemu_restart | 重启 VM |

## 与 VM 内工具的区别

| 场景 | VM 内工具 | QEMU Debug |
|------|----------|------------|
| 正常操作 | ✅ 推荐 | ❌ |
| MCP 无响应 | ❌ 不可用 | ✅ 使用 |
| 系统崩溃 | ❌ 不可用 | ✅ 使用 |
| 键盘被锁定 | ❌ 可能失败 | ✅ 绕过 |
"""
    
    async def _ssh_exec(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a command via SSH."""
        try:
            import asyncssh
            
            connect_kwargs = {
                "host": self.ssh_host,
                "port": self.ssh_port,
                "username": self.ssh_user,
                "known_hosts": None,
            }
            
            if os.path.exists(self.ssh_key):
                connect_kwargs["client_keys"] = [self.ssh_key]
            
            async with asyncssh.connect(**connect_kwargs) as conn:
                result = await asyncio.wait_for(
                    conn.run(command, check=False),
                    timeout=timeout
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_status,
                    "success": result.exit_status == 0
                }
        except asyncio.TimeoutError:
            return {"error": f"Command timed out after {timeout}s", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _qemu_monitor_command(self, command: str) -> str:
        """Send a command to QEMU monitor via socket."""
        try:
            reader, writer = await asyncio.open_unix_connection(self.monitor_socket)
            
            await asyncio.wait_for(reader.read(1024), timeout=2.0)
            
            writer.write(f"{command}\n".encode())
            await writer.drain()
            
            await asyncio.sleep(0.1)
            response = await asyncio.wait_for(reader.read(4096), timeout=5.0)
            
            writer.close()
            await writer.wait_closed()
            
            return response.decode().strip()
        except FileNotFoundError:
            return f"ERROR: QEMU monitor socket not found at {self.monitor_socket}"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _register_tools(self) -> None:
        """注册所有 QEMU Debug 工具。"""
        server = self  # Capture for closures
        
        @self.mcp.tool()
        async def qemu_ssh_exec(
            command: str,
            timeout: Optional[int] = 30
        ) -> Dict[str, Any]:
            """
            Execute a command on the VM via SSH.
            
            This bypasses the in-VM MCP server and executes commands directly via SSH.
            Useful for debugging when the MCP server is not responding.
            
            Args:
                command: Shell command to execute
                timeout: Command timeout in seconds (default: 30)
            
            Returns:
                Dictionary with stdout, stderr, exit_code, success
            """
            return await server._ssh_exec(command, timeout or 30)
        
        @self.mcp.tool()
        async def qemu_vnc_screenshot(
            format: Optional[str] = "png",
            quality: Optional[int] = 85
        ) -> Dict[str, Any]:
            """
            Capture a screenshot from the VM's VNC display.
            
            Args:
                format: Image format - 'png' or 'jpeg' (default: 'png')
                quality: JPEG quality 1-100 (default: 85, only used for jpeg)
            
            Returns:
                Dictionary with image_base64, format, width, height, success
            """
            try:
                with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as tmp:
                    tmp_path = tmp.name
                
                result = await server._qemu_monitor_command(f"screendump {tmp_path}")
                
                if "ERROR" in result:
                    return {"error": result, "success": False}
                
                await asyncio.sleep(0.5)
                
                try:
                    from PIL import Image
                    import io
                    
                    img = Image.open(tmp_path)
                    width, height = img.size
                    
                    buffer = io.BytesIO()
                    if (format or "png").lower() == "jpeg":
                        img = img.convert("RGB")
                        img.save(buffer, format="JPEG", quality=quality or 85)
                    else:
                        img.save(buffer, format="PNG")
                    
                    image_data = base64.b64encode(buffer.getvalue()).decode()
                    
                    os.unlink(tmp_path)
                    
                    return {
                        "image_base64": image_data,
                        "format": (format or "png").lower(),
                        "width": width,
                        "height": height,
                        "success": True
                    }
                except Exception as e:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    return {"error": f"Failed to process image: {str(e)}", "success": False}
                    
            except Exception as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def qemu_send_keys(
            keys: str,
            hold_time_ms: Optional[int] = 100
        ) -> Dict[str, Any]:
            """
            Send keyboard input directly to QEMU.
            
            Key format uses QEMU key names:
            - Letters: a, b, c, ... z
            - Special: ret (enter), spc (space), tab, esc, backspace
            - Modifiers: ctrl, alt, shift, meta
            - Combine with '-': ctrl-c, alt-f4, ctrl-alt-delete
            
            Args:
                keys: Key sequence to send
                hold_time_ms: How long to hold each key in milliseconds (default: 100)
            
            Returns:
                Dictionary with success, keys_sent
            """
            try:
                key_events = []
                hold_ms = hold_time_ms or 100
                
                if '-' in keys and len(keys.split('-')[0]) <= 5:
                    key_events.append(keys)
                else:
                    for char in keys:
                        if char == ' ':
                            key_events.append('spc')
                        elif char == '\n':
                            key_events.append('ret')
                        elif char == '\t':
                            key_events.append('tab')
                        elif char.isalnum():
                            key_events.append(char.lower())
                
                results = []
                for key in key_events:
                    result = await server._qemu_monitor_command(f"sendkey {key} {hold_ms}")
                    results.append(result)
                    await asyncio.sleep(hold_ms / 1000.0)
                
                return {
                    "success": True,
                    "keys_sent": key_events,
                    "responses": results
                }
            except Exception as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def qemu_send_mouse(
            x: int,
            y: int,
            button: Optional[str] = None,
            absolute: Optional[bool] = True
        ) -> Dict[str, Any]:
            """
            Send mouse input directly to QEMU.
            
            Args:
                x: X coordinate (pixels from left)
                y: Y coordinate (pixels from top)
                button: Mouse button - 'left', 'right', 'middle', or None for move only
                absolute: If True, use absolute coordinates (default: True)
            
            Returns:
                Dictionary with success, position
            """
            try:
                if absolute is not False:
                    cmd = f"mouse_set {x} {y}"
                else:
                    cmd = f"mouse_move {x} {y}"
                
                result = await server._qemu_monitor_command(cmd)
                
                if button:
                    button_map = {"left": 1, "middle": 2, "right": 4}
                    btn = button_map.get(button.lower(), 0)
                    if btn:
                        await server._qemu_monitor_command(f"mouse_button {btn}")
                        await asyncio.sleep(0.05)
                        await server._qemu_monitor_command("mouse_button 0")
                
                return {
                    "success": "ERROR" not in result,
                    "position": {"x": x, "y": y},
                    "button": button,
                    "response": result
                }
            except Exception as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def qemu_status() -> Dict[str, Any]:
            """
            Get the current status of the QEMU VM.
            
            Returns information about VM running state, SSH/VNC/MCP reachability.
            """
            status = {
                "vm_running": False,
                "ssh_reachable": False,
                "vnc_reachable": False,
                "mcp_reachable": False,
                "details": {}
            }
            
            # Check QEMU monitor
            try:
                result = await server._qemu_monitor_command("info status")
                status["vm_running"] = "running" in result.lower()
                status["details"]["qemu_status"] = result
            except Exception as e:
                status["details"]["qemu_error"] = str(e)
            
            # Check SSH
            try:
                ssh_result = await server._ssh_exec("echo ok", timeout=5)
                status["ssh_reachable"] = ssh_result.get("success", False)
            except Exception:
                pass
            
            # Check VNC port
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((server.vnc_host, server.vnc_port))
                status["vnc_reachable"] = result == 0
                sock.close()
            except Exception:
                pass
            
            # Check MCP server
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"http://{server.ssh_host}:{server.mcp_port}/health")
                    status["mcp_reachable"] = resp.status_code == 200
            except Exception:
                pass
            
            return status
        
        @self.mcp.tool()
        async def qemu_restart(
            force: Optional[bool] = False,
            wait_ready: Optional[bool] = True,
            timeout: Optional[int] = 120
        ) -> Dict[str, Any]:
            """
            Restart the QEMU VM.
            
            Args:
                force: If True, force reset without graceful shutdown (default: False)
                wait_ready: If True, wait for VM to be ready (default: True)
                timeout: Timeout in seconds to wait for VM (default: 120)
            
            Returns:
                Dictionary with success, duration
            """
            start_time = time.time()
            timeout_val = timeout or 120
            
            try:
                if force:
                    await server._qemu_monitor_command("system_reset")
                else:
                    await server._ssh_exec("sudo shutdown -r now", timeout=5)
                    await asyncio.sleep(5)
                
                if wait_ready is not False:
                    ready = False
                    elapsed = 0
                    while elapsed < timeout_val:
                        await asyncio.sleep(5)
                        elapsed = time.time() - start_time
                        
                        ssh_result = await server._ssh_exec("echo ok", timeout=5)
                        if ssh_result.get("success"):
                            ready = True
                            break
                    
                    duration = time.time() - start_time
                    return {
                        "success": ready,
                        "duration": round(duration, 1),
                        "message": "VM restarted successfully" if ready else f"VM not ready after {timeout_val}s"
                    }
                else:
                    return {
                        "success": True,
                        "message": "Restart initiated (not waiting for ready)"
                    }
            except Exception as e:
                return {"error": str(e), "success": False}
        
        @self.mcp.tool()
        async def qemu_deploy_vmuse_code(
            restart_service: Optional[bool] = True
        ) -> Dict[str, Any]:
            """
            Deploy novaic-mcp-vmuse code to VM.
            
            从 App Resources 复制 MCP Server 代码到 VM：
            - src/ → /opt/novaic-mcp-vmuse/src/
            - skills/ → /opt/novaic-mcp-vmuse/skills/
            - pyproject.toml → /opt/novaic-mcp-vmuse/
            
            Args:
                restart_service: 是否重启 novaic 服务 (默认: True)
            
            Returns:
                Dictionary with success, files_copied, service_status
            """
            import asyncssh
            
            # 1. 找到 novaic-mcp-vmuse 路径
            resource_dir = os.environ.get("NOVAIC_RESOURCE_DIR", "")
            vmuse_path = None
            
            # 尝试从 resource_dir 找
            if resource_dir:
                candidate = os.path.join(resource_dir, "novaic-mcp-vmuse")
                if os.path.exists(candidate):
                    vmuse_path = candidate
            
            # 开发环境回退：从 Gateway 位置推断
            if not vmuse_path:
                # Gateway 在 novaic/novaic-gateway，vmuse 在 novaic/novaic-mcp-vmuse
                gateway_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                candidate = os.path.join(gateway_dir, "novaic-mcp-vmuse")
                if os.path.exists(candidate):
                    vmuse_path = candidate
            
            if not vmuse_path or not os.path.exists(vmuse_path):
                return {
                    "success": False,
                    "error": f"novaic-mcp-vmuse not found. NOVAIC_RESOURCE_DIR={resource_dir}"
                }
            
            logger.info(f"[qemu_deploy_vmuse_code] Using source: {vmuse_path}")
            
            files_copied = []
            
            try:
                # 2. SSH 连接
                connect_kwargs = {
                    "host": server.ssh_host,
                    "port": server.ssh_port,
                    "username": server.ssh_user,
                    "known_hosts": None,
                }
                if os.path.exists(server.ssh_key):
                    connect_kwargs["client_keys"] = [server.ssh_key]
                
                async with asyncssh.connect(**connect_kwargs) as conn:
                    # 3. 停止服务
                    await conn.run("sudo systemctl stop novaic 2>/dev/null || true", check=False)
                    
                    # 4. 清理旧代码
                    await conn.run("rm -rf /opt/novaic-mcp-vmuse/src /opt/novaic-mcp-vmuse/skills", check=False)
                    
                    # 5. 复制 src/
                    src_path = os.path.join(vmuse_path, "src")
                    if os.path.exists(src_path):
                        await asyncssh.scp(src_path, (conn, "/opt/novaic-mcp-vmuse/"), recurse=True)
                        files_copied.append("src/")
                    
                    # 6. 复制 skills/
                    skills_path = os.path.join(vmuse_path, "skills")
                    if os.path.exists(skills_path):
                        await asyncssh.scp(skills_path, (conn, "/opt/novaic-mcp-vmuse/"), recurse=True)
                        files_copied.append("skills/")
                    
                    # 7. 复制 pyproject.toml
                    pyproject_path = os.path.join(vmuse_path, "pyproject.toml")
                    if os.path.exists(pyproject_path):
                        await asyncssh.scp(pyproject_path, (conn, "/opt/novaic-mcp-vmuse/"))
                        files_copied.append("pyproject.toml")
                    
                    # 8. 重启服务
                    service_status = "not_restarted"
                    if restart_service is not False:
                        result = await conn.run("sudo systemctl restart novaic", check=False)
                        if result.exit_status == 0:
                            service_status = "restarted"
                        else:
                            service_status = f"restart_failed: {result.stderr}"
                    
                    return {
                        "success": True,
                        "source_path": vmuse_path,
                        "files_copied": files_copied,
                        "service_status": service_status
                    }
                    
            except Exception as e:
                logger.error(f"[qemu_deploy_vmuse_code] Error: {e}")
                return {"success": False, "error": str(e), "files_copied": files_copied}
