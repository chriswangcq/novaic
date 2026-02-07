#!/usr/bin/env python3
"""
Playwright 辅助脚本 - 由 Guest Agent 调用
支持基本的浏览器操作

使用方法:
    playwright_helper.py <command> [<args_json>]

命令:
    navigate <args>  - 导航到 URL
    click <args>     - 点击元素
    type <args>      - 输入文本
    screenshot       - 截图
    content          - 获取页面内容

示例:
    playwright_helper.py navigate '{"url": "https://example.com"}'
    playwright_helper.py click '{"selector": "button#submit"}'
    playwright_helper.py type '{"selector": "input#username", "text": "admin"}'
    playwright_helper.py screenshot
    playwright_helper.py content
"""

import sys
import json
import os
import base64
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

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
    
    try:
        with sync_playwright() as p:
            # 启动浏览器（非 headless 模式，以便用户可以看到）
            browser = p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 创建新的浏览器上下文和页面
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # 设置默认超时
            page.set_default_timeout(DEFAULT_TIMEOUT)
            
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
                        result = {"status": "success"}
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
                        result = {"status": "success"}
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
            
            # 输出结果
            print(json.dumps(result))
            
            # 检查环境变量，决定是否关闭浏览器
            # BROWSER_KEEP_OPEN=1 表示保持浏览器打开
            keep_open = os.environ.get("BROWSER_KEEP_OPEN", "0") == "1"
            
            if not keep_open:
                # 关闭浏览器
                browser.close()
            else:
                # 保持浏览器打开
                # 等待用户手动关闭或超时
                print(f"[INFO] Browser kept open at {page.url}", file=sys.stderr)
    
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Playwright error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
