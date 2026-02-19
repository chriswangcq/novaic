"""
VMUSE 适配器 - 将 VMUSE MCP 调用适配到 vmcontrol API
提供向后兼容的接口

这个适配器将旧的 VMUSE/FastMCP 工具调用转换为新的 vmcontrol API 调用，
保持接口向后兼容，便于平滑迁移。
"""

import httpx
from typing import Dict, Any, Optional, List
import logging
import json
import shlex
import asyncio
import secrets
import time

from common.config import ServiceConfig
from common.http.clients import internal_async_client

logger = logging.getLogger(__name__)


class AimCache:
    """缓存 aim 位置信息"""
    def __init__(self, ttl_seconds: int = 600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
    
    def create(self, x: int, y: int, zoom: float = 1.0) -> str:
        """创建新的 aim"""
        aim_id = f"aim_{secrets.token_hex(4)}"
        self._cache[aim_id] = {
            "x": x,
            "y": y,
            "zoom": zoom,
            "created_at": time.time()
        }
        return aim_id
    
    def get(self, aim_id: str) -> Optional[Dict[str, Any]]:
        """获取 aim 位置"""
        if aim_id not in self._cache:
            return None
        
        aim = self._cache[aim_id]
        # 检查是否过期
        if time.time() - aim["created_at"] > self._ttl:
            del self._cache[aim_id]
            return None
        
        return aim
    
    def update(self, aim_id: str, delta_x: int = 0, delta_y: int = 0, zoom: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """更新 aim 位置"""
        aim = self.get(aim_id)
        if not aim:
            return None
        
        aim["x"] += delta_x
        aim["y"] += delta_y
        if zoom is not None:
            aim["zoom"] = zoom
        aim["created_at"] = time.time()  # 刷新 TTL
        
        return aim
    
    def clear_expired(self):
        """清理过期的 aim"""
        now = time.time()
        expired = [aid for aid, a in self._cache.items() if now - a["created_at"] > self._ttl]
        for aid in expired:
            del self._cache[aid]


class VmuseAdapter:
    """VMUSE 到 vmcontrol 的适配器
    
    提供与 VMUSE MCP 兼容的接口，底层调用 vmcontrol API。
    支持的工具：
    - browser_navigate: 浏览器导航
    - browser_click: 点击元素
    - browser_type: 输入文本
    - file_read: 读取文件
    - file_write: 写入文件
    - shell_exec: 执行命令
    - screenshot: 截图
    - mouse: 鼠标控制
    - keyboard: 键盘控制
    - list_windows: 列出所有窗口
    - focus_window: 聚焦窗口
    - maximize_window: 最大化窗口
    - minimize_window: 最小化窗口
    - close_window: 关闭窗口
    - resize_window: 调整窗口大小
    - launch_app: 启动应用
    """
    
    def __init__(self, vmcontrol_url: Optional[str] = None, timeout: float = 30.0):
        """
        初始化适配器
        
        Args:
            vmcontrol_url: vmcontrol 服务 URL，默认从配置读取
            timeout: 请求超时时间（秒）
        """
        self.vmcontrol_url = vmcontrol_url or ServiceConfig.VMCONTROL_URL
        self.timeout = timeout
        self.client = internal_async_client(
            base_url=self.vmcontrol_url,
            timeout=timeout,
        )
        self.aim_cache = AimCache(ttl_seconds=600)
        logger.info(f"[VmuseAdapter] Initialized with vmcontrol_url={self.vmcontrol_url}")
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
        logger.debug("[VmuseAdapter] Client closed")

    def _as_text_content(self, payload: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build MCP-style text content for compatibility."""
        return [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        vm_id: str = "1"
    ) -> Dict[str, Any]:
        """
        调用工具（兼容 VMUSE MCP 接口）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            vm_id: VM ID，默认为 "1"
        
        Returns:
            工具执行结果，格式：
            {
                "success": bool,
                "result": Any,  # 成功时的结果
                "error": str    # 失败时的错误信息
            }
        
        Raises:
            httpx.HTTPError: HTTP 请求失败
            ValueError: 不支持的工具
        """
        logger.debug(f"[VmuseAdapter] Calling tool: {tool_name} with args: {arguments}")
        
        try:
            # 浏览器操作
            if tool_name == "browser_navigate":
                return await self._browser_navigate(vm_id, arguments)
            
            elif tool_name == "browser_click":
                return await self._browser_click(vm_id, arguments)
            
            elif tool_name == "browser_type":
                return await self._browser_type(vm_id, arguments)
            
            # 文件操作
            elif tool_name == "file_read":
                return await self._file_read(vm_id, arguments)
            
            elif tool_name == "file_write":
                return await self._file_write(vm_id, arguments)
            
            # Shell 操作
            elif tool_name == "shell_exec":
                return await self._shell_exec(vm_id, arguments)
            
            # 截图
            elif tool_name == "screenshot":
                return await self._screenshot(vm_id, arguments)
            
            # Mouse 工具
            elif tool_name == "mouse":
                return await self._mouse(vm_id, arguments)
            
            # Keyboard 工具
            elif tool_name == "keyboard":
                return await self._keyboard(vm_id, arguments)
            
            # Browser 扩展功能
            elif tool_name == "browser_scroll":
                return await self._browser_scroll(vm_id, arguments)
            
            elif tool_name == "browser_eval":
                return await self._browser_eval(vm_id, arguments)
            
            elif tool_name == "browser_get_tabs":
                return await self._browser_get_tabs(vm_id, arguments)
            
            elif tool_name == "browser_switch_tab":
                return await self._browser_switch_tab(vm_id, arguments)
            
            elif tool_name == "browser_close_tab":
                return await self._browser_close_tab(vm_id, arguments)
            
            elif tool_name == "browser_screenshot":
                return await self._browser_screenshot(vm_id, arguments)
            
            elif tool_name == "browser_content":
                return await self._browser_content(vm_id, arguments)
            
            # Window 工具
            elif tool_name == "list_windows":
                return await self._list_windows(vm_id, arguments)
            
            elif tool_name == "focus_window":
                return await self._focus_window(vm_id, arguments)
            
            elif tool_name == "maximize_window":
                return await self._maximize_window(vm_id, arguments)
            
            elif tool_name == "minimize_window":
                return await self._minimize_window(vm_id, arguments)
            
            elif tool_name == "close_window":
                return await self._close_window(vm_id, arguments)
            
            elif tool_name == "resize_window":
                return await self._resize_window(vm_id, arguments)
            
            elif tool_name == "launch_app":
                return await self._launch_app(vm_id, arguments)
            
            # Context 工具
            elif tool_name == "system_snapshot":
                return await self._system_snapshot(vm_id, arguments)
            
            elif tool_name == "clipboard_get":
                return await self._clipboard_get(vm_id, arguments)
            
            elif tool_name == "clipboard_set":
                return await self._clipboard_set(vm_id, arguments)
            
            elif tool_name == "environment_info":
                return await self._environment_info(vm_id, arguments)
            
            else:
                error_msg = f"Unsupported tool: {tool_name}"
                logger.error(f"[VmuseAdapter] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] HTTP error for {tool_name}: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"[VmuseAdapter] Unexpected error for {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Adapter error: {str(e)}"
            }
    
    # ==================== 浏览器操作 ====================
    
    async def _browser_navigate(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        浏览器导航到 URL - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {"url": "..."}
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            url = arguments.get("url")
            if not url:
                return {
                    "success": False,
                    "error": "Missing required parameter: url",
                    "content": []
                }
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/browser/navigate",
                json={"url": url}
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": result.get("success", True),
                "result": result,
                "content": self._as_text_content(result),
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error: HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Adapter error: {str(e)}",
                "content": []
            }
    
    async def _browser_click(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        点击浏览器元素 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {"selector": "..."}
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            selector = arguments.get("selector")
            if not selector:
                return {
                    "success": False,
                    "error": "Missing required parameter: selector",
                    "content": []
                }
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/browser/click",
                json={"selector": selector}
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": result.get("success", True),
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_type(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        在浏览器元素中输入文本 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {"selector": "...", "text": "..."}
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            selector = arguments.get("selector")
            text = arguments.get("text")
            
            if not selector:
                return {
                    "success": False,
                    "error": "Missing required parameter: selector",
                    "content": []
                }
            if text is None:  # 允许空字符串
                return {
                    "success": False,
                    "error": "Missing required parameter: text",
                    "content": []
                }
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/browser/type",
                json={
                    "selector": selector,
                    "text": text
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": result.get("success", True),
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_scroll(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        滚动浏览器页面 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {"direction": "up|down|left|right", "amount": 100}
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            direction = arguments.get("direction")
            if not direction:
                return {
                    "success": False,
                    "error": "Missing required parameter: direction",
                    "content": []
                }
            
            if direction not in ["up", "down", "left", "right"]:
                return {
                    "success": False,
                    "error": f"Invalid direction: {direction}. Must be one of: up, down, left, right",
                    "content": []
                }
            
            amount = arguments.get("amount", 100)
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/browser/scroll",
                json={
                    "direction": direction,
                    "amount": amount
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": result.get("success", True),
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_eval(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        在浏览器中执行 JavaScript 代码 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {"script": "..."}
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            script = arguments.get("script")
            if not script:
                return {
                    "success": False,
                    "error": "Missing required parameter: script",
                    "content": []
                }
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/browser/eval",
                json={"script": script}
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": result.get("success", True),
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_get_tabs(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取浏览器标签页列表 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {}
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            response = await self.client.get(f"/api/vms/{vm_id}/browser/tabs")
            response.raise_for_status()
            result = response.json()
            
            tabs_info = {
                "tabs": result.get("tabs", []),
                "active_tab": result.get("active_tab", 0)
            }
            
            return {
                "success": True,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(tabs_info, ensure_ascii=False)
                    }
                ]
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_switch_tab(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        切换到指定的浏览器标签页 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {"tab_index": 0}
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            tab_index = arguments.get("tab_index")
            if tab_index is None:
                return {
                    "success": False,
                    "error": "Missing required parameter: tab_index",
                    "content": []
                }
            
            if not isinstance(tab_index, int) or tab_index < 0:
                return {
                    "success": False,
                    "error": f"Invalid tab_index: {tab_index}. Must be a non-negative integer",
                    "content": []
                }
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/browser/tabs/switch",
                json={"tab_index": tab_index}
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": result.get("success", True),
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_close_tab(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        关闭当前或指定的浏览器标签页 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {"tab_index": 0}  # optional
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [{"type": "text", "text": "..."}]
            }
        """
        try:
            tab_index = arguments.get("tab_index")
            
            payload = {}
            if tab_index is not None:
                if not isinstance(tab_index, int) or tab_index < 0:
                    return {
                        "success": False,
                        "error": f"Invalid tab_index: {tab_index}. Must be a non-negative integer",
                        "content": []
                    }
                payload["tab_index"] = tab_index
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/browser/tabs/close",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": result.get("success", True),
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        浏览器截图 - 返回 MCP 标准格式
        
        Args:
            vm_id: VM ID
            arguments: 参数（空）
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [
                    {"type": "text", "text": "..."},
                    {"type": "image", "data": "base64...", "mimeType": "image/png"}
                ]
            }
        """
        try:
            response = await self.client.post(f"/api/vms/{vm_id}/browser/screenshot")
            response.raise_for_status()
            result = response.json()
            
            # 检查返回格式
            if "content" in result and isinstance(result["content"], list):
                # vmcontrol 已返回 MCP 标准格式，直接使用
                return {
                    "success": result.get("status") == "success",
                    "content": result["content"]
                }
            else:
                # 转换传统格式为标准格式
                image_data = result.get("data") or result.get("image_data", "")
                
                if not image_data:
                    return {
                        "success": False,
                        "error": "No image data returned from vmcontrol",
                        "content": []
                    }
                
                # 可选：压缩图像（如果过大）
                image_data, metadata = await self._compress_image_if_needed(image_data)
                
                # 构建标准格式
                content = [
                    {
                        "type": "text",
                        "text": f"Browser screenshot captured successfully. {metadata.get('compression_info', '')}"
                    },
                    {
                        "type": "image",
                        "data": image_data,
                        "mimeType": f"image/{result.get('format', 'png')}",
                        "metadata": {
                            "width": result.get("width"),
                            "height": result.get("height"),
                            **metadata
                        }
                    }
                ]
                
                return {
                    "success": True,
                    "content": content
                }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Browser screenshot HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "content": []
            }
        except Exception as e:
            logger.error(f"[VmuseAdapter] Browser screenshot failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _browser_content(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取浏览器页面内容 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: {} (可选参数，如是否包含截图)
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [
                    {"type": "text", "text": "页面文本内容"},
                    {"type": "image", "data": "...", "mimeType": "image/png"}  # 可选
                ]
            }
        """
        try:
            response = await self.client.post(f"/api/vms/{vm_id}/browser/content")
            response.raise_for_status()
            result = response.json()
            
            content_items = []
            
            # 添加文本内容
            page_content = result.get("content", "") or result.get("text", "")
            if page_content:
                content_items.append({
                    "type": "text",
                    "text": page_content
                })
            
            # 如果返回中包含截图，添加到 content
            if "screenshot" in result or "image_data" in result:
                image_data = result.get("screenshot") or result.get("image_data")
                
                # 可选：压缩图像
                image_data, metadata = await self._compress_image_if_needed(image_data)
                
                content_items.append({
                    "type": "image",
                    "data": image_data,
                    "mimeType": result.get("mimeType", "image/png"),
                    "metadata": metadata
                })
            
            # 如果没有任何内容，返回空字符串
            if not content_items:
                content_items.append({
                    "type": "text",
                    "text": ""
                })
            
            return {
                "success": True,
                "content": content_items
            }
        
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            logger.error(f"[VmuseAdapter] Browser content failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    # ==================== 图像处理辅助方法 ====================
    
    def _extract_image_from_content(self, result: Dict[str, Any]) -> str:
        """
        从标准 content 格式中提取图像数据
        
        Args:
            result: 标准格式的返回结果
        
        Returns:
            Base64 编码的图像数据，如果没有则返回空字符串
        """
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "image":
                return item.get("data", "")
        return ""
    
    async def _compress_image_if_needed(
        self,
        image_data: str,
        max_size_kb: Optional[int] = None
    ) -> tuple[str, dict]:
        """
        压缩图像到指定大小
        
        Args:
            image_data: Base64 编码的图像数据
            max_size_kb: 最大大小（KB），如果为 None 则使用配置值
        
        Returns:
            (compressed_data, metadata) - 压缩后的数据和元数据
        """
        import base64
        
        # 使用配置值或传入的参数
        if max_size_kb is None:
            max_size_kb = ServiceConfig.IMAGE_MAX_SIZE_KB if ServiceConfig.IMAGE_COMPRESS_ENABLED else float('inf')
        max_dimension = ServiceConfig.IMAGE_MAX_DIMENSION
        
        try:
            # 如果压缩被禁用，直接返回
            if not ServiceConfig.IMAGE_COMPRESS_ENABLED:
                return image_data, {
                    "compressed": False,
                    "original_size": len(image_data.encode('utf-8')),
                    "compression_info": "(compression disabled)"
                }
            
            # 计算原始大小
            original_size = len(image_data.encode('utf-8'))
            
            # 如果小于阈值，直接返回
            if original_size <= max_size_kb * 1024:
                return image_data, {
                    "compressed": False,
                    "original_size": original_size,
                    "compression_info": ""
                }
            
            # 尝试压缩图像
            try:
                from PIL import Image
                from io import BytesIO
                
                # 解码图像
                img_bytes = base64.b64decode(image_data)
                img = Image.open(BytesIO(img_bytes))
                
                # 降分辨率（保持宽高比）
                if max(img.size) > max_dimension:
                    ratio = max_dimension / max(img.size)
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    img = img.resize(new_size, Image.LANCZOS)
                    logger.info(f"[VmuseAdapter] Resized image from {img.size} to {new_size}")
                
                # 压缩质量
                output = BytesIO()
                img.save(output, format='PNG', optimize=True)
                compressed_bytes = output.getvalue()
                compressed_data = base64.b64encode(compressed_bytes).decode('utf-8')
                
                compressed_size = len(compressed_data.encode('utf-8'))
                compression_ratio = compressed_size / original_size
                
                logger.info(f"[VmuseAdapter] Image compressed: {original_size} -> {compressed_size} bytes ({compression_ratio:.1%})")
                
                return compressed_data, {
                    "compressed": True,
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": f"{compression_ratio:.1%}",
                    "compression_info": f"(compressed from {original_size//1024}KB to {compressed_size//1024}KB)"
                }
            
            except ImportError:
                logger.warning("[VmuseAdapter] PIL not available, skipping image compression")
                return image_data, {
                    "compressed": False,
                    "original_size": original_size,
                    "compression_info": "(compression skipped: PIL not available)"
                }
        
        except Exception as e:
            logger.warning(f"[VmuseAdapter] Image compression failed: {e}")
            return image_data, {
                "compressed": False,
                "error": str(e),
                "compression_info": "(compression failed)"
            }
    
    # ==================== 文件操作 ====================
    
    async def _file_read(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        读取文件内容
        
        注意：文件内容可能很大，会被自动截断机制处理
        """
        path = arguments.get("path")
        if not path:
            return {
                "success": False,
                "error": "Missing required parameter: path",
                "content": []
            }
        
        try:
            response = await self.client.get(
                f"/api/vms/{vm_id}/guest/file",
                params={"path": path}
            )
            response.raise_for_status()
            result = response.json()
            
            # 转换为标准格式
            file_data = {
                "content": result.get("content", ""),
                "size": result.get("size", 0),
                "path": path
            }
            
            return {
                "success": True,
                "result": file_data,
                "content": self._as_text_content(file_data),
            }
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[VmuseAdapter] File read HTTP error for {path}: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            logger.error(f"[VmuseAdapter] File read failed for {path}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    async def _file_write(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """写入文件"""
        path = arguments.get("path")
        content = arguments.get("content")
        
        if not path:
            return {"success": False, "error": "Missing required parameter: path"}
        if content is None:  # 允许空内容
            return {"success": False, "error": "Missing required parameter: content"}
        
        response = await self.client.post(
            f"/api/vms/{vm_id}/guest/file",
            json={
                "path": path,
                "content": content
            }
        )
        response.raise_for_status()
        result = response.json()
        
        return {
            "success": result.get("success", True),
            "result": {
                "path": path,
                "bytes_written": len(content) if isinstance(content, str) else result.get("bytes_written", 0)
            }
        }
    
    # ==================== Shell 操作 ====================
    
    async def _shell_exec(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Shell 命令
        
        注意：命令输出可能很大，会被自动截断机制处理
        """
        command = arguments.get("command")
        if not command:
            return {
                "success": False,
                "error": "Missing required parameter: command",
                "content": []
            }
        
        wait = arguments.get("wait", True)
        
        try:
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", command],
                    "wait": wait
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # 转换为标准格式
            # 注意：success=True 表示命令执行完成（无论 exit_code 是多少）
            # exit_code 由 LLM 根据上下文判断是否符合预期
            exec_data = {
                "exit_code": result.get("exit_code", 0),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "command": command
            }
            
            return {
                "success": exec_data["exit_code"] == 0,
                "result": exec_data,
                "content": self._as_text_content(exec_data),
            }
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[VmuseAdapter] Shell exec HTTP error for '{command}': {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except Exception as e:
            logger.error(f"[VmuseAdapter] Shell exec failed for '{command}': {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    # ==================== 截图 ====================
    
    async def _screenshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取 VM 截图 - 返回 MCP 标准格式
        
        Args:
            vm_id: VM ID
            arguments: 参数（可选：grid, center, zoom_factor）
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [
                    {"type": "text", "text": "..."},
                    {"type": "image", "data": "base64...", "mimeType": "image/png"}
                ]
            }
        """
        try:
            response = await self.client.post(f"/api/vms/{vm_id}/screenshot")
            response.raise_for_status()
            result = response.json()
            
            # vmcontrol 返回 JSON: {"data": "base64...", "format": "png", "width": 1280, "height": 800}
            # 兼容两种格式：新格式使用 "data"，旧格式使用 "image_data"
            image_data = result.get("data") or result.get("image_data", "")
            
            if not image_data:
                return {
                    "success": False,
                    "error": "No image data returned from vmcontrol",
                    "content": []
                }
            
            # 可选：压缩图像（如果过大）
            image_data, metadata = await self._compress_image_if_needed(image_data)
            
            # 构建标准格式
            content = [
                {
                    "type": "text",
                    "text": f"Screenshot captured successfully. {metadata.get('compression_info', '')}"
                },
                {
                    "type": "image",
                    "data": image_data,
                    "mimeType": f"image/{result.get('format', 'png')}",
                    "metadata": {
                        "width": result.get("width"),
                        "height": result.get("height"),
                        **metadata
                    }
                }
            ]
            
            screenshot_result = {
                "format": result.get("format", "png"),
                "width": result.get("width"),
                "height": result.get("height"),
                "image_data": image_data,
            }

            return {
                "success": True,
                "result": screenshot_result,
                "content": content
            }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Screenshot HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "content": []
            }
        except Exception as e:
            logger.error(f"[VmuseAdapter] Screenshot failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    # ==================== 鼠标操作 ====================
    
    async def _mouse(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        鼠标操作 - 返回统一格式
        
        Args:
            vm_id: VM ID
            arguments: 鼠标操作参数
        
        Returns:
            统一格式：
            {
                "success": bool,
                "content": [
                    {"type": "text", "text": "..."},
                    {"type": "image", "data": "base64...", "mimeType": "image/png"}  # 仅 aim 操作
                ]
            }
        """
        action = arguments.get("action")
        
        if not action:
            return {
                "success": False,
                "error": "Missing 'action' parameter",
                "content": []
            }
        
        # 处理 aim action（返回图片）
        if action == "aim":
            try:
                # 绝对定位
                if "x" in arguments and "y" in arguments:
                    x = int(arguments["x"])
                    y = int(arguments["y"])
                    zoom = float(arguments.get("zoom", 1.0))
                    aim_id = self.aim_cache.create(x, y, zoom)
                    
                    # 获取带网格的截图（已返回标准格式）
                    screenshot_result = await self._screenshot(vm_id, {
                        "grid": True,
                        "center": {"x": x, "y": y},
                        "zoom_factor": zoom
                    })
                    
                    # 检查截图是否成功
                    if not screenshot_result.get("success"):
                        return {
                            "success": False,
                            "error": screenshot_result.get("error", "Failed to capture screenshot"),
                            "content": []
                        }
                    
                    # 构建返回内容：文本 + 图片
                    content = screenshot_result.get("content", []).copy()
                    
                    # 添加 aim 信息到文本
                    aim_info = {
                        "aim_id": aim_id,
                        "position": {"x": x, "y": y, "zoom": zoom},
                        "message": "Mouse aim position set successfully"
                    }
                    
                    # 如果有文本项，更新它；否则添加新的文本项
                    text_found = False
                    for item in content:
                        if item.get("type") == "text":
                            # 合并信息
                            try:
                                existing_text = json.loads(item.get("text", "{}"))
                                existing_text.update(aim_info)
                                item["text"] = json.dumps(existing_text, ensure_ascii=False)
                            except:
                                # 如果不是 JSON，追加信息
                                item["text"] = f"{item.get('text', '')}\n{json.dumps(aim_info, ensure_ascii=False)}"
                            text_found = True
                            break
                    
                    if not text_found:
                        # 在开头插入文本项
                        content.insert(0, {
                            "type": "text",
                            "text": json.dumps(aim_info, ensure_ascii=False)
                        })
                    
                    return {
                        "success": True,
                        "content": content
                    }
                
                # 相对调整
                elif "aim_id" in arguments:
                    aim_id = arguments["aim_id"]
                    delta_x = int(arguments.get("delta_x", 0))
                    delta_y = int(arguments.get("delta_y", 0))
                    zoom = arguments.get("zoom")
                    
                    aim = self.aim_cache.update(aim_id, delta_x, delta_y, zoom)
                    if not aim:
                        return {
                            "success": False,
                            "error": f"aim_id '{aim_id}' not found or expired",
                            "content": []
                        }
                    
                    # 获取更新后的截图（已返回标准格式）
                    screenshot_result = await self._screenshot(vm_id, {
                        "grid": True,
                        "center": {"x": aim["x"], "y": aim["y"]},
                        "zoom_factor": aim["zoom"]
                    })
                    
                    # 检查截图是否成功
                    if not screenshot_result.get("success"):
                        return {
                            "success": False,
                            "error": screenshot_result.get("error", "Failed to capture screenshot"),
                            "content": []
                        }
                    
                    # 构建返回内容：文本 + 图片
                    content = screenshot_result.get("content", []).copy()
                    
                    # 添加 aim 信息到文本
                    aim_info = {
                        "aim_id": aim_id,
                        "position": {"x": aim["x"], "y": aim["y"], "zoom": aim["zoom"]},
                        "delta": {"x": delta_x, "y": delta_y},
                        "message": "Mouse aim position updated successfully"
                    }
                    
                    # 如果有文本项，更新它；否则添加新的文本项
                    text_found = False
                    for item in content:
                        if item.get("type") == "text":
                            # 合并信息
                            try:
                                existing_text = json.loads(item.get("text", "{}"))
                                existing_text.update(aim_info)
                                item["text"] = json.dumps(existing_text, ensure_ascii=False)
                            except:
                                # 如果不是 JSON，追加信息
                                item["text"] = f"{item.get('text', '')}\n{json.dumps(aim_info, ensure_ascii=False)}"
                            text_found = True
                            break
                    
                    if not text_found:
                        # 在开头插入文本项
                        content.insert(0, {
                            "type": "text",
                            "text": json.dumps(aim_info, ensure_ascii=False)
                        })
                    
                    return {
                        "success": True,
                        "content": content
                    }
                
                else:
                    return {
                        "success": False,
                        "error": "aim requires x,y or aim_id",
                        "content": []
                    }
            
            except Exception as e:
                logger.error(f"[VmuseAdapter] Mouse aim operation failed: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "content": []
                }
        
        # ========== 添加强制 aim_id 检查 ==========
        # 所有 execute actions 必须使用 aim_id
        actions_requiring_aim_id = ["click", "double", "right_click", "down", "move", "scroll"]
        
        if action in actions_requiring_aim_id:
            # 检查是否提供了 aim_id
            if "aim_id" not in arguments:
                return {
                    "success": False,
                    "error": f"'{action}' requires aim_id. Use mouse(action='aim', x=..., y=...) first to get an aim_id.",
                    "content": []
                }
            
            # 从缓存获取 aim 数据
            aim_id = arguments["aim_id"]
            aim = self.aim_cache.get(aim_id)
            if not aim:
                return {
                    "success": False,
                    "error": f"Invalid or expired aim_id: '{aim_id}'. Please call mouse(action='aim', ...) again to get a new aim_id.",
                    "content": []
                }
            
            # 强制使用 aim 缓存中的坐标，覆盖任何直接提供的 x, y
            arguments["x"] = aim["x"]
            arguments["y"] = aim["y"]
            
            logger.info(f"[VmuseAdapter] Using aim_id '{aim_id}' at position ({aim['x']}, {aim['y']})")
        
        # ========== 继续处理各个 action ==========
        # 构建 vmcontrol API 请求
        payload = {"action": action}
        
        if action == "move":
            # 移动鼠标
            if "x" not in arguments or "y" not in arguments:
                return {
                    "success": False,
                    "error": "Missing 'x' or 'y' for move action",
                    "content": []
                }
            payload["x"] = arguments["x"]
            payload["y"] = arguments["y"]
        
        elif action in ["click", "right_click"]:
            # 点击
            if "x" in arguments and "y" in arguments:
                payload["x"] = arguments["x"]
                payload["y"] = arguments["y"]
            
            # 确定按钮
            if action == "right_click":
                payload["button"] = "right"
                payload["action"] = "click"
            else:
                payload["button"] = arguments.get("button", "left")
        
        elif action == "double":
            # 双击 - aim_id 已经设置了 x, y
            try:
                x = arguments.get("x")
                y = arguments.get("y")
                
                # 移动到位置并双击（不再支持在当前位置双击）
                await self._exec_guest_command(vm_id, f"xdotool mousemove {x} {y} click --repeat 2 --delay 100 1")
                
                result_info = {
                    "message": "Mouse double click executed successfully",
                    "action": action,
                    "x": x,
                    "y": y
                }
                
                return {
                    "success": True,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_info, ensure_ascii=False)
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"[VmuseAdapter] Mouse double click failed: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "content": []
                }
        
        elif action == "down":
            # 按下鼠标（拖拽开始） - aim_id 已经设置了 x, y
            try:
                x = arguments.get("x")
                y = arguments.get("y")
                button = arguments.get("button", "left")
                button_num = {"left": 1, "right": 3, "middle": 2}.get(button, 1)
                
                # 移动到位置并按下（不再支持在当前位置按下）
                await self._exec_guest_command(vm_id, f"xdotool mousemove {x} {y} mousedown {button_num}")
                
                result_info = {
                    "message": "Mouse down executed successfully",
                    "action": action,
                    "x": x,
                    "y": y,
                    "button": button
                }
                
                return {
                    "success": True,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_info, ensure_ascii=False)
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"[VmuseAdapter] Mouse down failed: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "content": []
                }
        
        elif action == "up":
            # 释放鼠标（拖拽结束）
            try:
                button = arguments.get("button", "left")
                button_num = {"left": 1, "right": 3, "middle": 2}.get(button, 1)
                
                await self._exec_guest_command(vm_id, f"xdotool mouseup {button_num}")
                
                result_info = {
                    "message": "Mouse up executed successfully",
                    "action": action,
                    "button": button
                }
                
                return {
                    "success": True,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_info, ensure_ascii=False)
                        }
                    ]
                }
            except Exception as e:
                logger.error(f"[VmuseAdapter] Mouse up failed: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "content": []
                }
        
        elif action == "scroll":
            # 滚动 - 转换参数格式
            direction = arguments.get("direction", "down")
            amount = arguments.get("amount", 1)
            
            # 获取 aim 位置
            x = arguments.get("x")
            y = arguments.get("y")
            
            # 先移动鼠标到 aim 位置，然后滚动
            if x is not None and y is not None:
                # 移动到位置
                move_result = await self._exec_guest_command(vm_id, f"xdotool mousemove {x} {y}")
                if move_result.get("exit_code") != 0:
                    return {
                        "success": False,
                        "error": "Failed to move mouse before scrolling",
                        "content": []
                    }
            
            # 转换：direction + amount → delta
            # up = 正数, down = 负数
            if direction == "up":
                payload["delta"] = amount
            else:  # down
                payload["delta"] = -amount
        
        else:
            return {
                "success": False,
                "error": f"Unknown mouse action: {action}",
                "content": []
            }
        
        # 调用 vmcontrol API
        try:
            response = await self.client.post(
                f"/api/vms/{vm_id}/input/mouse",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            result_info = {
                "message": f"Mouse {action} executed successfully",
                "action": action
            }
            
            return {
                "success": True,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result_info, ensure_ascii=False)
                    }
                ]
            }
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[VmuseAdapter] Mouse operation HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": []
            }
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Mouse operation HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "content": []
            }
        except Exception as e:
            logger.error(f"[VmuseAdapter] Mouse operation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "content": []
            }
    
    # ==================== 键盘操作 ====================
    
    async def _keyboard(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """键盘操作"""
        action = arguments.get("action")
        
        if not action:
            return {"success": False, "error": "Missing 'action' parameter"}
        
        # 构建 vmcontrol API 请求
        payload = {"action": action}
        
        if action == "type":
            # 输入文本
            if "text" not in arguments:
                return {"success": False, "error": "Missing 'text' for type action"}
            
            text = arguments["text"]
            
            # 检测是否包含非ASCII字符（中文、emoji等）
            has_non_ascii = any(ord(c) > 127 for c in text)
            
            if has_non_ascii:
                # 使用 Guest Agent + xdotool 逐字符输入
                logger.info(f"[VmuseAdapter] Detected non-ASCII characters, using xdotool for typing")
                
                try:
                    for char in text:
                        # 转义特殊字符
                        escaped_char = char.replace("'", "'\\''")
                        cmd = f"xdotool type --clearmodifiers '{escaped_char}'"
                        result = await self._exec_guest_command(vm_id, cmd)
                        
                        if result.get("exit_code") != 0:
                            logger.warning(f"[VmuseAdapter] Failed to type character: {char}")
                        
                        # 延迟200ms，等待输入法处理
                        await asyncio.sleep(0.2)
                    
                    return {
                        "success": True,
                        "result": {
                            "message": "Type executed successfully",
                            "action": action,
                            "text": text,
                            "method": "xdotool_per_char"
                        }
                    }
                except Exception as e:
                    logger.error(f"[VmuseAdapter] xdotool typing failed: {e}")
                    return {"success": False, "error": f"Typing failed: {str(e)}"}
            
            else:
                # ASCII 文本，使用 vmcontrol API（快速）
                payload["text"] = text
        
        elif action == "key":
            # 按键
            if "key" not in arguments:
                return {"success": False, "error": "Missing 'key' for key action"}
            payload["key"] = arguments["key"]
        
        elif action == "combo":
            # 组合键
            if "keys" not in arguments:
                return {"success": False, "error": "Missing 'keys' for combo action"}
            payload["keys"] = arguments["keys"]
        
        else:
            return {"success": False, "error": f"Unknown keyboard action: {action}"}
        
        # 调用 vmcontrol API
        try:
            response = await self.client.post(
                f"/api/vms/{vm_id}/input/keyboard",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "result": {
                    "message": f"Keyboard {action} executed successfully",
                    "action": action
                }
            }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Keyboard operation failed: {e}")
            return {
                "success": False,
                "error": f"Keyboard operation failed: {str(e)}"
            }
    
    # ==================== 窗口管理操作 ====================
    
    async def _list_windows(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """列出所有窗口"""
        try:
            # 通过 Guest Agent 执行 wmctrl -l
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", "wmctrl -l"],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # 解析 wmctrl 输出
            windows = []
            if result.get("exit_code") == 0 and result.get("stdout"):
                for line in result["stdout"].strip().split("\n"):
                    if line:
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            windows.append({
                                "id": parts[0],
                                "desktop": parts[1],
                                "pid": parts[2],
                                "title": parts[3]
                            })
            
            return {
                "success": True,
                "result": {
                    "windows": windows,
                    "count": len(windows)
                }
            }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] List windows failed: {e}")
            return {
                "success": False,
                "error": f"List windows failed: {str(e)}"
            }
    
    async def _focus_window(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """聚焦窗口"""
        window_id = arguments.get("window_id")
        if not window_id:
            return {"success": False, "error": "Missing required parameter: window_id"}
        
        try:
            # 使用 wmctrl -ia <window_id> 聚焦窗口
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", f"wmctrl -ia {window_id}"],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code") == 0:
                return {
                    "success": True,
                    "result": {
                        "message": f"Window {window_id} focused successfully",
                        "window_id": window_id
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to focus window: {result.get('stderr', 'Unknown error')}"
                }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Focus window failed: {e}")
            return {
                "success": False,
                "error": f"Focus window failed: {str(e)}"
            }
    
    async def _maximize_window(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """最大化窗口"""
        window_id = arguments.get("window_id")
        
        try:
            if window_id:
                # 最大化指定窗口
                command = f"wmctrl -ir {window_id} -b add,maximized_vert,maximized_horz"
            else:
                # 最大化当前聚焦窗口
                command = "wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz"
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", command],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code") == 0:
                return {
                    "success": True,
                    "result": {
                        "message": "Window maximized successfully",
                        "window_id": window_id or "active"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to maximize window: {result.get('stderr', 'Unknown error')}"
                }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Maximize window failed: {e}")
            return {
                "success": False,
                "error": f"Maximize window failed: {str(e)}"
            }
    
    async def _minimize_window(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """最小化窗口"""
        window_id = arguments.get("window_id")
        
        try:
            if window_id:
                # 最小化指定窗口（使用 xdotool）
                command = f"xdotool windowminimize {window_id}"
            else:
                # 最小化当前聚焦窗口
                command = "xdotool getactivewindow windowminimize"
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", command],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code") == 0:
                return {
                    "success": True,
                    "result": {
                        "message": "Window minimized successfully",
                        "window_id": window_id or "active"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to minimize window: {result.get('stderr', 'Unknown error')}"
                }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Minimize window failed: {e}")
            return {
                "success": False,
                "error": f"Minimize window failed: {str(e)}"
            }
    
    async def _close_window(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """关闭窗口"""
        window_id = arguments.get("window_id")
        
        try:
            if window_id:
                # 关闭指定窗口
                command = f"wmctrl -ic {window_id}"
            else:
                # 关闭当前聚焦窗口
                command = "wmctrl -c :ACTIVE:"
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", command],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code") == 0:
                return {
                    "success": True,
                    "result": {
                        "message": "Window closed successfully",
                        "window_id": window_id or "active"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to close window: {result.get('stderr', 'Unknown error')}"
                }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Close window failed: {e}")
            return {
                "success": False,
                "error": f"Close window failed: {str(e)}"
            }
    
    async def _resize_window(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调整窗口大小"""
        width = arguments.get("width")
        height = arguments.get("height")
        window_id = arguments.get("window_id")
        
        if width is None or height is None:
            return {"success": False, "error": "Missing required parameters: width and height"}
        
        try:
            if window_id:
                # 调整指定窗口大小
                command = f"wmctrl -ir {window_id} -e 0,-1,-1,{width},{height}"
            else:
                # 调整当前聚焦窗口大小
                command = f"wmctrl -r :ACTIVE: -e 0,-1,-1,{width},{height}"
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", command],
                    "wait": True
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("exit_code") == 0:
                return {
                    "success": True,
                    "result": {
                        "message": f"Window resized to {width}x{height}",
                        "window_id": window_id or "active",
                        "width": width,
                        "height": height
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to resize window: {result.get('stderr', 'Unknown error')}"
                }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Resize window failed: {e}")
            return {
                "success": False,
                "error": f"Resize window failed: {str(e)}"
            }
    
    async def _launch_app(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """启动应用"""
        app_name = arguments.get("app_name")
        args = arguments.get("args", [])
        
        if not app_name:
            return {"success": False, "error": "Missing required parameter: app_name"}
        
        try:
            # 构建命令 - 使用 nohup 后台启动，设置 DISPLAY=:0 以确保 GUI 程序在 VNC 窗口显示
            if args:
                args_str = " ".join(args)
                command = f"DISPLAY=:0 nohup {app_name} {args_str} > /dev/null 2>&1 &"
            else:
                command = f"DISPLAY=:0 nohup {app_name} > /dev/null 2>&1 &"
            
            response = await self.client.post(
                f"/api/vms/{vm_id}/guest/exec",
                json={
                    "path": "/bin/bash",
                    "args": ["-c", command],
                    "wait": False  # 不等待后台进程
                }
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "result": {
                    "message": f"Application '{app_name}' launched successfully",
                    "app_name": app_name,
                    "args": args
                }
            }
        
        except httpx.HTTPError as e:
            logger.error(f"[VmuseAdapter] Launch app failed: {e}")
            return {
                "success": False,
                "error": f"Launch app failed: {str(e)}"
            }
    
    # ==================== Context 工具 ====================
    
    async def _exec_guest_command(self, agent_id: str, command: str) -> Dict[str, Any]:
        """执行 Guest Agent 命令的辅助方法"""
        url = f"{self.vmcontrol_url}/api/vms/{agent_id}/guest/exec"
        payload = {
            "path": "/bin/bash",
            "args": ["-c", command],
            "wait": True
        }
        
        try:
            async with internal_async_client(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"[VmuseAdapter] Guest command failed: {e}")
            return {"error": str(e), "exit_code": -1, "stdout": "", "stderr": str(e)}
    
    async def _system_snapshot(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取系统状态快照
        
        注意：系统信息可能较大，会被自动截断机制处理
        """
        include = arguments.get("include", ["processes", "memory", "disk", "network", "cpu"])
        
        snapshot = {}
        
        try:
            if "processes" in include:
                # 获取进程信息（按内存使用排序，前20个）
                result = await self._exec_guest_command(vm_id, "ps aux --sort=-%mem | head -20")
                snapshot["processes"] = result.get("stdout", "")
            
            if "memory" in include:
                # 获取内存信息
                result = await self._exec_guest_command(vm_id, "free -h")
                snapshot["memory"] = result.get("stdout", "")
            
            if "disk" in include:
                # 获取磁盘信息
                result = await self._exec_guest_command(vm_id, "df -h")
                snapshot["disk"] = result.get("stdout", "")
            
            if "network" in include:
                # 获取网络信息
                result = await self._exec_guest_command(vm_id, "ip addr show")
                snapshot["network"] = result.get("stdout", "")
            
            if "cpu" in include:
                # 获取 CPU 信息
                result = await self._exec_guest_command(vm_id, "top -bn1 | head -5")
                snapshot["cpu"] = result.get("stdout", "")
            
            return {
                "success": True,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(snapshot, ensure_ascii=False)
                    }
                ]
            }
        
        except Exception as e:
            logger.error(f"[VmuseAdapter] System snapshot failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"System snapshot failed: {str(e)}",
                "content": []
            }
    
    async def _clipboard_get(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取剪贴板内容
        
        注意：剪贴板内容可能很大，会被自动截断机制处理
        """
        try:
            # 尝试使用 xclip 获取剪贴板内容
            result = await self._exec_guest_command(vm_id, "xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null || echo ''")
            
            clipboard_data = {
                "content": result.get("stdout", "")
            }
            
            return {
                "success": True,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(clipboard_data, ensure_ascii=False)
                    }
                ]
            }
        
        except Exception as e:
            logger.error(f"[VmuseAdapter] Clipboard get failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Clipboard get failed: {str(e)}",
                "content": []
            }
    
    async def _clipboard_set(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """设置剪贴板内容"""
        content = arguments.get("content", "")
        
        try:
            # 安全地引用内容，防止命令注入
            safe_content = shlex.quote(content)
            
            # 尝试使用 xclip 或 xsel 设置剪贴板
            command = f"echo {safe_content} | xclip -selection clipboard 2>/dev/null || echo {safe_content} | xsel --clipboard --input 2>/dev/null"
            result = await self._exec_guest_command(vm_id, command)
            
            return {
                "success": result.get("exit_code") == 0,
                "result": {
                    "message": "Clipboard content set successfully" if result.get("exit_code") == 0 else "Failed to set clipboard content"
                }
            }
        
        except Exception as e:
            logger.error(f"[VmuseAdapter] Clipboard set failed: {e}")
            return {
                "success": False,
                "error": f"Clipboard set failed: {str(e)}"
            }
    
    async def _environment_info(self, vm_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取环境信息
        
        注意：环境变量可能很多，会被自动截断机制处理
        """
        try:
            info = {}
            
            # OS 信息
            os_info = await self._exec_guest_command(vm_id, "uname -a")
            info["os"] = os_info.get("stdout", "").strip()
            
            # 发行版信息
            distro = await self._exec_guest_command(vm_id, "cat /etc/os-release 2>/dev/null | grep PRETTY_NAME || echo 'Unknown'")
            info["distro"] = distro.get("stdout", "").strip()
            
            # 架构信息
            arch = await self._exec_guest_command(vm_id, "uname -m")
            info["arch"] = arch.get("stdout", "").strip()
            
            # 环境变量（常用的）
            env_vars = await self._exec_guest_command(vm_id, "env | grep -E '^(PATH|HOME|USER|DISPLAY|LANG|SHELL)' | sort")
            info["env"] = env_vars.get("stdout", "").strip()
            
            return {
                "success": True,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(info, ensure_ascii=False)
                    }
                ]
            }
        
        except Exception as e:
            logger.error(f"[VmuseAdapter] Environment info failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Environment info failed: {str(e)}",
                "content": []
            }
    
    # ==================== 工具列表（可选） ====================
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有支持的工具及其参数
        
        Returns:
            工具映射表
        """
        return {
            "browser_navigate": {
                "description": "Navigate browser to URL",
                "parameters": {
                    "url": {"type": "string", "required": True, "description": "Target URL"}
                }
            },
            "browser_click": {
                "description": "Click browser element",
                "parameters": {
                    "selector": {"type": "string", "required": True, "description": "CSS selector"}
                }
            },
            "browser_type": {
                "description": "Type text into browser element",
                "parameters": {
                    "selector": {"type": "string", "required": True, "description": "CSS selector"},
                    "text": {"type": "string", "required": True, "description": "Text to type"}
                }
            },
            "file_read": {
                "description": "Read file from VM",
                "parameters": {
                    "path": {"type": "string", "required": True, "description": "File path"}
                }
            },
            "file_write": {
                "description": "Write file to VM",
                "parameters": {
                    "path": {"type": "string", "required": True, "description": "File path"},
                    "content": {"type": "string", "required": True, "description": "File content"}
                }
            },
            "shell_exec": {
                "description": "Execute shell command",
                "parameters": {
                    "command": {"type": "string", "required": True, "description": "Shell command"},
                    "wait": {"type": "boolean", "required": False, "description": "Wait for completion", "default": True}
                }
            },
            "screenshot": {
                "description": "Take VM screenshot",
                "parameters": {}
            },
            "mouse": {
                "description": "Control mouse in VM",
                "parameters": {
                    "action": {"type": "string", "required": True, "description": "Mouse action (move, click, right_click, scroll)"},
                    "x": {"type": "integer", "required": False, "description": "X coordinate"},
                    "y": {"type": "integer", "required": False, "description": "Y coordinate"},
                    "button": {"type": "string", "required": False, "description": "Mouse button (left, right, middle)"},
                    "direction": {"type": "string", "required": False, "description": "Scroll direction (up, down)"},
                    "amount": {"type": "integer", "required": False, "description": "Scroll amount", "default": 1}
                }
            },
            "keyboard": {
                "description": "Control keyboard in VM",
                "parameters": {
                    "action": {"type": "string", "required": True, "description": "Keyboard action (type, key, combo)"},
                    "text": {"type": "string", "required": False, "description": "Text to type"},
                    "key": {"type": "string", "required": False, "description": "Key to press"},
                    "keys": {"type": "array", "required": False, "description": "Keys for combo"}
                }
            },
            "list_windows": {
                "description": "List all desktop windows",
                "parameters": {}
            },
            "focus_window": {
                "description": "Focus a specific window",
                "parameters": {
                    "window_id": {"type": "string", "required": True, "description": "Window ID or title"}
                }
            },
            "maximize_window": {
                "description": "Maximize a window",
                "parameters": {
                    "window_id": {"type": "string", "required": False, "description": "Window ID or title (optional, uses focused window if not specified)"}
                }
            },
            "minimize_window": {
                "description": "Minimize a window",
                "parameters": {
                    "window_id": {"type": "string", "required": False, "description": "Window ID or title (optional, uses focused window if not specified)"}
                }
            },
            "close_window": {
                "description": "Close a window",
                "parameters": {
                    "window_id": {"type": "string", "required": False, "description": "Window ID or title (optional, uses focused window if not specified)"}
                }
            },
            "resize_window": {
                "description": "Resize a window",
                "parameters": {
                    "window_id": {"type": "string", "required": False, "description": "Window ID or title (optional, uses focused window if not specified)"},
                    "width": {"type": "integer", "required": True, "description": "New width in pixels"},
                    "height": {"type": "integer", "required": True, "description": "New height in pixels"}
                }
            },
            "launch_app": {
                "description": "Launch an application",
                "parameters": {
                    "app_name": {"type": "string", "required": True, "description": "Application name or command"},
                    "args": {"type": "array", "required": False, "description": "Command line arguments (optional)"}
                }
            }
        }
    
    def list_tools_mcp_format(self) -> list[Dict[str, Any]]:
        """
        返回所有 VM 工具的定义（MCP 标准格式）
        
        用于 Tools Server 工具发现。返回格式与 MCP 协议一致。
        
        Returns:
            工具列表，每个工具包含 name, description, inputSchema
        """
        return [
            {
                "name": "browser_navigate",
                "description": "Navigate browser to a URL",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "browser_click",
                "description": "Click element in browser by selector",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"}
                    },
                    "required": ["selector"]
                }
            },
            {
                "name": "browser_type",
                "description": "Type text into browser element",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "selector": {"type": "string", "description": "CSS selector"},
                        "text": {"type": "string", "description": "Text to type"}
                    },
                    "required": ["selector", "text"]
                }
            },
            {
                "name": "browser_screenshot",
                "description": "Take screenshot of current browser page",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "browser_content",
                "description": "Get text content of current browser page",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "browser_scroll",
                "description": "Scroll browser page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right"],
                            "description": "Scroll direction"
                        },
                        "amount": {
                            "type": "integer",
                            "description": "Scroll amount in pixels",
                            "default": 100
                        }
                    },
                    "required": ["direction"]
                }
            },
            {
                "name": "browser_eval",
                "description": "Execute JavaScript code in browser",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "script": {
                            "type": "string",
                            "description": "JavaScript code to execute"
                        }
                    },
                    "required": ["script"]
                }
            },
            {
                "name": "browser_get_tabs",
                "description": "Get list of open browser tabs",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "browser_switch_tab",
                "description": "Switch to a specific browser tab",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tab_index": {
                            "type": "integer",
                            "description": "Tab index (0-based)"
                        }
                    },
                    "required": ["tab_index"]
                }
            },
            {
                "name": "browser_close_tab",
                "description": "Close current or specific browser tab",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tab_index": {
                            "type": "integer",
                            "description": "Tab index to close (optional, closes current if not specified)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "file_read",
                "description": "Read file from VM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path in VM"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "file_write",
                "description": "Write file to VM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path in VM"},
                        "content": {"type": "string", "description": "File content (base64 for binary)"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "shell_exec",
                "description": "Execute shell command in VM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "screenshot",
                "description": "Take desktop screenshot of VM",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "mouse",
                "description": "Control mouse in VM. IMPORTANT: All actions except 'aim' require aim_id. Workflow: 1) aim to get aim_id, 2) use aim_id for other actions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["aim", "move", "click", "right_click", "double", "down", "up", "scroll"],
                            "description": "Mouse action to perform"
                        },
                        "x": {
                            "type": "integer",
                            "description": "X coordinate"
                        },
                        "y": {
                            "type": "integer",
                            "description": "Y coordinate"
                        },
                        "aim_id": {
                            "type": "string",
                            "description": "Aim ID from previous aim action"
                        },
                        "delta_x": {
                            "type": "integer",
                            "description": "X offset for aim adjustment"
                        },
                        "delta_y": {
                            "type": "integer",
                            "description": "Y offset for aim adjustment"
                        },
                        "zoom": {
                            "type": "number",
                            "description": "Zoom factor for aim (default: 1.0)"
                        },
                        "button": {
                            "type": "string",
                            "enum": ["left", "right", "middle"],
                            "description": "Mouse button"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down"],
                            "description": "Scroll direction"
                        },
                        "amount": {
                            "type": "integer",
                            "description": "Scroll amount",
                            "default": 1
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "keyboard",
                "description": "Control keyboard in VM (type text, press keys)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["type", "key", "combo"],
                            "description": "Keyboard action to perform"
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type (for type action)"
                        },
                        "key": {
                            "type": "string",
                            "description": "Key to press (for key action)"
                        },
                        "keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keys for combo (for combo action)"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "system_snapshot",
                "description": "Get system state snapshot (processes, memory, disk, network, cpu)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["processes", "memory", "disk", "network", "cpu"]
                            },
                            "description": "Components to include (default: all)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "clipboard_get",
                "description": "Get clipboard content",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "clipboard_set",
                "description": "Set clipboard content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to set"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "environment_info",
                "description": "Get environment information (OS, arch, env vars)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "list_windows",
                "description": "List all desktop windows",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "focus_window",
                "description": "Focus a specific window",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "window_id": {
                            "type": "string",
                            "description": "Window ID or title"
                        }
                    },
                    "required": ["window_id"]
                }
            },
            {
                "name": "maximize_window",
                "description": "Maximize a window",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "window_id": {
                            "type": "string",
                            "description": "Window ID or title (optional, uses focused window if not specified)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "minimize_window",
                "description": "Minimize a window",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "window_id": {
                            "type": "string",
                            "description": "Window ID or title (optional, uses focused window if not specified)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "close_window",
                "description": "Close a window",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "window_id": {
                            "type": "string",
                            "description": "Window ID or title (optional, uses focused window if not specified)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "resize_window",
                "description": "Resize a window",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "window_id": {
                            "type": "string",
                            "description": "Window ID or title (optional, uses focused window if not specified)"
                        },
                        "width": {
                            "type": "integer",
                            "description": "New width in pixels"
                        },
                        "height": {
                            "type": "integer",
                            "description": "New height in pixels"
                        }
                    },
                    "required": ["width", "height"]
                }
            },
            {
                "name": "launch_app",
                "description": "Launch an application",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Application name or command"
                        },
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Command line arguments (optional)"
                        }
                    },
                    "required": ["app_name"]
                }
            }
        ]


# ==================== 全局实例管理 ====================

_adapter_instance: Optional[VmuseAdapter] = None


def get_vmuse_adapter() -> VmuseAdapter:
    """
    获取 VMUSE 适配器全局实例（单例模式）
    
    Returns:
        VmuseAdapter 实例
    """
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = VmuseAdapter()
        logger.info("[VmuseAdapter] Global instance created")
    return _adapter_instance


async def close_vmuse_adapter():
    """关闭全局适配器实例"""
    global _adapter_instance
    if _adapter_instance is not None:
        await _adapter_instance.close()
        _adapter_instance = None
        logger.info("[VmuseAdapter] Global instance closed")
