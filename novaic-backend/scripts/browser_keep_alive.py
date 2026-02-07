#!/opt/novaic/venv/bin/python3
"""
Browser Keep Alive - 保持浏览器窗口打开

这个脚本启动浏览器后不退出，保持浏览器窗口可见。
通过 signal 文件接收命令（简单的文件系统通信）。
"""

import os
import sys
import json
import asyncio
import signal
from pathlib import Path
from playwright.async_api import async_playwright

USER_DATA_DIR = "/home/ubuntu/.config/chromium"
COMMAND_FILE = "/tmp/browser_command.json"
RESULT_FILE = "/tmp/browser_result.json"
PID_FILE = "/tmp/browser_keep_alive.pid"

class BrowserKeepAlive:
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None
        self.running = True
    
    async def start_browser(self):
        """启动浏览器"""
        print(f"[{os.getpid()}] Starting browser...", file=sys.stderr)
        
        self.playwright = await async_playwright().start()
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 720},
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        
        print(f"[{os.getpid()}] ✓ Browser started", file=sys.stderr)
    
    async def handle_command(self, cmd):
        """处理命令"""
        command = cmd.get("command")
        args = cmd.get("args", {})
        
        try:
            if command == "navigate":
                url = args.get("url", "")
                await self.page.goto(url, wait_until="load", timeout=30000)
                title = await self.page.title()
                return {"status": "success", "url": self.page.url}
            
            elif command == "click":
                selector = args.get("selector", "")
                await self.page.click(selector, timeout=5000)
                return {"status": "success", "url": self.page.url}
            
            elif command == "type":
                selector = args.get("selector", "")
                text = args.get("text", "")
                await self.page.fill(selector, text, timeout=30000)
                return {"status": "success"}
            
            elif command == "screenshot":
                screenshot_bytes = await self.page.screenshot()
                import base64
                return {
                    "status": "success",
                    "data": base64.b64encode(screenshot_bytes).decode('utf-8')
                }
            
            elif command == "content":
                html = await self.page.content()
                return {
                    "status": "success",
                    "html": html,
                    "url": self.page.url
                }
            
            elif command == "stop":
                self.running = False
                return {"status": "success"}
            
            else:
                return {"status": "error", "error": f"Unknown command: {command}"}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def run(self):
        """主循环"""
        await self.start_browser()
        
        # 保存 PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        print(f"[{os.getpid()}] Waiting for commands in {COMMAND_FILE}", file=sys.stderr)
        
        while self.running:
            try:
                # 检查命令文件
                if Path(COMMAND_FILE).exists():
                    with open(COMMAND_FILE, 'r') as f:
                        cmd = json.load(f)
                    
                    print(f"[{os.getpid()}] Got command: {cmd.get('command')}", file=sys.stderr)
                    
                    # 处理命令
                    result = await self.handle_command(cmd)
                    
                    # 写入结果
                    with open(RESULT_FILE, 'w') as f:
                        json.dump(result, f)
                    os.chmod(RESULT_FILE, 0o666)  # 确保 root 可以读取
                    
                    # 删除命令文件
                    os.remove(COMMAND_FILE)
                    
                    print(f"[{os.getpid()}] Command done", file=sys.stderr)
                
                # 等待一会儿
                await asyncio.sleep(0.5)
            
            except Exception as e:
                print(f"[{os.getpid()}] Error: {e}", file=sys.stderr)
                await asyncio.sleep(1)
        
        print(f"[{os.getpid()}] Stopping...", file=sys.stderr)


def main():
    # 设置信号处理
    def signal_handler(sig, frame):
        print(f"\n[{os.getpid()}] Received signal {sig}, exiting...", file=sys.stderr)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    daemon = BrowserKeepAlive()
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
