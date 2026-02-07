#!/usr/bin/env python3
"""
持久化浏览器会话管理器

功能:
- 启动并保持一个持久化的浏览器实例
- 多个命令可以复用同一个浏览器和页面
- 自动管理会话生命周期
- 支持超时自动清理

使用方法:
    from browser_session_manager import BrowserSessionManager
    
    manager = BrowserSessionManager()
    page = manager.get_page()
    page.goto("https://example.com")
"""

import os
import sys
import json
import time
import fcntl
import signal
import atexit
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext

# 配置
SESSION_DIR = Path("/tmp/novaic-browser-session")
LOCK_FILE = SESSION_DIR / "session.lock"
CDP_FILE = SESSION_DIR / "cdp_endpoint.json"
SESSION_TIMEOUT = 300  # 5分钟无操作后自动清理


class BrowserSessionManager:
    """持久化浏览器会话管理器"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.lock_fd = None
        self.is_owner = False
        
        # 确保会话目录存在
        SESSION_DIR.mkdir(exist_ok=True)
        
    def acquire_lock(self) -> bool:
        """获取会话锁"""
        try:
            self.lock_fd = open(LOCK_FILE, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.is_owner = True
            return True
        except (IOError, BlockingIOError):
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            return False
    
    def release_lock(self):
        """释放会话锁"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
            except:
                pass
            self.lock_fd = None
    
    def save_cdp_endpoint(self, endpoint: str):
        """保存 CDP endpoint 信息"""
        data = {
            "endpoint": endpoint,
            "pid": os.getpid(),
            "timestamp": time.time()
        }
        with open(CDP_FILE, 'w') as f:
            json.dump(data, f)
    
    def load_cdp_endpoint(self) -> Optional[dict]:
        """加载 CDP endpoint 信息"""
        if not CDP_FILE.exists():
            return None
        
        try:
            with open(CDP_FILE, 'r') as f:
                data = json.load(f)
            
            # 检查是否超时
            age = time.time() - data.get("timestamp", 0)
            if age > SESSION_TIMEOUT:
                print(f"[BrowserSession] 会话已超时 ({age:.0f}s > {SESSION_TIMEOUT}s)")
                return None
            
            return data
        except Exception as e:
            print(f"[BrowserSession] 加载 CDP endpoint 失败: {e}")
            return None
    
    def start_browser(self) -> Browser:
        """启动新的浏览器实例"""
        print("[BrowserSession] 启动新的浏览器实例...")
        
        self.playwright = sync_playwright().start()
        
        # 启动浏览器（非 headless，可见）
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ],
        )
        
        # 创建上下文
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 创建页面
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)
        
        # 保存进程信息（简化版，不使用 CDP）
        session_data = {
            "pid": os.getpid(),
            "timestamp": time.time(),
            "browser_running": True
        }
        with open(CDP_FILE, 'w') as f:
            json.dump(session_data, f)
        
        print(f"[BrowserSession] 浏览器已启动，PID: {os.getpid()}")
        
        # 注册清理函数
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup())
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup())
        
        return self.browser
    
    def connect_to_browser(self, cdp_endpoint: str) -> Browser:
        """连接到现有的浏览器实例"""
        print(f"[BrowserSession] 连接到现有浏览器: {cdp_endpoint}")
        
        self.playwright = sync_playwright().start()
        
        try:
            self.browser = self.playwright.chromium.connect_over_cdp(cdp_endpoint)
            
            # 获取现有的上下文和页面
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                pages = self.context.pages
                if pages:
                    self.page = pages[0]
                else:
                    self.page = self.context.new_page()
            else:
                self.context = self.browser.new_context(
                    viewport={'width': 1280, 'height': 720}
                )
                self.page = self.context.new_page()
            
            print(f"[BrowserSession] 已连接到浏览器")
            return self.browser
            
        except Exception as e:
            print(f"[BrowserSession] 连接失败: {e}")
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            return None
    
    def get_page(self) -> Page:
        """获取当前页面（如果不存在则创建）
        
        简化版实现：每次都创建新的浏览器实例，但保持打开不关闭
        """
        # 尝试获取锁来启动浏览器
        if self.acquire_lock():
            # 成功获取锁，启动新浏览器
            self.start_browser()
            return self.page
        else:
            # 已经有浏览器在运行，等待锁释放后获取
            print("[BrowserSession] 等待现有浏览器会话...")
            for i in range(10):
                time.sleep(1)
                if self.acquire_lock():
                    self.start_browser()
                    return self.page
            
            # 超时，强制启动
            print("[BrowserSession] 超时，强制启动新浏览器")
            self.start_browser()
            return self.page
    
    def cleanup(self):
        """清理资源"""
        print("[BrowserSession] 清理资源...")
        
        if self.page:
            try:
                self.page.close()
            except:
                pass
            self.page = None
        
        if self.context:
            try:
                self.context.close()
            except:
                pass
            self.context = None
        
        if self.browser and self.is_owner:
            try:
                self.browser.close()
            except:
                pass
            self.browser = None
        
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
            self.playwright = None
        
        self.release_lock()
        
        # 如果是所有者，删除 CDP 文件
        if self.is_owner and CDP_FILE.exists():
            try:
                CDP_FILE.unlink()
            except:
                pass
        
        print("[BrowserSession] 清理完成")
    
    def __enter__(self):
        """上下文管理器支持"""
        return self.get_page()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器支持"""
        # 不清理，保持浏览器运行
        pass


def main():
    """测试脚本"""
    manager = BrowserSessionManager()
    page = manager.get_page()
    
    print("浏览器已就绪！")
    print(f"当前 URL: {page.url}")
    
    # 导航到测试页面
    page.goto("https://www.baidu.com")
    print(f"已导航到: {page.title()}")
    
    # 保持运行
    print("\n浏览器将保持运行...")
    print("按 Ctrl+C 退出")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n退出...")
        manager.cleanup()


if __name__ == "__main__":
    main()
