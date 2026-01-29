"""
NovAIC MCP Server for QEMU VM Debugging Tools.

Provides tools for debugging and controlling QEMU VMs:
- qemu_ssh_exec: Execute command via SSH
- qemu_vnc_screenshot: Get VNC screenshot
- qemu_send_keys: Send keyboard input via QEMU monitor
- qemu_send_mouse: Send mouse input via QEMU monitor
- qemu_status: Get VM status
- qemu_restart: Restart the VM
"""

import os
import base64
import asyncio
import socket
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP

# QEMU configuration (via environment)
# Default ports based on centralized port allocation (Agent 0):
# SSH: 20008 = BASE_PORT(20000) + Agent0(0*20) + SSH_OFFSET(8)
# VNC: 20006 = BASE_PORT(20000) + Agent0(0*20) + VNC_OFFSET(6)
QEMU_SSH_HOST = os.environ.get("QEMU_SSH_HOST", "127.0.0.1")
QEMU_SSH_PORT = int(os.environ.get("QEMU_SSH_PORT", "20008"))
QEMU_SSH_USER = os.environ.get("QEMU_SSH_USER", "ubuntu")
QEMU_SSH_KEY = os.environ.get("QEMU_SSH_KEY", os.path.expanduser("~/.ssh/novaic_vm"))

QEMU_VNC_HOST = os.environ.get("QEMU_VNC_HOST", "127.0.0.1")
QEMU_VNC_PORT = int(os.environ.get("QEMU_VNC_PORT", "20006"))

QEMU_MONITOR_SOCKET = os.environ.get("QEMU_MONITOR_SOCKET", "/tmp/novaic-qemudebug-monitor.sock")

mcp = FastMCP(
    name="novaic-qemudebug",
    instructions="""NovAIC QEMU Debug - 虚拟机调试工具 (Fallback)

6 个工具用于在 Hypervisor 层面调试 VM。

## ⚠️ 重要：这是 Fallback 工具

**优先使用 VM 内的工具 (novaic-mcp-vmuse)**
仅在以下情况使用本工具：
- VM 内 MCP Server 无响应
- 需要 Hypervisor 层面的操作
- 调试 VM 启动/崩溃问题

## 工具一览

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

## 使用场景

### 1. 诊断 VM 状态
```
qemu_status()  # 检查 VM 运行状态、SSH/VNC/MCP 可达性
```

### 2. VM 无响应时执行命令
```
qemu_ssh_exec(command="sudo systemctl restart novaic-mcp")
```

### 3. 获取崩溃时的屏幕
```
qemu_vnc_screenshot()  # 返回 base64 编码的图片
```

### 4. 强制重启
```
qemu_restart(force=True)  # 硬重置
qemu_restart(force=False, wait_ready=True)  # 优雅重启
```

## qemu_send_keys 键名格式

- 字母：a, b, c, ... z
- 特殊：ret (回车), spc (空格), tab, esc, backspace
- 组合：ctrl-c, alt-f4, ctrl-alt-delete
- 功能键：f1, f2, ... f12
- 方向键：up, down, left, right
"""
)


async def _ssh_exec(command: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute a command via SSH."""
    try:
        import asyncssh
        
        # Try to connect with key authentication
        connect_kwargs = {
            "host": QEMU_SSH_HOST,
            "port": QEMU_SSH_PORT,
            "username": QEMU_SSH_USER,
            "known_hosts": None,  # Disable host key checking for local VM
        }
        
        # Add key if exists
        if os.path.exists(QEMU_SSH_KEY):
            connect_kwargs["client_keys"] = [QEMU_SSH_KEY]
        
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


async def _qemu_monitor_command(command: str) -> str:
    """Send a command to QEMU monitor via socket."""
    try:
        reader, writer = await asyncio.open_unix_connection(QEMU_MONITOR_SOCKET)
        
        # Read initial prompt
        await asyncio.wait_for(reader.read(1024), timeout=2.0)
        
        # Send command
        writer.write(f"{command}\n".encode())
        await writer.drain()
        
        # Read response
        await asyncio.sleep(0.1)
        response = await asyncio.wait_for(reader.read(4096), timeout=5.0)
        
        writer.close()
        await writer.wait_closed()
        
        return response.decode().strip()
    except FileNotFoundError:
        return f"ERROR: QEMU monitor socket not found at {QEMU_MONITOR_SOCKET}"
    except Exception as e:
        return f"ERROR: {str(e)}"


@mcp.tool()
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
        Dictionary with:
        - stdout: Standard output
        - stderr: Standard error
        - exit_code: Command exit code
        - success: Whether command succeeded (exit_code == 0)
    """
    return await _ssh_exec(command, timeout)


@mcp.tool()
async def qemu_vnc_screenshot(
    format: Optional[str] = "png",
    quality: Optional[int] = 85
) -> Dict[str, Any]:
    """
    Capture a screenshot from the VM's VNC display.
    
    This captures the raw VNC framebuffer, showing exactly what would be
    displayed on a VNC client connected to the VM.
    
    Args:
        format: Image format - 'png' or 'jpeg' (default: 'png')
        quality: JPEG quality 1-100 (default: 85, only used for jpeg)
    
    Returns:
        Dictionary with:
        - image_base64: Base64 encoded image data
        - format: Image format used
        - width: Image width in pixels
        - height: Image height in pixels
        - success: Whether screenshot was captured
    """
    try:
        # Use QEMU screendump command via monitor
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".ppm", delete=False) as tmp:
            tmp_path = tmp.name
        
        # Request screenshot via QEMU monitor
        result = await _qemu_monitor_command(f"screendump {tmp_path}")
        
        if "ERROR" in result:
            return {"error": result, "success": False}
        
        # Wait for file to be written
        await asyncio.sleep(0.5)
        
        # Read and convert the image
        try:
            from PIL import Image
            import io
            
            img = Image.open(tmp_path)
            width, height = img.size
            
            # Convert to requested format
            buffer = io.BytesIO()
            if format.lower() == "jpeg":
                img = img.convert("RGB")
                img.save(buffer, format="JPEG", quality=quality)
            else:
                img.save(buffer, format="PNG")
            
            image_data = base64.b64encode(buffer.getvalue()).decode()
            
            # Cleanup
            os.unlink(tmp_path)
            
            return {
                "image_base64": image_data,
                "format": format.lower(),
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


@mcp.tool()
async def qemu_send_keys(
    keys: str,
    hold_time_ms: Optional[int] = 100
) -> Dict[str, Any]:
    """
    Send keyboard input directly to QEMU.
    
    This sends key events at the hypervisor level, bypassing the guest OS.
    Useful for debugging or when the guest is not responding to normal input.
    
    Key format uses QEMU key names:
    - Letters: a, b, c, ... z
    - Numbers: 1, 2, ... 0
    - Special: ret (enter), spc (space), tab, esc, backspace
    - Modifiers: ctrl, alt, shift, meta
    - Function keys: f1, f2, ... f12
    - Arrow keys: up, down, left, right
    - Combine with '-': ctrl-c, alt-f4, ctrl-alt-delete
    
    Args:
        keys: Key sequence to send (e.g., "ctrl-alt-delete", "hello", "ret")
        hold_time_ms: How long to hold each key in milliseconds (default: 100)
    
    Returns:
        Dictionary with:
        - success: Whether keys were sent
        - keys_sent: The key sequence that was sent
    """
    try:
        # Parse key sequence
        # For simple strings, convert to individual key presses
        key_events = []
        
        if '-' in keys and len(keys.split('-')[0]) <= 5:
            # Looks like a combo (ctrl-c, alt-f4, etc.)
            key_events.append(keys)
        else:
            # Individual characters
            for char in keys:
                if char == ' ':
                    key_events.append('spc')
                elif char == '\n':
                    key_events.append('ret')
                elif char == '\t':
                    key_events.append('tab')
                elif char.isalnum():
                    key_events.append(char.lower())
                else:
                    # Skip unsupported characters
                    continue
        
        # Send keys via QEMU monitor
        results = []
        for key in key_events:
            result = await _qemu_monitor_command(f"sendkey {key} {hold_time_ms}")
            results.append(result)
            await asyncio.sleep(hold_time_ms / 1000.0)
        
        return {
            "success": True,
            "keys_sent": key_events,
            "responses": results
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@mcp.tool()
async def qemu_send_mouse(
    x: int,
    y: int,
    button: Optional[str] = None,
    absolute: Optional[bool] = True
) -> Dict[str, Any]:
    """
    Send mouse input directly to QEMU.
    
    This moves the mouse and optionally clicks at the hypervisor level.
    
    Args:
        x: X coordinate (pixels from left)
        y: Y coordinate (pixels from top)
        button: Mouse button to click - 'left', 'right', 'middle', or None for move only
        absolute: If True, use absolute coordinates; if False, relative movement
    
    Returns:
        Dictionary with:
        - success: Whether mouse event was sent
        - position: The position that was targeted
    """
    try:
        # QEMU uses mouse_move for relative or mouse_set for absolute
        if absolute:
            # mouse_set x y [button]
            cmd = f"mouse_set {x} {y}"
        else:
            cmd = f"mouse_move {x} {y}"
        
        result = await _qemu_monitor_command(cmd)
        
        if button:
            # mouse_button 1=left, 2=middle, 4=right
            button_map = {"left": 1, "middle": 2, "right": 4}
            btn = button_map.get(button.lower(), 0)
            if btn:
                # Press
                await _qemu_monitor_command(f"mouse_button {btn}")
                await asyncio.sleep(0.05)
                # Release
                await _qemu_monitor_command("mouse_button 0")
        
        return {
            "success": "ERROR" not in result,
            "position": {"x": x, "y": y},
            "button": button,
            "response": result
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@mcp.tool()
async def qemu_status() -> Dict[str, Any]:
    """
    Get the current status of the QEMU VM.
    
    Returns information about:
    - VM running state
    - CPU and memory usage
    - Network connectivity
    - MCP server status
    
    Returns:
        Dictionary with VM status information.
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
        result = await _qemu_monitor_command("info status")
        status["vm_running"] = "running" in result.lower()
        status["details"]["qemu_status"] = result
    except Exception as e:
        status["details"]["qemu_error"] = str(e)
    
    # Check SSH
    try:
        ssh_result = await _ssh_exec("echo ok", timeout=5)
        status["ssh_reachable"] = ssh_result.get("success", False)
    except Exception:
        pass
    
    # Check VNC port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((QEMU_VNC_HOST, QEMU_VNC_PORT))
        status["vnc_reachable"] = result == 0
        sock.close()
    except Exception:
        pass
    
    # Check MCP server (VM MCP port, default 20000 for Agent 0)
    # Get from environment or use default
    mcp_vm_port = int(os.environ.get("QEMU_MCP_PORT", "20000"))
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://{QEMU_SSH_HOST}:{mcp_vm_port}/health")
            status["mcp_reachable"] = resp.status_code == 200
    except Exception:
        pass
    
    return status


@mcp.tool()
async def qemu_restart(
    force: Optional[bool] = False,
    wait_ready: Optional[bool] = True,
    timeout: Optional[int] = 120
) -> Dict[str, Any]:
    """
    Restart the QEMU VM.
    
    Args:
        force: If True, force reset without graceful shutdown (default: False)
        wait_ready: If True, wait for VM to be ready after restart (default: True)
        timeout: Timeout in seconds to wait for VM to be ready (default: 120)
    
    Returns:
        Dictionary with:
        - success: Whether restart was successful
        - duration: Time taken for restart
    """
    import time
    start_time = time.time()
    
    try:
        if force:
            # Hard reset
            result = await _qemu_monitor_command("system_reset")
        else:
            # Try graceful shutdown first
            await _ssh_exec("sudo shutdown -r now", timeout=5)
            await asyncio.sleep(5)
        
        if wait_ready:
            # Wait for VM to come back up
            ready = False
            elapsed = 0
            while elapsed < timeout:
                await asyncio.sleep(5)
                elapsed = time.time() - start_time
                
                # Check if SSH is reachable
                ssh_result = await _ssh_exec("echo ok", timeout=5)
                if ssh_result.get("success"):
                    ready = True
                    break
            
            duration = time.time() - start_time
            return {
                "success": ready,
                "duration": round(duration, 1),
                "message": "VM restarted successfully" if ready else f"VM not ready after {timeout}s"
            }
        else:
            return {
                "success": True,
                "message": "Restart initiated (not waiting for ready)"
            }
    except Exception as e:
        return {"error": str(e), "success": False}


def main():
    """Run the MCP server."""
    import sys
    
    # Default to streamable HTTP transport
    # Default port 20005 = BASE_PORT(20000) + Agent0(0*20) + QEMUDEBUG_OFFSET(5)
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "20005"))
    
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=host, port=port)
    elif transport == "stdio":
        mcp.run(transport="stdio")
    else:
        print(f"Unknown transport: {transport}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
