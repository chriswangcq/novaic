#!/usr/bin/env python3
"""直接测试 Guest Agent socket"""

import socket
import json
import time

socket_path = "/tmp/novaic/novaic-ga-e270ec13-bfd4-4b5b-abd9-b51b6fa85ec6.sock"

print(f"连接 Guest Agent socket: {socket_path}\n")

try:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_path)
    print("✓ Socket 连接成功\n")
    
    # 测试 1: guest-ping
    print("1. 测试 guest-ping...")
    cmd = {"execute": "guest-ping"}
    sock.sendall((json.dumps(cmd) + "\n").encode())
    
    sock.settimeout(2.0)
    try:
        response = sock.recv(4096)
        print(f"   响应: {response.decode()}")
    except socket.timeout:
        print("   ❌ 超时，Guest Agent 未响应")
    
    # 测试 2: guest-info
    print("\n2. 测试 guest-info...")
    cmd = {"execute": "guest-info"}
    sock.sendall((json.dumps(cmd) + "\n").encode())
    
    try:
        response = sock.recv(4096)
        print(f"   响应: {response.decode()[:200]}...")
    except socket.timeout:
        print("   ❌ 超时")
    
    # 测试 3: guest-exec
    print("\n3. 测试 guest-exec...")
    cmd = {
        "execute": "guest-exec",
        "arguments": {
            "path": "/bin/echo",
            "arg": ["hello"],
            "capture-output": True
        }
    }
    sock.sendall((json.dumps(cmd) + "\n").encode())
    
    try:
        response = sock.recv(4096)
        print(f"   响应: {response.decode()}")
        result = json.loads(response.decode())
        if "return" in result:
            pid = result["return"].get("pid")
            if pid:
                print(f"   ✓ 获取到 PID: {pid}")
            else:
                print(f"   ❌ 响应中缺少 pid 字段")
        else:
            print(f"   ❌ 响应格式错误")
    except socket.timeout:
        print("   ❌ 超时")
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON 解析失败: {e}")
    
    sock.close()

except FileNotFoundError:
    print(f"❌ Socket 文件不存在")
except ConnectionRefusedError:
    print(f"❌ 连接被拒绝")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
