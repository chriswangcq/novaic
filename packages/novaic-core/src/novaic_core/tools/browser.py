"""
Browser Tools - Playwright-based browser automation
"""

import asyncio
import base64
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from ..config import settings


class BrowserTools:
    """Browser automation using Playwright"""
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
    
    async def _ensure_browser(self) -> Page:
        """Ensure browser is running and return the page"""
        if self._page is not None:
            return self._page
        
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        
        if self._browser is None:
            self._browser = await self._playwright.chromium.launch(
                headless=settings.browser_headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
        
        if self._context is None:
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
        
        if self._page is None:
            self._page = await self._context.new_page()
        
        return self._page
    
    async def navigate(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """
        Navigate to URL
        
        Args:
            url: URL to navigate to
            wait_until: load, domcontentloaded, networkidle
        """
        try:
            page = await self._ensure_browser()
            
            await page.goto(url, wait_until=wait_until, timeout=settings.browser_timeout)
            
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
        """
        Click an element
        
        Args:
            selector: CSS selector or text selector
        """
        try:
            page = await self._ensure_browser()
            
            # Try different selector strategies
            try:
                await page.click(selector, timeout=timeout)
            except:
                # Try by text
                await page.click(f"text={selector}", timeout=timeout)
            
            # Wait for any navigation or network activity
            await asyncio.sleep(0.5)
            
            return {"success": True, "url": page.url}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def type_text(
        self, 
        selector: str, 
        text: str, 
        clear: bool = True
    ) -> Dict[str, Any]:
        """
        Type text into an input field
        
        Args:
            selector: CSS selector
            text: Text to type
            clear: Whether to clear existing content first
        """
        try:
            page = await self._ensure_browser()
            
            if clear:
                await page.fill(selector, text, timeout=settings.browser_timeout)
            else:
                await page.type(selector, text, timeout=settings.browser_timeout)
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, full_page: bool = False) -> Dict[str, Any]:
        """
        Take a browser screenshot
        
        Args:
            full_page: Capture full page or just viewport
        """
        try:
            page = await self._ensure_browser()
            
            screenshot_bytes = await page.screenshot(full_page=full_page)
            
            return {
                "success": True,
                "screenshot": base64.b64encode(screenshot_bytes).decode('utf-8')
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def scroll(
        self, 
        direction: str, 
        amount: int = 500,
        selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scroll the page
        
        Args:
            direction: up, down, left, right
            amount: Pixels to scroll
            selector: Optional element to scroll within
        """
        try:
            page = await self._ensure_browser()
            
            delta_x, delta_y = 0, 0
            if direction == "down":
                delta_y = amount
            elif direction == "up":
                delta_y = -amount
            elif direction == "right":
                delta_x = amount
            elif direction == "left":
                delta_x = -amount
            
            if selector:
                element = await page.query_selector(selector)
                if element:
                    await element.evaluate(
                        f"el => el.scrollBy({delta_x}, {delta_y})"
                    )
            else:
                await page.evaluate(f"window.scrollBy({delta_x}, {delta_y})")
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def evaluate(self, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript in the browser
        
        Args:
            script: JavaScript code to execute
        """
        try:
            page = await self._ensure_browser()
            
            result = await page.evaluate(script)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_tabs(self) -> Dict[str, Any]:
        """Get all open tabs"""
        try:
            if self._context is None:
                return {"success": True, "tabs": []}
            
            pages = self._context.pages
            tabs = []
            for i, p in enumerate(pages):
                tabs.append({
                    "index": i,
                    "url": p.url,
                    "title": await p.title(),
                    "active": p == self._page
                })
            
            return {"success": True, "tabs": tabs}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def switch_tab(self, index: int) -> Dict[str, Any]:
        """Switch to a different tab"""
        try:
            if self._context is None:
                return {"success": False, "error": "No browser context"}
            
            pages = self._context.pages
            if index < 0 or index >= len(pages):
                return {"success": False, "error": f"Invalid tab index: {index}"}
            
            self._page = pages[index]
            await self._page.bring_to_front()
            
            return {"success": True, "url": self._page.url}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close_tab(self, index: Optional[int] = None) -> Dict[str, Any]:
        """Close a tab"""
        try:
            if self._context is None:
                return {"success": False, "error": "No browser context"}
            
            pages = self._context.pages
            
            if index is not None:
                if index < 0 or index >= len(pages):
                    return {"success": False, "error": f"Invalid tab index: {index}"}
                page_to_close = pages[index]
            else:
                page_to_close = self._page
            
            if page_to_close:
                await page_to_close.close()
                
                # Switch to another tab if available
                pages = self._context.pages
                if pages:
                    self._page = pages[-1]
                else:
                    self._page = await self._context.new_page()
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close browser and cleanup"""
        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# Global browser instance
_browser_tools: Optional[BrowserTools] = None


def get_browser_tools() -> BrowserTools:
    """Get or create browser tools instance"""
    global _browser_tools
    if _browser_tools is None:
        _browser_tools = BrowserTools()
    return _browser_tools

