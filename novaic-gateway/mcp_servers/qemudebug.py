"""
QEMU Debug MCP Server - 虚拟机调试和设置工具

提供 Hypervisor 层面的 VM 调试工具和 VM 设置工具。
仅在 VM 内 MCP Server 无响应时使用，或用于初始化 VM。

启用方式: export NOVAIC_MCP_QEMUDEBUG_ENABLED=true
"""

import os
import platform
import base64
import asyncio
import socket
import tempfile
import time
import shutil
import subprocess
import logging
from typing import Optional, Dict, Any, List

from .base import BaseMCPServer

logger = logging.getLogger(__name__)

# Ubuntu Cloud Image 配置
UBUNTU_VERSIONS = {
    "24.04": "noble",
    "22.04": "jammy",
    "20.04": "focal",
}


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
    - qemu_deploy_vmuse_code: 部署 MCP Server 代码
    - qemu_download_image: 下载云镜像
    - qemu_create_vm: 创建 VM
    - qemu_start_vm: 启动 VM
    """
    
    name = "qemudebug"
    description = "QEMU 虚拟机调试和设置工具"
    
    def __init__(self, agent_id: Optional[str] = None, agent_index: int = 0):
        # QEMU configuration
        self.ssh_host = os.environ.get("QEMU_SSH_HOST", "127.0.0.1")
        self.ssh_user = os.environ.get("QEMU_SSH_USER", "ubuntu")
        # SSH key is now managed by SshKeyManager (no more env var)
        self.vnc_host = os.environ.get("QEMU_VNC_HOST", "127.0.0.1")
        self.monitor_socket = os.environ.get("QEMU_MONITOR_SOCKET", "/tmp/novaic-qemudebug-monitor.sock")
        
        # 直接使用传入的 agent_index（由调用者从数据库获取）
        self._agent_index = agent_index
        
        # 中心化端口分配
        from config.agents import allocate_ports_for_agent
        self._ports_config = allocate_ports_for_agent(self._agent_index)
        
        logger.info(f"[QemuDebugMCPServer] agent_id={agent_id}, agent_index={self._agent_index}")
        
        # 存储 agent_id 用于后续操作 (必须有 agent_id)
        if not agent_id:
            raise ValueError("[QemuDebugMCPServer] agent_id is required")
        self._init_agent_id = agent_id
        
        # VM Setup configuration
        self.data_dir = os.environ.get("NOVAIC_DATA_DIR", os.path.expanduser("~/.novaic"))
        
        # 共享资源目录（源镜像、固件等只读资源）
        self.shared_dir = os.path.join(self.data_dir, "shared")
        self.shared_images_dir = os.path.join(self.shared_dir, "images")  # 源镜像（共享）
        self.firmware_dir = os.path.join(self.shared_dir, "firmware")     # UEFI 固件（共享）
        
        # Agent 独立目录（VM 磁盘、配置等）
        self.agent_dir = os.path.join(self.data_dir, "agents", self._init_agent_id)
        self.vm_dir = os.path.join(self.agent_dir, "vm")
        self.disk_dir = os.path.join(self.vm_dir, "disk")      # VM 磁盘（独立）
        self.iso_dir = os.path.join(self.vm_dir, "iso")        # cloud-init ISO（独立）
        self.config_dir = os.path.join(self.vm_dir, "config")  # cloud-init 配置（独立）
        
        # VM 运行状态
        self.vm_pid_file = os.path.join(self.vm_dir, ".vm.pid")
        
        logger.info(f"[QemuDebugMCPServer] VM dir: {self.vm_dir}")
        
        # 架构检测
        self.arch = platform.machine()
        self.is_arm64 = self.arch in ("arm64", "aarch64")
        
        super().__init__(agent_id=agent_id, agent_index=agent_index)
    
    # Note: _resolve_agent_index removed - agent_index is now passed directly to __init__
    
    @property
    def ssh_port(self) -> int:
        """SSH 端口 (中心化分配)"""
        return self._ports_config.ssh
    
    @property
    def vnc_port(self) -> int:
        """VNC 端口 (中心化分配)"""
        return self._ports_config.vnc
    
    @property
    def mcp_port(self) -> int:
        """MCP 端口 (中心化分配)"""
        return self._ports_config.vm
    
    @property
    def websocket_port(self) -> int:
        """WebSocket 端口 (中心化分配)"""
        return self._ports_config.websocket
    
    def _build_instructions(self) -> str:
        return """QEMU Debug MCP - 虚拟机调试和设置工具

## 工具分类

### VM 设置工具 (Host 端)
| 工具 | 用途 |
|------|------|
| qemu_download_image | 下载 Ubuntu 云镜像 |
| qemu_create_vm | 创建 VM (磁盘 + cloud-init) |
| qemu_start_vm | 启动 VM |
| qemu_deploy_vmuse_code | 部署 MCP Server 代码 |

### VM 调试工具 (Fallback)
| 工具 | 用途 |
|------|------|
| qemu_ssh_exec | 通过 SSH 执行命令 |
| qemu_vnc_screenshot | 获取 VNC 显示截图 |
| qemu_send_keys | 发送键盘输入 (绕过 Guest) |
| qemu_send_mouse | 发送鼠标输入 (绕过 Guest) |
| qemu_status | 检查 VM 状态 |
| qemu_restart | 重启 VM |

## VM 创建流程

```
qemu_download_image()  # 下载 Ubuntu 镜像
      ↓
qemu_create_vm()       # 创建 VM 磁盘和 cloud-init
      ↓
qemu_start_vm()        # 启动 VM
      ↓
等待 SSH 可用 (qemu_status 轮询)
      ↓
qemu_deploy_vmuse_code()  # 部署 MCP Server
```

## 调试工具使用场景

| 场景 | VM 内工具 | QEMU Debug |
|------|----------|------------|
| 正常操作 | ✅ 推荐 | ❌ |
| MCP 无响应 | ❌ 不可用 | ✅ 使用 |
| 系统崩溃 | ❌ 不可用 | ✅ 使用 |
| 键盘被锁定 | ❌ 可能失败 | ✅ 绕过 |
"""
    
    async def _ssh_exec(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a command via SSH using SshKeyManager."""
        try:
            import asyncssh
            from vm.ssh import get_ssh_key_manager
            
            # Get private key from SshKeyManager
            ssh_manager = get_ssh_key_manager()
            key_path = await ssh_manager.get_private_key_path()
            
            connect_kwargs = {
                "host": self.ssh_host,
                "port": self.ssh_port,
                "username": self.ssh_user,
                "known_hosts": None,
                "client_keys": [str(key_path)],
                "compression_algs": None,  # 禁用压缩，避免 zlib 错误
            }
            
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
    
    def _ensure_dirs(self) -> None:
        """确保所有必要目录存在。"""
        # 共享目录
        for d in [self.shared_images_dir, self.firmware_dir]:
            os.makedirs(d, exist_ok=True)
        # Agent 独立目录
        for d in [self.vm_dir, self.disk_dir, self.iso_dir, self.config_dir]:
            os.makedirs(d, exist_ok=True)
    
    async def _get_ssh_pubkey(self) -> str:
        """获取 SSH 公钥（使用 SshKeyManager）。"""
        from vm.ssh import get_ssh_key_manager
        ssh_manager = get_ssh_key_manager()
        return await ssh_manager.get_public_key()
    
    def _find_qemu_img(self) -> str:
        """查找 qemu-img 路径。"""
        for path in ["/opt/homebrew/bin/qemu-img", "/usr/local/bin/qemu-img", "qemu-img"]:
            if shutil.which(path):
                return path
        raise FileNotFoundError("qemu-img not found")
    
    def _find_qemu_system(self) -> str:
        """查找 qemu-system 路径。"""
        cmd = "qemu-system-aarch64" if self.is_arm64 else "qemu-system-x86_64"
        for path in [f"/opt/homebrew/bin/{cmd}", f"/usr/local/bin/{cmd}", cmd]:
            if shutil.which(path):
                return path
        raise FileNotFoundError(f"{cmd} not found")
    
    def _find_mkisofs(self) -> Optional[str]:
        """查找 mkisofs 或替代工具。"""
        for cmd in ["mkisofs", "genisoimage", "hdiutil"]:
            if shutil.which(cmd):
                return cmd
        return None
    
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
            
            # Check VM process via PID file (primary method)
            pid = None
            if os.path.exists(server.vm_pid_file):
                try:
                    with open(server.vm_pid_file, "r") as f:
                        pid = int(f.read().strip())
                    # Check if process is running (signal 0 doesn't kill, just checks)
                    os.kill(pid, 0)
                    status["vm_running"] = True
                    status["details"]["pid"] = pid
                    status["details"]["pid_file"] = server.vm_pid_file
                except (ValueError, ProcessLookupError):
                    # PID file exists but process not running
                    status["details"]["pid_error"] = "Process not found (VM may have crashed)"
                except PermissionError:
                    # Process exists but we can't signal it (still means it's running)
                    status["vm_running"] = True
                    status["details"]["pid"] = pid
            else:
                status["details"]["pid_error"] = f"PID file not found: {server.vm_pid_file}"
            
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
            
            # If SSH/VNC reachable but PID check failed, VM is likely running
            # (maybe started by another process or PID file was deleted)
            if not status["vm_running"] and (status["ssh_reachable"] or status["vnc_reachable"]):
                status["vm_running"] = True
                status["details"]["detection_method"] = "network_reachability"
            
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
            restart_service: Optional[bool] = True,
            force: Optional[bool] = False
        ) -> Dict[str, Any]:
            """
            Deploy novaic-mcp-vmuse code to VM.
            
            智能部署流程：
            1. 检查 cloud-init 是否完成（未完成则返回 wait 状态）
            2. 检查 Python venv 是否就绪
            3. 复制代码到 /opt/novaic-mcp-vmuse/
            4. 启动 novaic.service
            5. 验证 MCP 服务是否响应
            
            Args:
                restart_service: 是否重启 novaic 服务 (默认: True)
                force: 强制部署，即使 cloud-init 未完成 (默认: False)
            
            Returns:
                Dictionary with:
                - success: bool - 部署是否成功
                - status: str - "wait" | "deployed" | "error"
                - cloudinit_complete: bool - cloud-init 是否完成
                - cloudinit_progress: str - cloud-init 进度信息
                - venv_ready: bool - Python venv 是否就绪
                - files_copied: list - 复制的文件列表
                - service_status: str - 服务状态
                - mcp_reachable: bool - MCP 是否可达
            """
            import asyncssh
            
            result = {
                "success": False,
                "status": "error",
                "cloudinit_complete": False,
                "cloudinit_progress": "",
                "venv_ready": False,
                "files_copied": [],
                "service_status": "unknown",
                "mcp_reachable": False,
            }
            
            # 1. 找到 novaic-mcp-vmuse 路径
            resource_dir = os.environ.get("NOVAIC_RESOURCE_DIR", "")
            vmuse_path = None
            
            if resource_dir:
                candidate = os.path.join(resource_dir, "novaic-mcp-vmuse")
                if os.path.exists(candidate):
                    vmuse_path = candidate
            
            if not vmuse_path:
                gateway_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                candidate = os.path.join(gateway_dir, "novaic-mcp-vmuse")
                if os.path.exists(candidate):
                    vmuse_path = candidate
            
            if not vmuse_path or not os.path.exists(vmuse_path):
                result["error"] = f"novaic-mcp-vmuse not found. NOVAIC_RESOURCE_DIR={resource_dir}"
                return result
            
            logger.info(f"[qemu_deploy_vmuse_code] Using source: {vmuse_path}")
            
            try:
                # 2. SSH 连接（使用 SshKeyManager）
                from vm.ssh import get_ssh_key_manager
                ssh_manager = get_ssh_key_manager()
                key_path = await ssh_manager.get_private_key_path()
                
                connect_kwargs = {
                    "host": server.ssh_host,
                    "port": server.ssh_port,
                    "username": server.ssh_user,
                    "known_hosts": None,
                    "client_keys": [str(key_path)],
                    "compression_algs": None,  # 禁用压缩，避免 zlib 错误
                }
                
                async with asyncssh.connect(**connect_kwargs) as conn:
                    # 3. 检查 cloud-init 状态
                    cloudinit_check = await conn.run(
                        "test -f /var/log/novaic-init-done.log && echo 'DONE' || echo 'PENDING'",
                        check=False
                    )
                    cloudinit_done = "DONE" in cloudinit_check.stdout
                    result["cloudinit_complete"] = cloudinit_done
                    
                    if not cloudinit_done:
                        # 获取 cloud-init 进度 - 一次命令获取所有状态
                        progress_result = await conn.run(
                            """
LOG=/var/log/cloud-init-output.log
echo "=== MILESTONES ==="
grep -c 'Hit:\\|Get:' $LOG 2>/dev/null || echo "0"        # apt_hits
grep -c 'Setting up' $LOG 2>/dev/null || echo "0"         # packages_setup
grep -q 'Setting up xfce4 ' $LOG 2>/dev/null && echo "HAS_XFCE4"
grep -q 'Setting up chromium' $LOG 2>/dev/null && echo "HAS_CHROMIUM"
grep -q 'Setting up python3-pip' $LOG 2>/dev/null && echo "HAS_PYTHON_PIP"
test -d /opt/novaic-venv/bin && echo "HAS_VENV"
grep -q 'Installing.*fastmcp\\|pip install.*fastmcp' $LOG 2>/dev/null && echo "HAS_PIP_DEPS"
grep -q 'playwright install\\|Playwright' $LOG 2>/dev/null && echo "HAS_PLAYWRIGHT"
grep -q 'systemctl enable\\|systemctl start' $LOG 2>/dev/null && echo "HAS_SERVICES"
echo "=== RECENT ==="
tail -5 $LOG 2>/dev/null | grep -E 'Setting up|Unpacking|pip|playwright|venv|systemctl' | tail -1
""",
                            check=False
                        )
                        output = progress_result.stdout
                        
                        # 解析进度 - 里程碑定义（按顺序，越后面进度越高）
                        MILESTONES = [
                            ("HAS_SERVICES",    95, "Starting services...",              1),
                            ("HAS_PLAYWRIGHT",  90, "Installing Playwright Chromium...", 2),
                            ("HAS_PIP_DEPS",    80, "Installing Python dependencies...", 3),
                            ("HAS_VENV",        70, "Creating Python virtual environment...", 5),
                            ("HAS_PYTHON_PIP",  60, "Installing Python environment...",  6),
                            ("HAS_CHROMIUM",    40, "Installing Chromium browser...",    8),
                            ("HAS_XFCE4",       20, "Installing desktop environment...", 10),
                        ]
                        
                        # 找到最高的已完成里程碑
                        percent, stage, eta_minutes = 5, "Initializing...", 15
                        for marker, pct, desc, eta in MILESTONES:
                            if marker in output:
                                percent, stage, eta_minutes = pct, desc, eta
                                break
                        
                        # 如果还没到第一个里程碑，检查 apt update 进度
                        if percent == 5:
                            lines = output.split('\n')
                            if len(lines) > 0:
                                try:
                                    apt_hits = int(lines[1].strip()) if lines[1].strip().isdigit() else 0
                                    if apt_hits > 0:
                                        percent, stage, eta_minutes = 10, "Updating package lists...", 12
                                except (IndexError, ValueError):
                                    pass
                        
                        # 提取最近的活动日志
                        last_activity = ""
                        if "=== RECENT ===" in output:
                            recent_part = output.split("=== RECENT ===")[-1].strip()
                            if recent_part:
                                last_activity = recent_part.split('\n')[0][:80]
                        
                        result["cloudinit_progress"] = stage
                        result["cloudinit_percent"] = percent
                        result["cloudinit_eta_minutes"] = eta_minutes
                        result["cloudinit_last_activity"] = last_activity
                        
                        if not force:
                            result["status"] = "wait"
                            result["message"] = f"cloud-init {percent}% - {stage} (ETA: ~{eta_minutes} min)"
                            logger.info(f"[qemu_deploy_vmuse_code] cloud-init {percent}%, returning wait")
                            return result
                    
                    # 4. 检查 venv 是否就绪
                    venv_check = await conn.run(
                        "test -d /opt/novaic-venv/bin && /opt/novaic-venv/bin/python -c 'import fastmcp' 2>/dev/null && echo 'READY'",
                        check=False
                    )
                    venv_ready = "READY" in venv_check.stdout
                    result["venv_ready"] = venv_ready
                    
                    if not venv_ready and not force:
                        result["status"] = "wait"
                        result["message"] = "Python venv not ready. cloud-init may still be installing dependencies."
                        result["cloudinit_progress"] = "Installing Python dependencies..."
                        logger.info(f"[qemu_deploy_vmuse_code] venv not ready, returning wait")
                        return result
                    
                    # 5. 停止服务（如果存在）
                    await conn.run("sudo systemctl stop novaic 2>/dev/null || true", check=False)
                    
                    # 6. 清理旧代码
                    await conn.run("rm -rf /opt/novaic-mcp-vmuse/src /opt/novaic-mcp-vmuse/skills", check=False)
                    
                    # 7. 复制代码
                    files_copied = []
                    
                    src_path = os.path.join(vmuse_path, "src")
                    if os.path.exists(src_path):
                        await asyncssh.scp(src_path, (conn, "/opt/novaic-mcp-vmuse/"), recurse=True)
                        files_copied.append("src/")
                    
                    skills_path = os.path.join(vmuse_path, "skills")
                    if os.path.exists(skills_path):
                        await asyncssh.scp(skills_path, (conn, "/opt/novaic-mcp-vmuse/"), recurse=True)
                        files_copied.append("skills/")
                    
                    pyproject_path = os.path.join(vmuse_path, "pyproject.toml")
                    if os.path.exists(pyproject_path):
                        await asyncssh.scp(pyproject_path, (conn, "/opt/novaic-mcp-vmuse/"))
                        files_copied.append("pyproject.toml")
                    
                    result["files_copied"] = files_copied
                    logger.info(f"[qemu_deploy_vmuse_code] Copied files: {files_copied}")
                    
                    # 8. 启动服务
                    if restart_service is not False:
                        # 先 daemon-reload 确保 service 文件已加载
                        await conn.run("sudo systemctl daemon-reload", check=False)
                        
                        start_result = await conn.run("sudo systemctl restart novaic", check=False)
                        if start_result.exit_status == 0:
                            result["service_status"] = "started"
                        else:
                            # 服务启动失败，尝试获取错误信息
                            log_result = await conn.run(
                                "journalctl -u novaic -n 10 --no-pager 2>/dev/null || echo 'No logs'",
                                check=False
                            )
                            result["service_status"] = f"start_failed: {start_result.stderr.strip()}"
                            result["service_logs"] = log_result.stdout.strip()[:500]
                    else:
                        result["service_status"] = "not_started"
                    
                    # 9. 等待服务启动并验证 MCP
                    if restart_service is not False:
                        await asyncio.sleep(3)  # 等待服务启动
                        
                        # 检查服务状态
                        status_check = await conn.run("systemctl is-active novaic", check=False)
                        service_active = status_check.stdout.strip() == "active"
                        
                        if service_active:
                            result["service_status"] = "active"
                            
                            # 验证 MCP 端点
                            mcp_check = await conn.run(
                                'curl -s -m 5 http://localhost:8080/mcp -X POST '
                                '-H "Content-Type: application/json" '
                                '-H "Accept: application/json, text/event-stream" '
                                '-d \'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","clientInfo":{"name":"deploy-check"}}}\' '
                                '| grep -q "protocolVersion" && echo "MCP_OK"',
                                check=False
                            )
                            result["mcp_reachable"] = "MCP_OK" in mcp_check.stdout
                        else:
                            result["service_status"] = f"inactive ({status_check.stdout.strip()})"
                    
                    # 10. 设置最终状态
                    if result["service_status"] == "active" and result["mcp_reachable"]:
                        result["success"] = True
                        result["status"] = "deployed"
                        result["message"] = "MCP Server deployed and running!"
                    elif result["service_status"] == "active":
                        result["success"] = True
                        result["status"] = "deployed"
                        result["message"] = "Service started but MCP not yet responding. May need a few more seconds."
                    else:
                        result["status"] = "error"
                        result["message"] = f"Service failed to start: {result['service_status']}"
                    
                    return result
                    
            except Exception as e:
                logger.error(f"[qemu_deploy_vmuse_code] Error: {e}")
                result["error"] = str(e)
                return result
        
        @self.mcp.tool()
        async def qemu_download_image(
            version: Optional[str] = "24.04",
            force: Optional[bool] = False
        ) -> Dict[str, Any]:
            """
            Download Ubuntu cloud image.
            
            下载 Ubuntu 云镜像到本地。首次安装 VM 需要先下载镜像。
            
            Args:
                version: Ubuntu 版本 (默认: "24.04", 支持 "22.04", "20.04")
                force: 强制重新下载，即使本地已有文件 (默认: False)
            
            Returns:
                Dictionary with success, image_path, size_mb, downloaded
            """
            import httpx
            
            version = version or "24.04"
            if version not in UBUNTU_VERSIONS:
                return {"success": False, "error": f"Unsupported version: {version}. Supported: {list(UBUNTU_VERSIONS.keys())}"}
            
            codename = UBUNTU_VERSIONS[version]
            arch_suffix = "arm64" if server.is_arm64 else "amd64"
            image_name = f"{codename}-server-cloudimg-{arch_suffix}.img"
            
            server._ensure_dirs()
            # 源镜像放在共享目录（所有 agent 共用）
            image_path = os.path.join(server.shared_images_dir, image_name)
            
            # 检查是否已存在 (除非 force=True)
            if os.path.exists(image_path) and not force:
                size_mb = os.path.getsize(image_path) / (1024 * 1024)
                return {
                    "success": True,
                    "image_path": image_path,
                    "size_mb": round(size_mb, 1),
                    "downloaded": False,
                    "message": "Image already exists (use force=True to re-download)"
                }
            
            # 删除旧文件 (如果 force)
            if force and os.path.exists(image_path):
                os.unlink(image_path)
                logger.info(f"[qemu_download_image] Removed existing image for force download")
            
            # 下载（流式，带进度通知）
            url = f"https://cloud-images.ubuntu.com/{codename}/current/{image_name}"
            logger.info(f"[qemu_download_image] Downloading from {url}")
            
            # 进度通知函数
            async def notify_progress(message: str):
                """发送进度通知到 Gateway chat API"""
                try:
                    gateway_url = os.environ.get("NOVAIC_GATEWAY_URL", "http://127.0.0.1:19999")
                    async with httpx.AsyncClient(timeout=5.0) as notify_client:
                        await notify_client.post(
                            f"{gateway_url}/api/chat/event",
                            json={
                                "type": "AGENT_NOTIFY",
                                "data": {
                                    "agent_id": server._init_agent_id,
                                    "message": message,
                                    "level": "info",
                                    "reply_type": "notification"
                                }
                            }
                        )
                except Exception as e:
                    logger.debug(f"[qemu_download_image] Failed to send progress notification: {e}")
            
            try:
                async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as client:
                    # 先获取文件大小
                    head_resp = await client.head(url)
                    total_size = int(head_resp.headers.get("content-length", 0))
                    total_mb = total_size / (1024 * 1024)
                    
                    logger.info(f"[qemu_download_image] Total size: {total_mb:.1f} MB")
                    await notify_progress(f"📥 开始下载 Ubuntu {version} 镜像 ({total_mb:.0f} MB)...")
                    
                    # 流式下载
                    downloaded = 0
                    last_progress = 0
                    
                    async with client.stream("GET", url) as response:
                        response.raise_for_status()
                        
                        with open(image_path, "wb") as f:
                            async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 每 20% 发送一次进度通知
                                if total_size > 0:
                                    progress = int(downloaded / total_size * 100)
                                    if progress >= last_progress + 20:
                                        last_progress = progress
                                        downloaded_mb = downloaded / (1024 * 1024)
                                        logger.info(f"[qemu_download_image] Progress: {progress}%")
                                        await notify_progress(f"⏳ 下载进度: {progress}% ({downloaded_mb:.0f}/{total_mb:.0f} MB)")
                    
                    size_mb = os.path.getsize(image_path) / (1024 * 1024)
                    return {
                        "success": True,
                        "image_path": image_path,
                        "size_mb": round(size_mb, 1),
                        "downloaded": True,
                        "message": "Download complete"
                    }
            except Exception as e:
                if os.path.exists(image_path):
                    os.unlink(image_path)
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def qemu_create_vm(
            disk_size: Optional[str] = "40G",
            memory: Optional[str] = "4096",
            cpus: Optional[int] = 4
        ) -> Dict[str, Any]:
            """
            Create VM from downloaded cloud image.
            
            创建 VM 磁盘、cloud-init ISO 和 UEFI 固件（ARM64）。
            需要先运行 qemu_download_image 下载镜像。
            
            Args:
                disk_size: 磁盘大小 (默认: "40G")
                memory: 内存大小 MB (默认: "4096")
                cpus: CPU 核心数 (默认: 4)
            
            Returns:
                Dictionary with success, disk_path, seed_iso_path
            """
            server._ensure_dirs()
            
            # 查找源镜像（在共享目录）
            arch_suffix = "arm64" if server.is_arm64 else "amd64"
            image_files = [f for f in os.listdir(server.shared_images_dir) if f.endswith(f"-{arch_suffix}.img")]
            if not image_files:
                return {"success": False, "error": "No cloud image found. Run qemu_download_image first."}
            
            source_image = os.path.join(server.shared_images_dir, image_files[0])
            # VM 磁盘放在 agent 独立目录
            disk_path = os.path.join(server.disk_dir, "novaic-vm.qcow2")
            seed_iso_path = os.path.join(server.iso_dir, "cloud-init-seed.iso")
            
            try:
                qemu_img = server._find_qemu_img()
                
                # 1. 创建磁盘
                if os.path.exists(disk_path):
                    os.unlink(disk_path)
                
                subprocess.run([qemu_img, "convert", "-f", "qcow2", "-O", "qcow2", source_image, disk_path], check=True)
                subprocess.run([qemu_img, "resize", disk_path, disk_size or "40G"], check=True)
                
                # 2. 获取 SSH 公钥（使用 SshKeyManager）
                ssh_pubkey = await server._get_ssh_pubkey()
                
                # 3. 创建 cloud-init 配置
                meta_data = f"instance-id: novaic-vm\nlocal-hostname: novaic-vm\n"
                
                # 简化的 user-data（完整版参考 setup.rs）
                user_data = f"""#cloud-config
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    ssh_authorized_keys:
      - {ssh_pubkey}

chpasswd:
  list: |
    ubuntu:ubuntu
  expire: false

ssh_pwauth: true

package_update: true
packages:
  - xfce4
  - xfce4-terminal
  - lightdm
  - x11vnc
  - chromium-browser
  - xdotool
  - scrot
  - python3
  - python3-pip
  - python3-venv
  - curl
  - git

write_files:
  - path: /etc/lightdm/lightdm.conf.d/50-autologin.conf
    content: |
      [Seat:*]
      autologin-user=ubuntu
      autologin-user-timeout=0
      user-session=xfce

runcmd:
  - chown -R ubuntu:ubuntu /home/ubuntu
  - mkdir -p /opt/novaic-mcp-vmuse /opt/novaic-venv
  - chown -R ubuntu:ubuntu /opt/novaic-mcp-vmuse /opt/novaic-venv
  - systemctl enable lightdm
  - systemctl start lightdm
  - echo "NovAIC VM cloud-init completed" > /var/log/novaic-init-done.log

final_message: "NovAIC VM ready"
"""
                
                # 写入配置文件
                meta_path = os.path.join(server.config_dir, "meta-data")
                user_path = os.path.join(server.config_dir, "user-data")
                with open(meta_path, "w") as f:
                    f.write(meta_data)
                with open(user_path, "w") as f:
                    f.write(user_data)
                
                # 4. 创建 cloud-init ISO
                mkisofs = server._find_mkisofs()
                if not mkisofs:
                    return {"success": False, "error": "mkisofs/genisoimage/hdiutil not found"}
                
                if mkisofs == "hdiutil":
                    # macOS
                    temp_dir = tempfile.mkdtemp()
                    shutil.copy(meta_path, temp_dir)
                    shutil.copy(user_path, temp_dir)
                    subprocess.run([
                        "hdiutil", "makehybrid", "-o", seed_iso_path.replace(".iso", ""),
                        "-hfs", "-joliet", "-iso", "-default-volume-name", "cidata", temp_dir
                    ], check=True)
                    shutil.rmtree(temp_dir)
                else:
                    subprocess.run([
                        mkisofs, "-output", seed_iso_path, "-volid", "cidata",
                        "-joliet", "-rock", user_path, meta_path
                    ], check=True)
                
                # 5. ARM64: 配置 UEFI 固件
                uefi_vars_path = None
                if server.is_arm64:
                    # 查找 UEFI 固件
                    uefi_src = "/opt/homebrew/share/qemu/edk2-aarch64-code.fd"
                    uefi_dst = os.path.join(server.firmware_dir, "QEMU_EFI.fd")
                    uefi_vars_path = os.path.join(server.firmware_dir, "QEMU_VARS.fd")
                    
                    if not os.path.exists(uefi_dst):
                        if os.path.exists(uefi_src):
                            shutil.copy(uefi_src, uefi_dst)
                        else:
                            return {"success": False, "error": "UEFI firmware not found"}
                    
                    if not os.path.exists(uefi_vars_path):
                        # 创建空的 UEFI 变量文件
                        with open(uefi_vars_path, "wb") as f:
                            f.write(b'\x00' * 64 * 1024 * 1024)  # 64MB
                
                return {
                    "success": True,
                    "disk_path": disk_path,
                    "seed_iso_path": seed_iso_path,
                    "uefi_vars_path": uefi_vars_path,
                    "disk_size": disk_size,
                    "message": "VM created successfully"
                }
                
            except Exception as e:
                logger.error(f"[qemu_create_vm] Error: {e}")
                return {"success": False, "error": str(e)}
        
        @self.mcp.tool()
        async def qemu_start_vm(
            memory: Optional[str] = "4096",
            cpus: Optional[int] = 4,
            daemon: Optional[bool] = True
        ) -> Dict[str, Any]:
            """
            Start the QEMU VM.
            
            启动 VM。需要先运行 qemu_create_vm 创建 VM。
            端口自动从当前 agent 配置获取，不需要手动指定。
            
            Args:
                memory: 内存大小 MB (默认: "4096")
                cpus: CPU 核心数 (默认: 4)
                daemon: 后台运行 (默认: True)
            
            Returns:
                Dictionary with success, pid, ports
            """
            disk_path = os.path.join(server.disk_dir, "novaic-vm.qcow2")
            seed_iso_path = os.path.join(server.iso_dir, "cloud-init-seed.iso")
            
            if not os.path.exists(disk_path):
                return {"success": False, "error": "VM disk not found. Run qemu_create_vm first."}
            
            # 检查是否已运行
            if os.path.exists(server.vm_pid_file):
                with open(server.vm_pid_file, "r") as f:
                    old_pid = f.read().strip()
                try:
                    os.kill(int(old_pid), 0)
                    return {"success": False, "error": f"VM already running (PID: {old_pid})"}
                except ProcessLookupError:
                    os.unlink(server.vm_pid_file)
            
            try:
                qemu_system = server._find_qemu_system()
                
                # 使用当前 agent 的端口配置（不允许跨 agent 操作）
                vnc_port = server.vnc_port
                mcp_port = server.mcp_port
                ssh_port = server.ssh_port
                ws_port = server.websocket_port
                
                # 构建命令
                cmd = [qemu_system]
                
                if server.is_arm64:
                    uefi_fw = os.path.join(server.firmware_dir, "QEMU_EFI.fd")
                    uefi_vars = os.path.join(server.firmware_dir, "QEMU_VARS.fd")
                    
                    cmd.extend([
                        "-M", "virt,highmem=on", "-cpu", "host", "-accel", "hvf",
                        "-m", memory or "4096", "-smp", str(cpus or 4),
                        "-drive", f"if=pflash,format=raw,file={uefi_fw},readonly=on",
                        "-drive", f"if=pflash,format=raw,file={uefi_vars}",
                        "-drive", f"if=none,id=hd0,format=qcow2,file={disk_path}",
                        "-device", "virtio-blk-pci,drive=hd0,bootindex=1",
                        "-device", "virtio-scsi-pci,id=scsi0",
                        "-drive", f"if=none,id=cd0,format=raw,file={seed_iso_path},readonly=on",
                        "-device", "scsi-cd,drive=cd0,bus=scsi0.0",
                        "-device", "virtio-gpu-pci",
                    ])
                else:
                    cmd.extend([
                        "-M", "q35", "-cpu", "host", "-accel", "hvf",
                        "-m", memory or "4096", "-smp", str(cpus or 4),
                        "-hda", disk_path,
                        "-cdrom", seed_iso_path,
                    ])
                
                # 网络和设备
                net_fwd = f"hostfwd=tcp::{vnc_port}-:5900,hostfwd=tcp::{mcp_port}-:8080,hostfwd=tcp::{ssh_port}-:22,hostfwd=tcp::{ws_port}-:6080"
                cmd.extend([
                    "-device", "virtio-net-pci,netdev=net0",
                    "-netdev", f"user,id=net0,{net_fwd}",
                    "-device", "usb-ehci",
                    "-device", "usb-kbd",
                    "-device", "usb-mouse",
                ])
                
                if daemon:
                    cmd.extend(["-display", "none", "-daemonize", "-pidfile", server.vm_pid_file])
                else:
                    cmd.extend(["-display", "cocoa" if server.is_arm64 else "gtk"])
                
                logger.info(f"[qemu_start_vm] Starting: {' '.join(cmd)}")
                
                if daemon:
                    subprocess.run(cmd, check=True)
                    await asyncio.sleep(2)
                    
                    if os.path.exists(server.vm_pid_file):
                        with open(server.vm_pid_file, "r") as f:
                            pid = f.read().strip()
                        return {
                            "success": True,
                            "pid": pid,
                            "ports": {
                                "ssh": ssh_port,
                                "vnc": vnc_port,
                                "mcp": mcp_port,
                                "websocket": ws_port
                            },
                            "message": "VM started in background"
                        }
                    else:
                        return {"success": False, "error": "VM started but PID file not found"}
                else:
                    # 前台运行
                    process = subprocess.Popen(cmd)
                    return {
                        "success": True,
                        "pid": str(process.pid),
                        "message": "VM started in foreground"
                    }
                    
            except Exception as e:
                logger.error(f"[qemu_start_vm] Error: {e}")
                return {"success": False, "error": str(e)}
