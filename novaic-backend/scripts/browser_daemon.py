#!/opt/novaic/venv/bin/python3
"""
浏览器守护进程

功能：
- 在后台保持运行
- 监听 Unix Socket 接收命令
- 维护一个持久化的浏览器实例

Socket 路径: /tmp/novaic-browser-daemon.sock

协议:
  发送: {"command": "navigate", "args": {"url": "..."}}
  接收: {"status": "success", ...}
"""

import os
import sys
import json
import socket
import signal
import atexit
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Page

# 配置
SOCKET_PATH = "/tmp/novaic-browser-daemon.sock"
USER_DATA_DIR = "/tmp/novaic-browser-userdata"
PID_FILE = "/tmp/novaic-browser-daemon.pid"

# 日志
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class BrowserDaemon:
    """浏览器守护进程"""
    
    def __init__(self):
        self.playwright = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.socket = None
        self.running = False
    
    def start_browser(self):
        """启动持久化浏览器"""
        if self.playwright is None:
            logger.info("启动 Playwright...")
            self.playwright = sync_playwright().start()
        
        if self.context is None:
            # 确保用户数据目录存在
            Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"启动持久化浏览器: {USER_DATA_DIR}")
            
            # 使用 launch_persistent_context
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False,  # 可见
                viewport={"width": 1280, "height": 720},
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            
            logger.info("✓ 浏览器已启动")
        
        # 获取或创建页面
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        
        self.page.set_default_timeout(30000)
        
        return self.page
    
    def handle_command(self, command: str, args: dict) -> dict:
        """处理命令"""
        try:
            page = self.start_browser()
            
            if command == "navigate":
                url = args.get("url")
                if not url:
                    return {"status": "error", "error": "Missing 'url' parameter"}
                
                response = page.goto(url, wait_until="domcontentloaded")
                return {
                    "status": "success",
                    "url": page.url,
                    "title": page.title(),
                    "status_code": response.status if response else None
                }
            
            elif command == "click":
                selector = args.get("selector")
                if not selector:
                    return {"status": "error", "error": "Missing 'selector' parameter"}
                
                page.click(selector)
                return {"status": "success", "url": page.url}
            
            elif command == "type":
                selector = args.get("selector")
                text = args.get("text")
                if not selector or text is None:
                    return {"status": "error", "error": "Missing parameters"}
                
                page.fill(selector, text)
                return {"status": "success", "url": page.url}
            
            elif command == "screenshot":
                screenshot_bytes = page.screenshot(full_page=False)
                import base64
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                return {
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
            
            elif command == "content":
                html = page.content()
                return {
                    "status": "success",
                    "html": html,
                    "url": page.url,
                    "title": page.title()
                }
            
            elif command == "status":
                # 返回浏览器状态
                return {
                    "status": "success",
                    "browser_running": self.context is not None,
                    "current_url": page.url if page else None
                }
            
            elif command == "shutdown":
                # 关闭守护进程
                self.running = False
                return {"status": "success", "message": "Daemon shutting down"}
            
            else:
                return {"status": "error", "error": f"Unknown command: {command}"}
        
        except Exception as e:
            logger.error(f"命令执行失败: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        if self.context:
            try:
                self.context.close()
            except:
                pass
        
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        
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
    
    def start(self):
        """启动守护进程"""
        # 清理旧的 socket
        if Path(SOCKET_PATH).exists():
            Path(SOCKET_PATH).unlink()
        
        # 保存 PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        # 创建 Unix Socket
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(SOCKET_PATH)
        self.socket.listen(5)
        
        # 设置权限
        os.chmod(SOCKET_PATH, 0o666)
        
        logger.info(f"✓ 守护进程已启动")
        logger.info(f"  PID: {os.getpid()}")
        logger.info(f"  Socket: {SOCKET_PATH}")
        
        # 注册清理函数
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup() or sys.exit(0))
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup() or sys.exit(0))
        
        self.running = True
        
        # 主循环
        while self.running:
            try:
                conn, addr = self.socket.accept()
                
                # 接收命令
                data = conn.recv(4096).decode('utf-8')
                if not data:
                    conn.close()
                    continue
                
                try:
                    request = json.loads(data)
                    command = request.get("command")
                    args = request.get("args", {})
                    
                    logger.info(f"收到命令: {command}")
                    
                    # 处理命令
                    result = self.handle_command(command, args)
                    
                    # 发送响应
                    response = json.dumps(result) + "\n"
                    conn.sendall(response.encode('utf-8'))
                    
                except json.JSONDecodeError as e:
                    error_response = json.dumps({
                        "status": "error",
                        "error": f"Invalid JSON: {e}"
                    }) + "\n"
                    conn.sendall(error_response.encode('utf-8'))
                
                conn.close()
                
            except Exception as e:
                logger.error(f"处理连接失败: {e}")
        
        self.cleanup()
        logger.info("守护进程已停止")


def main():
    """主函数"""
    daemon = BrowserDaemon()
    
    try:
        daemon.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号")
        daemon.cleanup()
    except Exception as e:
        logger.error(f"守护进程异常: {e}", exc_info=True)
        daemon.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
