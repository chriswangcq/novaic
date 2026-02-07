#!/opt/novaic/venv/bin/python3
"""
VMUSE 浏览器服务客户端

与 vmuse_browser_service 通信，执行浏览器命令。

使用方法:
    vmuse_browser_client.py <command> [<args_json>]

示例:
    vmuse_browser_client.py navigate '{"url": "https://example.com"}'
    vmuse_browser_client.py click '{"selector": "button#submit"}'
"""

import os
import sys
import json
import socket
import time
import subprocess
from pathlib import Path

SOCKET_PATH = "/tmp/novaic-browser-service.sock"
DAEMON_SCRIPT = "/opt/novaic/scripts/vmuse_browser_service.py"
MAX_RETRY = 3


def ensure_service():
    """确保服务运行"""
    if Path(SOCKET_PATH).exists():
        return True
    
    print("[Client] 服务未运行，启动中...", file=sys.stderr)
    
    # 启动守护进程
    # 需要设置环境变量
    env = os.environ.copy()
    env.update({
        "XAUTHORITY": "/home/ubuntu/.Xauthority",
        "DISPLAY": ":0",
        "PLAYWRIGHT_BROWSERS_PATH": "/opt/novaic/.cache"
    })
    
    subprocess.Popen(
        ["/opt/novaic/venv/bin/python3", DAEMON_SCRIPT],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # 等待 socket 创建
    for i in range(15):
        time.sleep(1)
        if Path(SOCKET_PATH).exists():
            print("[Client] ✓ 服务已启动", file=sys.stderr)
            return True
    
    print("[Client] ❌ 服务启动失败", file=sys.stderr)
    return False


def send_command(command: str, args: dict, retry=0) -> dict:
    """发送命令到服务"""
    if not ensure_service():
        return {"status": "error", "error": "Service not available"}
    
    try:
        # 连接到服务
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(40.0)  # 40秒超时（浏览器操作可能较慢）
        sock.connect(SOCKET_PATH)
        
        # 发送命令
        request = json.dumps({"command": command, "args": args})
        sock.sendall(request.encode('utf-8'))
        
        # 接收响应
        response = b""
        while True:
            chunk = sock.recv(8192)
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
        if retry < MAX_RETRY:
            # 服务可能刚启动，重试
            print(f"[Client] Connection refused, retry {retry+1}/{MAX_RETRY}...", file=sys.stderr)
            time.sleep(2)
            return send_command(command, args, retry + 1)
        return {"status": "error", "error": "Service connection refused"}
    except Exception as e:
        return {"status": "error", "error": f"Client error: {str(e)}"}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command"}))
        sys.exit(1)
    
    command = sys.argv[1]
    args = {}
    
    if len(sys.argv) > 2:
        try:
            # 参数可能被引号包裹，去除外层引号
            arg_str = sys.argv[2]
            if arg_str.startswith('"') and arg_str.endswith('"'):
                arg_str = arg_str[1:-1]
            
            # 可能需要处理转义的引号
            arg_str = arg_str.replace('\\"', '"')
            
            args = json.loads(arg_str)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON arguments: {e}"}))
            sys.exit(1)
    
    # 发送命令到服务
    result = send_command(command, args)
    
    # 转换响应格式：status -> success
    if "status" in result:
        if result["status"] == "success":
            result["success"] = True
            del result["status"]
        elif result["status"] == "error":
            result["success"] = False
            del result["status"]
    
    # 输出结果
    print(json.dumps(result))
    
    # 返回退出码
    if result.get("success"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
