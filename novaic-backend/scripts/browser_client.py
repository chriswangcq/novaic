#!/opt/novaic/venv/bin/python3
"""
浏览器守护进程客户端

用于与 browser_daemon 通信，执行浏览器命令。

使用方法:
    browser_client.py <command> [<args_json>]

示例:
    browser_client.py navigate '{"url": "https://example.com"}'
    browser_client.py click '{"selector": "button#submit"}'
    browser_client.py screenshot
"""

import sys
import json
import socket
from pathlib import Path

SOCKET_PATH = "/tmp/novaic-browser-daemon.sock"
DAEMON_SCRIPT = "/opt/novaic/scripts/browser_daemon.py"


def ensure_daemon():
    """确保守护进程运行"""
    if not Path(SOCKET_PATH).exists():
        print("[Client] 守护进程未运行，尝试启动...", file=sys.stderr)
        
        # 启动守护进程
        import subprocess
        subprocess.Popen(
            ["/opt/novaic/venv/bin/python3", DAEMON_SCRIPT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # 等待 socket 创建
        import time
        for i in range(10):
            time.sleep(1)
            if Path(SOCKET_PATH).exists():
                print("[Client] ✓ 守护进程已启动", file=sys.stderr)
                return True
        
        print("[Client] ❌ 守护进程启动失败", file=sys.stderr)
        return False
    
    return True


def send_command(command: str, args: dict) -> dict:
    """发送命令到守护进程"""
    if not ensure_daemon():
        return {"status": "error", "error": "Daemon not available"}
    
    try:
        # 连接到守护进程
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(30.0)  # 30秒超时
        sock.connect(SOCKET_PATH)
        
        # 发送命令
        request = json.dumps({"command": command, "args": args})
        sock.sendall(request.encode('utf-8'))
        
        # 接收响应
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\n" in response:  # 完整的 JSON 响应
                break
        
        sock.close()
        
        # 解析响应
        return json.loads(response.decode('utf-8'))
    
    except socket.timeout:
        return {"status": "error", "error": "Command timeout"}
    except ConnectionRefusedError:
        return {"status": "error", "error": "Daemon connection refused"}
    except Exception as e:
        return {"status": "error", "error": f"Client error: {str(e)}"}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "error": "Missing command"}))
        sys.exit(1)
    
    command = sys.argv[1]
    args = {}
    
    if len(sys.argv) > 2:
        try:
            args = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "error": f"Invalid JSON arguments: {e}"}))
            sys.exit(1)
    
    # 发送命令到守护进程
    result = send_command(command, args)
    
    # 输出结果
    print(json.dumps(result))
    
    # 返回退出码
    if result.get("status") == "success":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
