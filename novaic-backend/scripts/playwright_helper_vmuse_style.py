#!/opt/novaic/venv/bin/python3
"""
Playwright 辅助脚本 - VMUSE 风格持久化浏览器

基于之前的 novaic-mcp-vmuse 实现，使用 launch_persistent_context
保持浏览器持久运行，不关闭。

使用方法:
    playwright_helper_vmuse_style.py <command> [<args_json>]
"""

import sys
import json
import os
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext

# 配置
USER_DATA_DIR = "/tmp/novaic-browser-userdata"
DEFAULT_TIMEOUT = 30000


class BrowserSession:
    """持久化浏览器会话"""
    
    _instance = None
    _playwright = None
    _context: BrowserContext = None
    _page = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def ensure_browser(self):
        """确保浏览器运行并返回 page"""
        if self._page is not None:
            return self._page
        
        if self._playwright is None:
            print("[Browser] 启动 Playwright...", file=sys.stderr)
            self._playwright = sync_playwright().start()
        
        if self._context is None:
            # 确保用户数据目录存在
            Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
            
            print(f"[Browser] 启动持久化浏览器，用户数据: {USER_DATA_DIR}", file=sys.stderr)
            
            # 关键：使用 launch_persistent_context 保持浏览器持久运行
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,  # 可见
                viewport={"width": 1280, "height": 720},
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            
            print("[Browser] 浏览器已启动", file=sys.stderr)
        
        # 获取现有页面或创建新页面
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()
        
        self._page.set_default_timeout(DEFAULT_TIMEOUT)
        
        return self._page


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
    
    try:
        # 获取浏览器会话
        session = BrowserSession.get_instance()
        page = session.ensure_browser()
        
        result = {}
        
        if command == "navigate":
            url = args.get("url")
            if not url:
                result = {"status": "error", "error": "Missing 'url' parameter"}
            else:
                try:
                    response = page.goto(url, wait_until="domcontentloaded")
                    result = {
                        "status": "success",
                        "url": page.url,
                        "title": page.title()
                    }
                    if response:
                        result["status_code"] = response.status
                except Exception as e:
                    result = {"status": "error", "error": f"Navigation failed: {str(e)}"}
        
        elif command == "click":
            selector = args.get("selector")
            if not selector:
                result = {"status": "error", "error": "Missing 'selector' parameter"}
            else:
                try:
                    page.click(selector)
                    result = {"status": "success", "url": page.url}
                except Exception as e:
                    result = {"status": "error", "error": f"Click failed: {str(e)}"}
        
        elif command == "type":
            selector = args.get("selector")
            text = args.get("text")
            if not selector:
                result = {"status": "error", "error": "Missing 'selector' parameter"}
            elif text is None:
                result = {"status": "error", "error": "Missing 'text' parameter"}
            else:
                try:
                    page.fill(selector, text)
                    result = {"status": "success", "url": page.url}
                except Exception as e:
                    result = {"status": "error", "error": f"Type failed: {str(e)}"}
        
        elif command == "screenshot":
            try:
                screenshot_bytes = page.screenshot(full_page=False)
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                result = {
                    "status": "success",
                    "url": page.url,
                    "content": [
                        {
                            "type": "image",
                            "data": screenshot_base64,
                            "mimeType": "image/png"
                        }
                    ]
                }
            except Exception as e:
                result = {
                    "status": "error",
                    "error": f"Screenshot failed: {str(e)}"
                }
        
        elif command == "content":
            try:
                html = page.content()
                result = {
                    "status": "success",
                    "html": html,
                    "url": page.url,
                    "title": page.title()
                }
            except Exception as e:
                result = {"status": "error", "error": f"Get content failed: {str(e)}"}
        
        elif command == "close":
            # 关闭浏览器
            if session._context:
                session._context.close()
            if session._playwright:
                session._playwright.stop()
            result = {"status": "success", "message": "Browser closed"}
        
        else:
            result = {"status": "error", "error": f"Unknown command: {command}"}
        
        # 输出结果（浏览器保持运行）
        print(json.dumps(result))
        
        # 输出状态信息到 stderr
        print(f"[Browser] 命令执行完成，浏览器保持运行", file=sys.stderr)
        print(f"[Browser] 当前 URL: {page.url}", file=sys.stderr)
    
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
