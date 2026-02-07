#!/opt/novaic/venv/bin/python3
"""
VMUSE Browser Standalone - 简化版持久化浏览器

直接使用 VMUSE 的 browser.py 逻辑，作为命令行工具运行
使用 launch_persistent_context 保持浏览器状态

用法:
    vmuse_browser_standalone.py <command> [<args_json>]
"""

import sys
import json
import asyncio
import base64
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, BrowserContext

# 配置
USER_DATA_DIR = "/home/ubuntu/.config/chromium"
BROWSER_TIMEOUT = 30000  # ms


class BrowserTools:
    """Browser automation using Playwright with persistent user data"""
    
    def __init__(self):
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._new_tab_info: Optional[Dict[str, Any]] = None
    
    def _on_new_page(self, page: Page):
        """Callback when a new page/tab is opened"""
        self._new_tab_info = {
            "url": page.url,
            "message": f"New tab opened: {page.url}"
        }
        # Auto-switch to new tab
        self._page = page
        print(f"[Browser] New tab opened and switched: {page.url}", file=sys.stderr)
    
    async def _ensure_browser(self) -> Page:
        """Ensure browser is running and return the page"""
        if self._page is not None:
            return self._page
        
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        
        if self._context is None:
            import os
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            
            print(f"[Browser] Using persistent user data: {USER_DATA_DIR}", file=sys.stderr)
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                viewport={"width": 1280, "height": 720},
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            # Listen for new tabs
            self._context.on("page", self._on_new_page)
        
        # Get existing page or create new one
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()
        
        return self._page
    
    async def navigate(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """Navigate to URL"""
        try:
            page = await self._ensure_browser()
            
            await page.goto(url, wait_until=wait_until, timeout=BROWSER_TIMEOUT)
            
            # Get page info
            title = await page.title()
            current_url = page.url
            
            # Get simplified HTML structure
            html_content = await page.evaluate("""
                () => {
                    function simplify(el, depth = 0) {
                        if (depth > 5) return '...';
                        const tag = el.tagName.toLowerCase();
                        let info = tag;
                        
                        if (el.id) info += `#${el.id}`;
                        if (el.className && typeof el.className === 'string') {
                            info += '.' + el.className.split(' ').slice(0, 2).join('.');
                        }
                        
                        const children = Array.from(el.children).slice(0, 5);
                        if (children.length > 0) {
                            const childInfo = children.map(c => simplify(c, depth + 1)).join(', ');
                            info += ` [${childInfo}]`;
                        }
                        
                        return info;
                    }
                    return simplify(document.body);
                }
            """)
            
            return {
                "success": True,
                "url": current_url,
                "title": title,
                "structure": html_content
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click an element"""
        try:
            page = await self._ensure_browser()
            self._new_tab_info = None
            
            # Try different selector strategies
            try:
                await page.click(selector, timeout=timeout)
            except:
                # Try by text
                await page.click(f"text={selector}", timeout=timeout)
            
            # Wait for any navigation or network activity
            await asyncio.sleep(0.5)
            
            result = {"success": True, "url": self._page.url}
            
            # Include new tab info if a new tab was opened
            if self._new_tab_info:
                result["new_tab"] = self._new_tab_info
                result["note"] = "A new tab was opened and is now active"
                self._new_tab_info = None
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def type_text(self, selector: str, text: str, clear: bool = True) -> Dict[str, Any]:
        """Type text into an input field"""
        try:
            page = await self._ensure_browser()
            
            if clear:
                await page.fill(selector, text, timeout=BROWSER_TIMEOUT)
            else:
                await page.type(selector, text, timeout=BROWSER_TIMEOUT)
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, full_page: bool = False) -> Dict[str, Any]:
        """Take a browser screenshot"""
        try:
            page = await self._ensure_browser()
            
            screenshot_bytes = await page.screenshot(full_page=full_page)
            
            return {
                "success": True,
                "screenshot": base64.b64encode(screenshot_bytes).decode('utf-8')
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def content(self) -> Dict[str, Any]:
        """Get page HTML content"""
        try:
            page = await self._ensure_browser()
            html = await page.content()
            return {
                "success": True,
                "html": html,
                "url": page.url,
                "title": await page.title()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command"}))
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
            print(json.dumps({"error": f"Invalid JSON arguments: {e}"}))
            sys.exit(1)
    
    browser = BrowserTools()
    
    try:
        if command == "navigate":
            result = await browser.navigate(args.get("url", ""))
        elif command == "click":
            result = await browser.click(args.get("selector", ""))
        elif command == "type":
            result = await browser.type_text(
                args.get("selector", ""),
                args.get("text", ""),
                args.get("clear", True)
            )
        elif command == "screenshot":
            result = await browser.screenshot(args.get("full_page", False))
        elif command == "content":
            result = await browser.content()
        else:
            result = {"error": f"Unknown command: {command}"}
        
        print(json.dumps(result))
        sys.exit(0 if result.get("success") else 1)
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
