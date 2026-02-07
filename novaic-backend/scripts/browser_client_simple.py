#!/opt/novaic/venv/bin/python3
"""
Browser Client - 与 browser_keep_alive 守护进程通信

通过文件系统通信（简单可靠）
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

COMMAND_FILE = "/tmp/browser_command.json"
RESULT_FILE = "/tmp/browser_result.json"
PID_FILE = "/tmp/browser_keep_alive.pid"
DAEMON_SCRIPT = "/opt/novaic/scripts/browser_keep_alive.py"

def ensure_daemon():
    """确保守护进程运行"""
    # 检查 PID 文件
    if Path(PID_FILE).exists():
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            os.kill(pid, 0)  # Signal 0 只检查进程是否存在
            return True  # 守护进程已在运行
        except (OSError, ValueError):
            # PID 文件存在但进程不存在，删除 PID 文件
            Path(PID_FILE).unlink()
    
    print("[Client] Starting browser daemon as ubuntu user...", file=sys.stderr)
    
    # 启动守护进程 - 以 ubuntu 用户身份运行
    # Guest Agent 以 root 运行，但浏览器需要以 ubuntu 用户运行才能显示在桌面
    # 使用 nohup + shell 脚本确保环境变量正确传递
    subprocess.Popen(
        [
            "sudo", "-u", "ubuntu", 
            "nohup",
            "/bin/bash", "/opt/novaic/scripts/simple_browser_daemon.sh"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        preexec_fn=None
    )
    
    # 等待守护进程启动
    for i in range(30):
        time.sleep(1)
        if Path(PID_FILE).exists():
            print("[Client] ✓ Daemon started", file=sys.stderr)
            return True
    
    print("[Client] ❌ Daemon failed to start", file=sys.stderr)
    return False


def send_command(command, args, timeout=40):
    """发送命令到守护进程"""
    if not ensure_daemon():
        return {"status": "error", "error": "Daemon not available"}
    
    # 删除旧的结果文件
    if Path(RESULT_FILE).exists():
        Path(RESULT_FILE).unlink()
    
    # 写入命令文件（设置 ubuntu 可读写）
    with open(COMMAND_FILE, 'w') as f:
        json.dump({"command": command, "args": args}, f)
    os.chmod(COMMAND_FILE, 0o666)
    
    # 等待结果
    for i in range(timeout):
        time.sleep(1)
        if Path(RESULT_FILE).exists():
            with open(RESULT_FILE, 'r') as f:
                result = json.load(f)
            Path(RESULT_FILE).unlink()
            return result
    
    return {"status": "error", "error": "Command timeout"}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "error": "Missing command"}))
        sys.exit(1)
    
    command = sys.argv[1]
    args = {}
    
    if len(sys.argv) > 2:
        try:
            arg_str = sys.argv[2]
            # Remove outer quotes if present
            if arg_str.startswith('"') and arg_str.endswith('"'):
                arg_str = arg_str[1:-1]
            
            # Handle escaped quotes
            arg_str = arg_str.replace('\\"', '"')
            
            args = json.loads(arg_str)
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "error", "error": f"Invalid JSON arguments: {e}"}))
            sys.exit(1)
    
    # 发送命令
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
