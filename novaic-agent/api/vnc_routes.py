"""
VNC Server Management API
Agent 现在运行在宿主机，VNC 服务由 VM 的 autostart.sh 自动启动。
这个 API 提供状态检查和重启功能。
"""

from fastapi import APIRouter, HTTPException
import socket
import subprocess
import os

router = APIRouter(prefix="/api/vnc", tags=["vnc"])

VNC_PORT = 5900
WEBSOCKET_PORT = 6080

# SSH 配置（从环境变量读取，默认值）
SSH_PORT = int(os.getenv("VM_SSH_PORT", "2222"))
SSH_USER = os.getenv("VM_SSH_USER", "user")
SSH_HOST = os.getenv("VM_SSH_HOST", "localhost")


def _check_port(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    """检查端口是否可连接（通过 QEMU 端口转发）"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


@router.post("/start")
async def start_vnc():
    """
    VNC 服务由 VM 的 autostart.sh 自动启动。
    这个 API 只检查服务是否就绪。
    """
    vnc_ready = _check_port(VNC_PORT)
    ws_ready = _check_port(WEBSOCKET_PORT)
    
    if vnc_ready and ws_ready:
        return {
            "status": "running",
            "port": VNC_PORT,
            "ws_port": WEBSOCKET_PORT,
            "websockify": True,
            "message": "VNC server is running (managed by VM)"
        }
    elif vnc_ready:
        return {
            "status": "running",
            "port": VNC_PORT,
            "ws_port": WEBSOCKET_PORT,
            "websockify": False,
            "message": "VNC running but websockify not ready yet"
        }
    else:
        return {
            "status": "starting",
            "port": VNC_PORT,
            "ws_port": WEBSOCKET_PORT,
            "websockify": ws_ready,
            "message": "VNC services starting (managed by VM autostart)"
        }


@router.post("/stop")
async def stop_vnc():
    """VNC 服务由 VM 管理，不支持从 Agent 停止"""
    return {
        "status": "info",
        "message": "VNC is managed by VM, use VM stop to stop VNC"
    }


@router.get("/status")
async def vnc_status():
    """检查 VNC 服务状态（通过端口检测）"""
    vnc_ready = _check_port(VNC_PORT)
    ws_ready = _check_port(WEBSOCKET_PORT)
    
    return {
        "running": vnc_ready,
        "websockify": ws_ready,
        "port": VNC_PORT if vnc_ready else None,
        "ws_port": WEBSOCKET_PORT if ws_ready else None,
        "ready": vnc_ready and ws_ready
    }


@router.post("/restart")
async def restart_vnc():
    """
    重启 VM 内的 VNC 服务（通过 SSH 执行修复脚本）
    这会停止并重新启动 Xvfb、xfce4、x11vnc 和 websockify
    """
    try:
        # 构建 SSH 命令来执行修复脚本
        ssh_cmd = [
            "ssh",
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=no",
            "-p", str(SSH_PORT),
            f"{SSH_USER}@{SSH_HOST}",
            "bash -s"
        ]
        
        # 修复脚本内容（内联，避免需要上传文件）
        fix_script = """
        set -e
        LOG=/tmp/novaic-restart.log
        echo "[$(date)] Restarting VNC services..." >> "$LOG"
        
        # 1. 停止所有相关服务
        echo "Stopping services..."
        pkill -f "websockify.*6080" 2>/dev/null || true
        pkill -x x11vnc 2>/dev/null || true
        pkill -f xfce4 2>/dev/null || true
        pkill -x Xvfb 2>/dev/null || true
        sleep 2
        
        # 2. 清理锁文件
        rm -f /tmp/.X0-lock /tmp/.X11-unix/X0 2>/dev/null || true
        
        # 3. 重新启动服务
        if [ -f /etc/local.d/novaic-services.start ]; then
            sh /etc/local.d/novaic-services.start >> "$LOG" 2>&1
        else
            # 手动启动
            Xvfb :0 -screen 0 1280x800x24 -ac +extension GLX +render -noreset >> /tmp/xvfb.log 2>&1 &
            sleep 2
            export DISPLAY=:0
            for i in $(seq 1 10); do
                if DISPLAY=:0 xdpyinfo > /dev/null 2>&1; then break; fi
                sleep 0.5
            done
            
            # 启动 xfce4（改进版）
            export COMPOSITOR=0
            export XDG_SESSION_TYPE=x11
            export XDG_CURRENT_DESKTOP=XFCE
            export XDG_CONFIG_HOME="$HOME/.config"
            export XDG_DATA_HOME="$HOME/.local/share"
            export XDG_RUNTIME_DIR="/tmp/xfce4-runtime-$USER"
            mkdir -p "$XDG_RUNTIME_DIR" 2>/dev/null || true
            
            if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
                eval $(dbus-launch --sh-syntax 2>/dev/null) || true
            fi
            
            DISPLAY=:0 startxfce4 >> /tmp/xfce4.log 2>&1 &
            # 等待 xfce4 完全启动
            for i in $(seq 1 30); do
                sleep 0.5
                if pgrep -f xfce4-session > /dev/null && pgrep -f xfwm4 > /dev/null && pgrep -f xfce4-panel > /dev/null; then
                    break
                fi
            done
            sleep 2
            
            DISPLAY=:0 x11vnc -display :0 -forever -shared -rfbport 5900 -nopw \
                -noxdamage -wait 50 -defer 50 -nowf -nowcr -nosel \
                -cursor most -speeds lan -bg -o /tmp/x11vnc.log 2>&1
            sleep 2
            python3 -m websockify 6080 localhost:5900 >> /tmp/websockify.log 2>&1 &
            sleep 1
        fi
        
        # 4. 验证
        sleep 2
        xvfb_ok=$(pgrep -x Xvfb > /dev/null && echo "ok" || echo "failed")
        xfce4_ok=$(pgrep -f xfce4-session > /dev/null && pgrep -f xfwm4 > /dev/null && pgrep -f xfce4-panel > /dev/null && echo "ok" || echo "failed")
        x11vnc_ok=$(pgrep -x x11vnc > /dev/null && echo "ok" || echo "failed")
        ws_ok=$(pgrep -f "websockify.*6080" > /dev/null && echo "ok" || echo "failed")
        
        echo "Xvfb: $xvfb_ok"
        echo "xfce4: $xfce4_ok"
        echo "x11vnc: $x11vnc_ok"
        echo "websockify: $ws_ok"
        echo "[$(date)] Restart completed" >> "$LOG"
        """
        
        # 执行 SSH 命令
        process = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=fix_script, timeout=30)
        
        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to restart VNC: {stderr}"
            )
        
        # 等待服务就绪
        import asyncio
        for i in range(20):
            await asyncio.sleep(0.5)
            vnc_ready = _check_port(VNC_PORT)
            ws_ready = _check_port(WEBSOCKET_PORT)
            if vnc_ready and ws_ready:
                return {
                    "status": "restarted",
                    "message": "VNC services restarted successfully",
                    "output": stdout,
                    "port": VNC_PORT,
                    "ws_port": WEBSOCKET_PORT
                }
        
        # 部分就绪
        return {
            "status": "restarted",
            "message": "VNC services restarted, but may need more time to be fully ready",
            "output": stdout,
            "vnc_ready": _check_port(VNC_PORT),
            "websockify_ready": _check_port(WEBSOCKET_PORT)
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Restart timeout - services may still be starting"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart VNC: {str(e)}"
        )


@router.post("/check-gui-components")
async def check_gui_components():
    """
    检查所有 GUI 组件状态
    """
    try:
        ssh_cmd = [
            "ssh",
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=no",
            "-p", str(SSH_PORT),
            f"{SSH_USER}@{SSH_HOST}",
            "bash -s"
        ]
        
        check_script = """
        export DISPLAY=:0
        
        components = {}
        
        # 检查各个组件
        pgrep -f xfce4-session > /dev/null && components["xfce4-session"] = "running" || components["xfce4-session"] = "stopped"
        pgrep -f xfwm4 > /dev/null && components["xfwm4"] = "running" || components["xfwm4"] = "stopped"
        pgrep -f xfce4-panel > /dev/null && components["xfce4-panel"] = "running" || components["xfce4-panel"] = "stopped"
        pgrep -f xfdesktop > /dev/null && components["xfdesktop"] = "running" || components["xfdesktop"] = "stopped"
        pgrep -f xfsettingsd > /dev/null && components["xfsettingsd"] = "running" || components["xfsettingsd"] = "stopped"
        pgrep -f xfconfd > /dev/null && components["xfconfd"] = "running" || components["xfconfd"] = "stopped"
        
        # 检查窗口数
        if command -v wmctrl > /dev/null 2>&1; then
            window_count=$(DISPLAY=:0 wmctrl -l 2>/dev/null | wc -l)
        else
            window_count=0
        fi
        
        echo "xfce4-session: ${components[xfce4-session]}"
        echo "xfwm4: ${components[xfwm4]}"
        echo "xfce4-panel: ${components[xfce4-panel]}"
        echo "xfdesktop: ${components[xfdesktop]}"
        echo "xfsettingsd: ${components[xfsettingsd]}"
        echo "xfconfd: ${components[xfconfd]}"
        echo "windows: $window_count"
        """
        
        process = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=check_script, timeout=10)
        
        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check components: {stderr}"
            )
        
        # 解析输出
        result = {}
        for line in stdout.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        
        return {
            "status": "ok",
            "components": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check GUI components: {str(e)}"
        )


@router.post("/restart-xfce4")
async def restart_xfce4():
    """
    专门重启 xfce4 桌面环境（修复黑屏问题）
    """
    try:
        ssh_cmd = [
            "ssh",
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=no",
            "-p", str(SSH_PORT),
            f"{SSH_USER}@{SSH_HOST}",
            "bash -s"
        ]
        
        fix_script = """
        set -e
        export DISPLAY=:0
        
        # 检查显示是否可用
        if ! xdpyinfo > /dev/null 2>&1; then
            echo "ERROR: Display server not available"
            exit 1
        fi
        
        # 停止 xfce4
        pkill -f xfce4-session 2>/dev/null || true
        pkill -f xfwm4 2>/dev/null || true
        pkill -f xfce4-panel 2>/dev/null || true
        sleep 2
        
        # 设置环境变量
        export XDG_SESSION_TYPE=x11
        export XDG_CURRENT_DESKTOP=XFCE
        export XDG_CONFIG_HOME="$HOME/.config"
        export XDG_DATA_HOME="$HOME/.local/share"
        export XDG_RUNTIME_DIR="/tmp/xfce4-runtime-$USER"
        mkdir -p "$XDG_RUNTIME_DIR" 2>/dev/null || true
        export COMPOSITOR=0
        
        # 启动 D-Bus
        if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
            eval $(dbus-launch --sh-syntax 2>/dev/null) || true
        fi
        
        # 启动 xfce4
        DISPLAY=:0 startxfce4 >> /tmp/xfce4.log 2>&1 &
        
        # 等待启动
        for i in $(seq 1 30); do
            sleep 0.5
            if pgrep -f xfce4-session > /dev/null && pgrep -f xfwm4 > /dev/null && pgrep -f xfce4-panel > /dev/null; then
                echo "xfce4 started successfully"
                break
            fi
        done
        
        # 确保 xfdesktop 启动
        sleep 2
        if ! pgrep -f xfdesktop > /dev/null; then
            DISPLAY=:0 xfdesktop >> /tmp/xfdesktop.log 2>&1 &
        fi
        
        # 确保 xfsettingsd 启动
        if ! pgrep -f xfsettingsd > /dev/null; then
            DISPLAY=:0 xfsettingsd >> /tmp/xfsettingsd.log 2>&1 &
        fi
        
        # 启动测试窗口
        sleep 1
        DISPLAY=:0 xfce4-terminal --geometry 80x24+100+100 --title="GUI Test" --command="echo 'GUI ready!' && sleep 5" >> /tmp/xfce4-terminal.log 2>&1 &
        
        echo "All components started"
        exit 0
        """
        
        process = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=fix_script, timeout=20)
        
        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to restart xfce4: {stderr or stdout}"
            )
        
        return {
            "status": "restarted",
            "message": "xfce4 desktop environment restarted",
            "output": stdout
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart xfce4: {str(e)}"
        )


@router.post("/resize")
async def resize_vnc(width: int, height: int):
    """VNC 服务由 VM 管理，不支持动态调整大小"""
    return {
        "status": "info",
        "message": "VNC resize not supported, VM uses fixed resolution"
    }
