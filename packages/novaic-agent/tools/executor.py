"""
Tool Executor - 调用 Executor API 执行操作

通过 HTTP 调用 Executor 服务，不在 Agent 本地执行。
Executor 服务负责实际的 Shell/Browser/Screen/Input 操作。
"""

from typing import Dict, Any, Optional
import httpx

from config import settings


class ToolExecutor:
    """
    工具执行器 - 调用 Executor API
    """
    
    def __init__(self):
        self.executor_url = settings.executor_url
        self._client: Optional[httpx.AsyncClient] = None
        
        # 工具映射
        self._tools = {
            # Shell
            "run_command": self._run_command,
            "run_python": self._run_python,
            # File
            "read_file": self._read_file,
            "write_file": self._write_file,
            "list_files": self._list_files,
            # Browser
            "browser_navigate": self._browser_navigate,
            "browser_click": self._browser_click,
            "browser_type": self._browser_type,
            "browser_scroll": self._browser_scroll,
            "browser_screenshot": self._browser_screenshot,
            "browser_eval": self._browser_eval,
            "browser_get_tabs": self._browser_get_tabs,
            "browser_switch_tab": self._browser_switch_tab,
            "browser_close_tab": self._browser_close_tab,
            # Screen & Input
            "screenshot": self._screenshot,
            "mouse": self._mouse,
            "keyboard": self._keyboard,
        }
        
        # 浏览器会话 ID（懒创建）
        self._browser_session_id = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            # 禁用连接池复用，避免缓存失败的连接
            self._client = httpx.AsyncClient(
                timeout=60.0,
                limits=httpx.Limits(max_keepalive_connections=0)  # 不保持连接
            )
        return self._client
    
    async def _reset_client(self):
        """重置 HTTP 客户端（连接失败时调用）"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        if tool_name not in self._tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        handler = self._tools[tool_name]
        return await handler(tool_input)
    
    def interrupt(self) -> None:
        """中断执行"""
        # 关闭浏览器会话
        self._browser_session_id = None
    
    async def health_check(self) -> Dict[str, Any]:
        """检查 Executor 健康状态"""
        try:
            client = await self._get_client()
            resp = await client.get(f"{self.executor_url}/health")
            return {"healthy": resp.status_code == 200, "data": resp.json()}
        except Exception as e:
            # 连接失败时重置客户端
            await self._reset_client()
            return {"healthy": False, "error": str(e)}
    
    # ==================== Shell ====================
    
    async def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Shell 命令"""
        from config import settings
        
        try:
            client = await self._get_client()
            
            # 检查是否为后台运行模式
            background = params.get("background", False)
            
            # 构建请求参数 - visible 默认值从配置读取
            request_json = {
                "cmd": params.get("command", ""),
                "cwd": params.get("cwd"),
                "timeout": params.get("timeout", 60),
                "visible": params.get("visible", settings.visible_shell),  # 默认从配置读取
                "background": background  # 后台运行模式
            }
            
            # 后台模式使用较短的超时时间（命令会立即返回）
            http_timeout = 10.0 if background else 120.0
            
            resp = await client.post(
                f"{self.executor_url}/api/exec",
                json=request_json,
                timeout=http_timeout
            )
            return resp.json()
        except Exception as e:
            await self._reset_client()
            return {"success": False, "error": str(e)}
    
    async def _run_python(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Python 代码"""
        code = params.get("code", "")
        visible = params.get("visible", False)  # 是否在 GUI 中可见执行（用于游戏、GUI 程序等）
        
        # 使用 python3 -c 执行
        escaped_code = code.replace("'", "'\"'\"'")  # 转义单引号
        return await self._run_command({
            "command": f"python3 -c '{escaped_code}'",
            "visible": visible
        })
    
    # ==================== File ====================
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """读取文件"""
        path = params.get("path", "")
        # 转义路径中的特殊字符
        escaped_path = path.replace("'", "'\"'\"'")
        return await self._run_command({"command": f"cat '{escaped_path}'"})
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """写入文件"""
        path = params.get("path", "")
        content = params.get("content", "")
        
        # 确保目录存在
        dir_cmd = f"mkdir -p $(dirname '{path}')"
        
        # 使用 heredoc 写入，避免引号问题
        write_cmd = f"cat > '{path}' << 'NBCC_EOF'\n{content}\nNBCC_EOF"
        
        # 组合命令
        cmd = f"{dir_cmd} && {write_cmd}"
        return await self._run_command({"command": cmd})
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """列出文件"""
        path = params.get("path", ".")
        escaped_path = path.replace("'", "'\"'\"'")
        return await self._run_command({"command": f"ls -la '{escaped_path}'"})
    
    # ==================== Browser ====================
    
    async def _ensure_browser_session(self) -> Optional[str]:
        """
        确保浏览器会话存在
        使用默认会话以保持登录状态
        """
        # 先尝试获取/复用默认会话
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.executor_url}/api/browser/session/default",
                timeout=30.0  # 浏览器启动可能需要更长时间
            )
            if resp.status_code == 200:
                data = resp.json()
                self._browser_session_id = data.get("session_id")
                reused = data.get("reused", False)
                if reused:
                    print(f"[ToolExecutor] Reusing existing browser session: {self._browser_session_id}")
                else:
                    print(f"[ToolExecutor] Created new default browser session: {self._browser_session_id}")
                return self._browser_session_id
        except Exception as e:
            print(f"[ToolExecutor] Failed to get default session: {e}")
            # 连接失败时重置客户端
            await self._reset_client()
        
        # 如果有缓存的会话 ID，验证它
        if self._browser_session_id:
            try:
                client = await self._get_client()  # 重新获取客户端
                resp = await client.get(
                    f"{self.executor_url}/api/browser/session/{self._browser_session_id}/state"
                )
                if resp.status_code == 200:
                    return self._browser_session_id
            except Exception:
                await self._reset_client()
            self._browser_session_id = None
        
        # 创建新会话（fallback）
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/browser/session",
                json={"name": "default"},
                timeout=30.0
            )
            data = resp.json()
            self._browser_session_id = data.get("session_id")
            print(f"[ToolExecutor] Created browser session: {self._browser_session_id}")
            return self._browser_session_id
        except Exception as e:
            print(f"[ToolExecutor] Failed to create browser session: {e}")
            await self._reset_client()
            return None
    
    async def _browser_navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """导航到 URL"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "Failed to create browser session"}
        
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/browser/session/{session_id}/navigate",
                json={"url": params.get("url", "")}
            )
            result = resp.json()
            
            # 导航后自动获取页面状态
            if result.get("success"):
                state_resp = await client.get(
                    f"{self.executor_url}/api/browser/session/{session_id}/state"
                )
                if state_resp.status_code == 200:
                    state_data = state_resp.json()
                    result["page_state"] = state_data.get("observation", {})
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """点击元素 - 支持 element_id（推荐）或 selector"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            
            # 优先使用 element_id
            if "element_id" in params and params["element_id"] is not None:
                resp = await client.post(
                    f"{self.executor_url}/api/browser/session/{session_id}/click_by_id",
                    json={"element_id": params["element_id"]}
                )
            else:
                # fallback to selector
                resp = await client.post(
                    f"{self.executor_url}/api/browser/session/{session_id}/click",
                    json={"selector": params.get("selector", "")}
                )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """输入文本 - 支持 element_id（推荐）或 selector"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            
            # 优先使用 element_id
            if "element_id" in params and params["element_id"] is not None:
                resp = await client.post(
                    f"{self.executor_url}/api/browser/session/{session_id}/type_by_id",
                    json={
                        "element_id": params["element_id"],
                        "text": params.get("text", "")
                    }
                )
            else:
                # fallback to selector
                resp = await client.post(
                    f"{self.executor_url}/api/browser/session/{session_id}/type",
                    json={
                        "selector": params.get("selector", ""),
                        "text": params.get("text", "")
                    }
                )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_scroll(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """滚动页面"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/browser/session/{session_id}/scroll",
                json={
                    "direction": params.get("direction", "down"),
                    "amount": params.get("amount", 500)
                }
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """浏览器截图"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/browser/session/{session_id}/screenshot",
                json={"full_page": params.get("full_page", False)}
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_eval(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行 JavaScript"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/browser/session/{session_id}/eval",
                json={"script": params.get("script", "")}
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_get_tabs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取所有浏览器标签页"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self.executor_url}/api/browser/session/{session_id}/tabs"
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_switch_tab(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """切换到指定标签页"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/browser/session/{session_id}/switch_tab",
                json={"index": params.get("index")}
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _browser_close_tab(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """关闭指定标签页"""
        session_id = await self._ensure_browser_session()
        if not session_id:
            return {"success": False, "error": "No browser session"}
        
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/browser/session/{session_id}/close_tab",
                json={"index": params.get("index")}
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== Screen & Input ====================
    
    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """桌面截图"""
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/screen/screenshot",
                json=params or {}
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _mouse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """鼠标操作"""
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/input/mouse",
                json=params
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _keyboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """键盘操作"""
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.executor_url}/api/input/keyboard",
                json=params
            )
            return resp.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self) -> None:
        """关闭资源"""
        if self._client:
            await self._client.aclose()
            self._client = None
