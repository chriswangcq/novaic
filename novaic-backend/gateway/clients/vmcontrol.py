"""
VmControl 客户端

用于与 vmcontrol 服务（Rust 服务）通信
"""

import logging
from typing import Optional, Dict, Any
import httpx

from common.config import ServiceConfig
from common.http.clients import internal_async_client

logger = logging.getLogger(__name__)


class VmControlClient:
    """VmControl 服务客户端"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        初始化 VmControl 客户端
        
        Args:
            base_url: vmcontrol 服务 URL，默认从配置读取
        """
        self.base_url = base_url or ServiceConfig.VMCONTROL_URL
        self.client = internal_async_client(
            base_url=self.base_url,
            timeout=ServiceConfig.HTTP_TIMEOUT,
        )
        logger.info(f"[VmControlClient] Initialized with base_url={self.base_url}")
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
    
    async def health_check(self) -> bool:
        """
        检查 vmcontrol 服务健康状态
        
        Returns:
            bool: 服务是否健康
        """
        # vmcontrol currently exposes /health (not /api/health) in production.
        # Probe both endpoints for compatibility across versions.
        for endpoint in ("/health", "/api/health"):
            try:
                response = await self.client.get(endpoint)
                if response.status_code == 200:
                    return True
            except Exception:
                continue
        logger.warning("[VmControlClient] Health check failed on both /health and /api/health")
        return False
    
    async def get_vm_info(self, vm_id: str) -> Dict[str, Any]:
        """
        获取 VM 信息
        
        Args:
            vm_id: VM ID
            
        Returns:
            VM 详细信息
            
        Raises:
            httpx.HTTPStatusError: 请求失败
        """
        response = await self.client.get(f"/api/vms/{vm_id}")
        response.raise_for_status()
        return response.json()
    
    async def list_vms(self) -> list[Dict[str, Any]]:
        """
        列出所有 VM
        
        Returns:
            VM 列表
        """
        response = await self.client.get("/api/vms")
        response.raise_for_status()
        return response.json()
    
    async def screenshot(self, vm_id: str) -> Dict[str, Any]:
        """
        获取 VM 截图（JSON 格式）
        
        Args:
            vm_id: VM ID
            
        Returns:
            {
                "data": "base64...",
                "format": "png",
                "width": 1920,
                "height": 1080
            }
        """
        response = await self.client.post(f"/api/vms/{vm_id}/screenshot")
        response.raise_for_status()
        return response.json()  # 返回 JSON 而不是 bytes
    
    async def send_keys(self, vm_id: str, keys: str) -> Dict[str, Any]:
        """
        发送按键到 VM
        
        Args:
            vm_id: VM ID
            keys: 按键序列
            
        Returns:
            操作结果
        """
        response = await self.client.post(
            f"/api/vms/{vm_id}/keys",
            json={"keys": keys}
        )
        response.raise_for_status()
        return response.json()
    
    async def mouse_move(self, vm_id: str, x: int, y: int) -> Dict[str, Any]:
        """
        移动鼠标
        
        Args:
            vm_id: VM ID
            x: X 坐标
            y: Y 坐标
            
        Returns:
            操作结果
        """
        response = await self.client.post(
            f"/api/vms/{vm_id}/mouse/move",
            json={"x": x, "y": y}
        )
        response.raise_for_status()
        return response.json()
    
    async def mouse_click(self, vm_id: str, button: str = "left") -> Dict[str, Any]:
        """
        鼠标点击
        
        Args:
            vm_id: VM ID
            button: 按钮（left/right/middle）
            
        Returns:
            操作结果
        """
        response = await self.client.post(
            f"/api/vms/{vm_id}/mouse/click",
            json={"button": button}
        )
        response.raise_for_status()
        return response.json()
    
    async def register_vm(self, vm_id: str, name: str, qmp_socket: str) -> Dict[str, Any]:
        """
        注册 VM 到 vmcontrol 服务
        
        Args:
            vm_id: VM ID (agent_id)
            name: VM 名称
            qmp_socket: QMP socket 路径
            
        Returns:
            注册结果
            
        Raises:
            httpx.HTTPStatusError: 请求失败
        """
        response = await self.client.post(
            "/api/vms",
            json={
                "id": vm_id,
                "name": name,
                "qmp_socket": qmp_socket
            }
        )
        response.raise_for_status()
        return response.json()

    async def shutdown_vm(self, vm_id: str) -> Dict[str, Any]:
        """
        请求 vmcontrol 对指定 VM 执行优雅关机。

        Args:
            vm_id: VM ID

        Returns:
            关机结果
        """
        response = await self.client.post(f"/api/vms/{vm_id}/shutdown")
        response.raise_for_status()
        if not response.text:
            return {"success": True}
        return response.json()

    async def shutdown_all_vms(self) -> Dict[str, Any]:
        """
        请求 vmcontrol 对所有已注册 VM 执行优雅关机。

        Returns:
            结果映射
        """
        response = await self.client.post("/api/vms/shutdown-all")
        response.raise_for_status()
        if not response.text:
            return {"success": True}
        return response.json()


# 全局客户端实例
_vmcontrol_client: Optional[VmControlClient] = None


def get_vmcontrol_client() -> VmControlClient:
    """
    获取全局 VmControl 客户端实例
    
    Returns:
        VmControlClient 实例
    """
    global _vmcontrol_client
    if _vmcontrol_client is None:
        _vmcontrol_client = VmControlClient()
    return _vmcontrol_client


async def close_vmcontrol_client():
    """关闭全局客户端实例"""
    global _vmcontrol_client
    if _vmcontrol_client is not None:
        await _vmcontrol_client.close()
        _vmcontrol_client = None
