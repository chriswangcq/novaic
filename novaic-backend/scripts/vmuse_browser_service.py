#!/opt/novaic/venv/bin/python3
"""
VMUSE 浏览器服务 - 基于原始 VMUSE 实现，去掉 fastmcp 依赖

这是一个守护进程，保持浏览器持久运行。
使用 Unix Socket 接收命令。

Socket 路径: /tmp/novaic-browser-service.sock
"""

import os
import sys
import json
import socket
import signal
import atexit
import asyncio
import logging
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, BrowserContext

# 配置
SOCKET_PATH = "/tmp/novaic-browser-service.sock"
USER_DATA_DIR = "/home/ubuntu/.config/chromium"  # 与系统 chromium 共享
PID_FILE = "/tmp/novaic-browser-service.pid"
BROWSER_TIMEOUT = 30000  # ms

# 日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class BrowserService:
    """基于 VMUSE 的浏览器服务"""
    
    def __init__(self):
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._new_tab_info: Optional[Dict[str, Any]] = None
        self.socket = None
        self.running = False
    
    def _on_new_page(self, page: Page):
        """当打开新标签页时的回调"""
        self._new_tab_info = {
            "url": page.url,
            "message": f"New tab opened: {page.url}"
        }
        # 自动切换到新标签页
        self._page = page
        logger.info(f"New tab opened and switched: {page.url}")
    
    async def _ensure_browser(self) -> Page:
        """确保浏览器运行并返回页面（使用持久化上下文保留登录数据）"""
        if self._page is not None:
            return self._page
        
        if self._playwright is None:
            logger.info("启动 Playwright...")
            self._playwright = await async_playwright().start()
        
        if self._context is None:
            # 确保用户数据目录存在
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            
            # 使用 launch_persistent_context 共享登录数据
            # 警告：不能同时运行系统 chromium 和 Playwright（锁冲突）
            logger.info(f"Using persistent user data: {USER_DATA_DIR}")
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,  # 可见
                viewport={"width": 1280, "height": 720},
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            # 监听新标签页
            self._context.on("page", self._on_new_page)
            logger.info("✓ 浏览器已启动")
        
        # 获取现有页面或创建新页面
        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()
        
        return self._page
    
    async def handle_command(self, command: str, args: dict) -> dict:
        """处理浏览器命令"""
        try:
            page = await self._ensure_browser()
            
            if command == "navigate":
                url = args.get("url")
                wait_until = args.get("wait_until", "load")
                
                if not url:
                    return {"status": "error", "error": "Missing 'url' parameter"}
                
                await page.goto(url, wait_until=wait_until, timeout=BROWSER_TIMEOUT)
                
                # 获取页面信息
                title = await page.title()
                current_url = page.url
                
                # 获取简化的 HTML 结构
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
                    "status": "success",
                    "url": current_url,
                    "title": title,
                    "structure": html_content
                }
            
            elif command == "click":
                selector = args.get("selector")
                timeout = args.get("timeout", 5000)
                
                if not selector:
                    return {"status": "error", "error": "Missing 'selector' parameter"}
                
                self._new_tab_info = None  # 重置新标签页跟踪
                
                # 尝试不同的选择器策略
                try:
                    await page.click(selector, timeout=timeout)
                except:
                    # 尝试按文本查找
                    await page.click(f"text={selector}", timeout=timeout)
                
                # 等待任何导航或网络活动
                await asyncio.sleep(0.5)
                
                result = {"status": "success", "url": self._page.url}
                
                # 如果打开了新标签页，包含信息
                if self._new_tab_info:
                    result["new_tab"] = self._new_tab_info
                    result["note"] = "A new tab was opened and is now active"
                    self._new_tab_info = None
                
                return result
            
            elif command == "type":
                selector = args.get("selector")
                text = args.get("text")
                clear = args.get("clear", True)
                
                if not selector:
                    return {"status": "error", "error": "Missing 'selector' parameter"}
                if text is None:
                    return {"status": "error", "error": "Missing 'text' parameter"}
                
                if clear:
                    await page.fill(selector, text, timeout=BROWSER_TIMEOUT)
                else:
                    await page.type(selector, text, timeout=BROWSER_TIMEOUT)
                
                return {"status": "success"}
            
            elif command == "screenshot":
                full_page = args.get("full_page", False)
                
                screenshot_bytes = await page.screenshot(full_page=full_page)
                
                return {
                    "status": "success",
                    "screenshot": base64.b64encode(screenshot_bytes).decode('utf-8')
                }
            
            elif command == "content":
                html = await page.content()
                return {
                    "status": "success",
                    "html": html,
                    "url": page.url,
                    "title": await page.title()
                }
            
            elif command == "status":
                # 返回服务状态
                return {
                    "status": "success",
                    "browser_running": self._context is not None,
                    "current_url": page.url if page else None,
                    "current_title": await page.title() if page else None
                }
            
            elif command == "shutdown":
                # 关闭服务
                self.running = False
                return {"status": "success", "message": "Service shutting down"}
            
            else:
                return {"status": "error", "error": f"Unknown command: {command}"}
        
        except Exception as e:
            logger.error(f"命令执行失败: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def handle_connection(self, reader, writer):
        """处理客户端连接"""
        try:
            # 接收命令
            data = await reader.read(4096)
            if not data:
                writer.close()
                await writer.wait_closed()
                return
            
            try:
                request = json.loads(data.decode('utf-8'))
                command = request.get("command")
                args = request.get("args", {})
                
                logger.info(f"收到命令: {command}({args.get('url', '')})")
                
                # 处理命令
                result = await self.handle_command(command, args)
                
                # 发送响应
                response = json.dumps(result) + "\n"
                writer.write(response.encode('utf-8'))
                await writer.drain()
                
            except json.JSONDecodeError as e:
                error_response = json.dumps({
                    "status": "error",
                    "error": f"Invalid JSON: {e}"
                }) + "\n"
                writer.write(error_response.encode('utf-8'))
                await writer.drain()
        
        except Exception as e:
            logger.error(f"处理连接失败: {e}")
        
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        
        # 删除 socket 文件
        if Path(SOCKET_PATH).exists():
            try:
                Path(SOCKET_PATH).unlink()
            except:
                pass
        
        # 删除 PID 文件
        if Path(PID_FILE).exists():
            try:
                Path(PID_FILE).unlink()
            except:
                pass
        
        logger.info("清理完成")
    
    async def start(self):
        """启动服务"""
        # 清理旧的 socket
        if Path(SOCKET_PATH).exists():
            Path(SOCKET_PATH).unlink()
        
        # 保存 PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        # 创建 Unix Socket 服务器
        server = await asyncio.start_unix_server(
            self.handle_connection,
            path=SOCKET_PATH
        )
        
        # 设置权限
        os.chmod(SOCKET_PATH, 0o666)
        
        logger.info(f"✓ VMUSE 浏览器服务已启动")
        logger.info(f"  PID: {os.getpid()}")
        logger.info(f"  Socket: {SOCKET_PATH}")
        
        # 注册清理函数
        atexit.register(self.cleanup)
        
        self.running = True
        
        # 启动服务器
        async with server:
            await server.serve_forever()


def main():
    """主函数"""
    service = BrowserService()
    
    # 信号处理
    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，准备退出...")
        service.running = False
        service.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 运行服务
        asyncio.run(service.start())
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    except Exception as e:
        logger.error(f"服务异常: {e}", exc_info=True)
        sys.exit(1)
    finally:
        service.cleanup()


if __name__ == "__main__":
    main()
