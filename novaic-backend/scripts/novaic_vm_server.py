#!/opt/novaic/venv/bin/python3
"""
NovAIC VM Server - 完整 VMUSE 服务器
在 VM 内运行的 HTTP 服务，提供所有 VMUSE 工具的访问

包含: Browser, Desktop (mouse/keyboard/screenshot), Shell, Files
"""

import os
import asyncio
import logging
import subprocess
import base64
import tempfile
import secrets
import time
from pathlib import Path
from typing import Optional, Dict, Any
from aiohttp import web
import signal

# Playwright
from playwright.async_api import async_playwright, Page, BrowserContext

# 配置
USER_DATA_DIR = "/home/ubuntu/.config/novaic-browser"  # 独立目录避免与系统 chromium 冲突
BROWSER_TIMEOUT = 30000  # ms
PORT = 8080

# 日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class BrowserManager:
    """浏览器管理器 - 保持浏览器持久运行"""
    
    def __init__(self):
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._new_tab_info: Optional[Dict[str, Any]] = None
    
    def _on_new_page(self, page: Page):
        """新标签页回调"""
        self._new_tab_info = {
            "url": page.url,
            "message": f"New tab opened: {page.url}"
        }
        self._page = page
        logger.info(f"New tab opened: {page.url}")
    
    async def ensure_browser(self) -> Page:
        """确保浏览器运行"""
        if self._page is not None:
            return self._page
        
        if self._playwright is None:
            logger.info("Starting Playwright...")
            self._playwright = await async_playwright().start()
        
        if self._context is None:
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            
            # 禁用 crashpad - 设置环境变量
            os.environ['CHROME_CRASHPAD_PIPE_NAME'] = ''
            os.environ['BREAKPAD_DUMP_LOCATION'] = ''
            
            logger.info(f"Launching persistent browser: {USER_DATA_DIR}")
            # VMUSE 原始实现 + 添加 crashpad 禁用参数
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,
                viewport={"width": 1280, "height": 720},
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-features=CrashReporter,Crashpad",  # 禁用崩溃报告
                ]
            )
            self._context.on("page", self._on_new_page)
            logger.info("✓ Browser launched")
        
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()
        
        return self._page
    
    async def navigate(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """导航到 URL"""
        try:
            page = await self.ensure_browser()
            await page.goto(url, wait_until=wait_until, timeout=BROWSER_TIMEOUT)
            
            title = await page.title()
            current_url = page.url
            
            return {
                "status": "success",
                "url": current_url,
                "title": title
            }
        except Exception as e:
            logger.error(f"Navigate error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """点击元素"""
        try:
            page = await self.ensure_browser()
            self._new_tab_info = None
            
            try:
                await page.click(selector, timeout=timeout)
            except:
                await page.click(f"text={selector}", timeout=timeout)
            
            await asyncio.sleep(0.5)
            
            result = {"status": "success", "url": self._page.url}
            
            if self._new_tab_info:
                result["new_tab"] = self._new_tab_info
                self._new_tab_info = None
            
            return result
        except Exception as e:
            logger.error(f"Click error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def type_text(self, selector: str, text: str, clear: bool = True) -> Dict[str, Any]:
        """输入文本"""
        try:
            page = await self.ensure_browser()
            
            if clear:
                await page.fill(selector, text, timeout=BROWSER_TIMEOUT)
            else:
                await page.type(selector, text, timeout=BROWSER_TIMEOUT)
            
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Type error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def screenshot(self, full_page: bool = False) -> Dict[str, Any]:
        """截图"""
        try:
            page = await self.ensure_browser()
            screenshot_bytes = await page.screenshot(full_page=full_page)
            
            import base64
            return {
                "status": "success",
                "data": base64.b64encode(screenshot_bytes).decode('utf-8')
            }
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def content(self) -> Dict[str, Any]:
        """获取页面内容"""
        try:
            page = await self.ensure_browser()
            html = await page.content()
            return {
                "status": "success",
                "html": html,
                "url": page.url,
                "title": await page.title()
            }
        except Exception as e:
            logger.error(f"Content error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up browser...")
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()


class VMServer:
    """VM HTTP 服务器"""
    
    def __init__(self):
        self.browser = BrowserManager()
        self.app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        # Health check
        self.app.router.add_get('/health', self.health)
        
        # Browser routes
        self.app.router.add_post('/api/browser/navigate', self.browser_navigate)
        self.app.router.add_post('/api/browser/click', self.browser_click)
        self.app.router.add_post('/api/browser/type', self.browser_type)
        self.app.router.add_post('/api/browser/screenshot', self.browser_screenshot)
        self.app.router.add_post('/api/browser/content', self.browser_content)
        self.app.router.add_post('/api/browser/scroll', self.browser_scroll)
        self.app.router.add_post('/api/browser/evaluate', self.browser_evaluate)
        
        # Desktop routes
        self.app.router.add_post('/api/desktop/screenshot', self.desktop_screenshot)
        self.app.router.add_post('/api/desktop/mouse', self.desktop_mouse)
        self.app.router.add_post('/api/desktop/keyboard', self.desktop_keyboard)
        
        # Shell routes
        self.app.router.add_post('/api/shell/command', self.shell_command)
        
        # File routes
        self.app.router.add_post('/api/file/read', self.file_read)
        self.app.router.add_post('/api/file/write', self.file_write)
        self.app.router.add_post('/api/file/list', self.file_list)
    
    async def health(self, request):
        """健康检查"""
        return web.json_response({"status": "healthy", "service": "novaic-vm-server"})
    
    async def browser_navigate(self, request):
        """浏览器导航"""
        try:
            data = await request.json()
            url = data.get('url')
            if not url:
                return web.json_response({"status": "error", "error": "Missing url"}, status=400)
            
            result = await self.browser.navigate(url)
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Navigate handler error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def browser_click(self, request):
        """浏览器点击"""
        try:
            data = await request.json()
            selector = data.get('selector')
            if not selector:
                return web.json_response({"status": "error", "error": "Missing selector"}, status=400)
            
            result = await self.browser.click(selector)
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Click handler error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def browser_type(self, request):
        """浏览器输入"""
        try:
            data = await request.json()
            selector = data.get('selector')
            text = data.get('text')
            if not selector or text is None:
                return web.json_response({"status": "error", "error": "Missing selector or text"}, status=400)
            
            result = await self.browser.type_text(selector, text, data.get('clear', True))
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Type handler error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def browser_screenshot(self, request):
        """浏览器截图"""
        try:
            data = await request.json() if request.body_exists else {}
            result = await self.browser.screenshot(data.get('full_page', False))
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Screenshot handler error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def browser_content(self, request):
        """获取页面内容"""
        try:
            result = await self.browser.content()
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Content handler error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def browser_scroll(self, request):
        """浏览器滚动"""
        try:
            data = await request.json()
            direction = data.get('direction', 'down')
            amount = data.get('amount', 500)
            page = await self.browser.ensure_browser()
            
            delta_x, delta_y = 0, 0
            if direction == "down":
                delta_y = amount
            elif direction == "up":
                delta_y = -amount
            elif direction == "right":
                delta_x = amount
            elif direction == "left":
                delta_x = -amount
            
            await page.evaluate(f"window.scrollBy({delta_x}, {delta_y})")
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def browser_evaluate(self, request):
        """执行 JavaScript"""
        try:
            data = await request.json()
            script = data.get('script')
            if not script:
                return web.json_response({"status": "error", "error": "Missing script"}, status=400)
            
            page = await self.browser.ensure_browser()
            result = await page.evaluate(script)
            return web.json_response({"status": "success", "data": result})
        except Exception as e:
            logger.error(f"Evaluate error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    # ==================== Desktop Tools ====================
    
    async def desktop_screenshot(self, request):
        """桌面截图"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                temp_path = f.name
            
            # 设置 DISPLAY 环境变量
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            
            # 使用 scrot 截图
            result = subprocess.run(["scrot", "-p", "-o", temp_path], capture_output=True, timeout=10, env=env)
            if result.returncode != 0:
                # Fallback to import
                result = subprocess.run(["import", "-window", "root", temp_path], capture_output=True, timeout=10, env=env)
            
            if result.returncode != 0:
                os.unlink(temp_path)
                return web.json_response({"status": "error", "error": "Screenshot failed"}, status=500)
            
            with open(temp_path, "rb") as f:
                screenshot_bytes = f.read()
            os.unlink(temp_path)
            
            return web.json_response({
                "status": "success",
                "data": base64.b64encode(screenshot_bytes).decode('utf-8')
            })
        except Exception as e:
            logger.error(f"Desktop screenshot error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def desktop_mouse(self, request):
        """鼠标操作"""
        try:
            data = await request.json()
            action = data.get('action')
            if not action:
                return web.json_response({"status": "error", "error": "Missing action"}, status=400)
            
            # 简化实现：直接执行 xdotool 命令
            if action == "click":
                x = data.get('x')
                y = data.get('y')
                if x is None or y is None:
                    return web.json_response({"status": "error", "error": "Missing x or y"}, status=400)
                cmd = ["xdotool", "mousemove", str(x), str(y), "click", "1"]
            elif action == "move":
                x = data.get('x')
                y = data.get('y')
                if x is None or y is None:
                    return web.json_response({"status": "error", "error": "Missing x or y"}, status=400)
                cmd = ["xdotool", "mousemove", str(x), str(y)]
            else:
                return web.json_response({"status": "error", "error": f"Unsupported action: {action}"}, status=400)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return web.json_response({"status": "error", "error": result.stderr}, status=500)
            
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Mouse error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def desktop_keyboard(self, request):
        """键盘操作"""
        try:
            data = await request.json()
            action = data.get('action')
            if not action:
                return web.json_response({"status": "error", "error": "Missing action"}, status=400)
            
            if action == "type":
                text = data.get('text')
                if not text:
                    return web.json_response({"status": "error", "error": "Missing text"}, status=400)
                cmd = ["xdotool", "type", "--clearmodifiers", text]
            elif action == "key":
                keys = data.get('keys', [])
                if not keys:
                    return web.json_response({"status": "error", "error": "Missing keys"}, status=400)
                combo = "+".join(keys)
                cmd = ["xdotool", "key", combo]
            else:
                return web.json_response({"status": "error", "error": f"Unsupported action: {action}"}, status=400)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return web.json_response({"status": "error", "error": result.stderr}, status=500)
            
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"Keyboard error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    # ==================== Shell Tools ====================
    
    async def shell_command(self, request):
        """执行 Shell 命令"""
        try:
            data = await request.json()
            command = data.get('command')
            if not command:
                return web.json_response({"status": "error", "error": "Missing command"}, status=400)
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                return web.json_response({
                    "status": "success",
                    "data": {
                        "stdout": stdout.decode('utf-8', errors='replace'),
                        "stderr": stderr.decode('utf-8', errors='replace'),
                        "exit_code": process.returncode
                    }
                })
            except asyncio.TimeoutError:
                process.terminate()
                return web.json_response({"status": "error", "error": "Command timeout"}, status=500)
        except Exception as e:
            logger.error(f"Shell command error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    # ==================== File Tools ====================
    
    async def file_read(self, request):
        """读取文件"""
        try:
            data = await request.json()
            path = data.get('path')
            if not path:
                return web.json_response({"status": "error", "error": "Missing path"}, status=400)
            
            path = os.path.expanduser(path)
            if not os.path.exists(path):
                return web.json_response({"status": "error", "error": f"File not found: {path}"}, status=404)
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return web.json_response({"status": "success", "data": content})
        except Exception as e:
            logger.error(f"File read error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def file_write(self, request):
        """写入文件"""
        try:
            data = await request.json()
            path = data.get('path')
            content = data.get('content')
            if not path or content is None:
                return web.json_response({"status": "error", "error": "Missing path or content"}, status=400)
            
            path = os.path.expanduser(path)
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return web.json_response({"status": "success"})
        except Exception as e:
            logger.error(f"File write error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def file_list(self, request):
        """列出目录"""
        try:
            data = await request.json() if request.body_exists else {}
            path = data.get('path', '.')
            path = os.path.expanduser(path)
            
            if not os.path.exists(path):
                return web.json_response({"status": "error", "error": f"Path not found: {path}"}, status=404)
            
            if not os.path.isdir(path):
                return web.json_response({"status": "error", "error": f"Not a directory: {path}"}, status=400)
            
            entries = []
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                try:
                    stat_info = os.stat(full_path)
                    entries.append({
                        "name": name,
                        "type": "directory" if os.path.isdir(full_path) else "file",
                        "size": stat_info.st_size
                    })
                except:
                    entries.append({"name": name, "type": "unknown"})
            
            entries.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            return web.json_response({"status": "success", "data": entries})
        except Exception as e:
            logger.error(f"File list error: {e}")
            return web.json_response({"status": "error", "error": str(e)}, status=500)
    
    async def start(self):
        """启动服务"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        logger.info(f"✓ NovAIC VM Server started on http://0.0.0.0:{PORT}")
        logger.info(f"  Health: http://0.0.0.0:{PORT}/health")
        logger.info(f"  Browser: /api/browser/* (navigate, click, type, screenshot, scroll, evaluate)")
        logger.info(f"  Desktop: /api/desktop/* (screenshot, mouse, keyboard)")
        logger.info(f"  Shell: /api/shell/* (command)")
        logger.info(f"  Files: /api/file/* (read, write, list)")
        
        # 保持运行
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self.browser.cleanup()
            await runner.cleanup()


def main():
    """主函数"""
    server = VMServer()
    
    # 信号处理
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        loop.stop()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        loop.run_until_complete(server.start())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
