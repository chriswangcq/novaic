#!/usr/bin/env python3
"""
Playwright 辅助脚本 - 持久化浏览器版本

使用持久化浏览器会话，浏览器保持打开状态，可以连续执行多个操作。

使用方法:
    playwright_helper_persistent.py <command> [<args_json>]

命令:
    navigate <args>  - 导航到 URL
    click <args>     - 点击元素
    type <args>      - 输入文本
    screenshot       - 截图
    content          - 获取页面内容
    close            - 关闭浏览器会话

示例:
    playwright_helper_persistent.py navigate '{"url": "https://example.com"}'
    playwright_helper_persistent.py click '{"selector": "button#submit"}'
    playwright_helper_persistent.py screenshot
    playwright_helper_persistent.py close
"""

import sys
import json
import base64
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from browser_session_manager import BrowserSessionManager
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# 默认超时时间（毫秒）
DEFAULT_TIMEOUT = 30000


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
    
    result = {}
    manager = BrowserSessionManager()
    
    try:
        # 特殊命令：关闭浏览器
        if command == "close":
            manager.cleanup()
            result = {"status": "success", "message": "Browser session closed"}
            print(json.dumps(result))
            return
        
        # 获取页面（会复用或创建）
        page = manager.get_page()
        
        # 设置默认超时
        page.set_default_timeout(DEFAULT_TIMEOUT)
        
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
                except PlaywrightTimeoutError:
                    result = {"status": "error", "error": f"Timeout navigating to {url}"}
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
                except PlaywrightTimeoutError:
                    result = {"status": "error", "error": f"Element not found or not clickable: {selector}"}
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
                except PlaywrightTimeoutError:
                    result = {"status": "error", "error": f"Element not found: {selector}"}
                except Exception as e:
                    result = {"status": "error", "error": f"Type failed: {str(e)}"}
        
        elif command == "screenshot":
            try:
                screenshot_bytes = page.screenshot(full_page=False)
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                # MCP 标准格式
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
                    "content": [
                        {
                            "type": "text",
                            "text": f"Screenshot failed: {str(e)}"
                        }
                    ],
                    "error": str(e)
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
        
        else:
            result = {"status": "error", "error": f"Unknown command: {command}"}
        
        # 输出结果（不关闭浏览器）
        print(json.dumps(result))
    
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
