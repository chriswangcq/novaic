"""
VmControl API 代理

将前端的 VNC WebSocket 和 REST API 请求代理到 vmcontrol 服务
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Response
from starlette.websockets import WebSocketState
import websockets
import asyncio

from common.config import ServiceConfig
from gateway.clients.vmcontrol import get_vmcontrol_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vmcontrol", tags=["vmcontrol"])


# ==================== WebSocket 代理 ====================

@router.websocket("/vms/{vm_id}/vnc")
async def vnc_websocket_proxy(websocket: WebSocket, vm_id: str):
    """
    VNC WebSocket 代理
    
    将前端的 VNC WebSocket 连接代理到 vmcontrol 服务
    """
    await websocket.accept()
    logger.info(f"[VNC Proxy] Client connected for VM {vm_id}")
    
    # 构建 vmcontrol WebSocket URL
    vmcontrol_ws_url = f"ws://{ServiceConfig.VMCONTROL_HOST}:{ServiceConfig.VMCONTROL_PORT}/api/vms/{vm_id}/vnc"
    
    vmcontrol_ws = None
    try:
        # 连接到 vmcontrol
        logger.info(f"[VNC Proxy] Connecting to vmcontrol: {vmcontrol_ws_url}")
        vmcontrol_ws = await websockets.connect(
            vmcontrol_ws_url,
            ping_interval=20,
            ping_timeout=10,
        )
        logger.info(f"[VNC Proxy] Connected to vmcontrol for VM {vm_id}")
        
        # 双向转发
        await bidirectional_forward(websocket, vmcontrol_ws, vm_id)
        
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"[VNC Proxy] WebSocket error for VM {vm_id}: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason=f"vmcontrol connection failed: {str(e)}")
    except Exception as e:
        logger.error(f"[VNC Proxy] Error for VM {vm_id}: {e}")
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011, reason=f"Proxy error: {str(e)}")
    finally:
        if vmcontrol_ws:
            await vmcontrol_ws.close()
        logger.info(f"[VNC Proxy] Connection closed for VM {vm_id}")


async def bidirectional_forward(client_ws: WebSocket, server_ws, vm_id: str):
    """
    双向转发 WebSocket 消息
    
    Args:
        client_ws: 前端 WebSocket 连接
        server_ws: vmcontrol WebSocket 连接
        vm_id: VM ID（用于日志）
    """
    
    async def forward_to_server():
        """转发客户端消息到服务器"""
        try:
            while True:
                # 接收来自客户端的消息
                data = await client_ws.receive_bytes()
                # 转发到 vmcontrol
                await server_ws.send(data)
        except WebSocketDisconnect:
            logger.info(f"[VNC Proxy] Client disconnected for VM {vm_id}")
        except Exception as e:
            logger.error(f"[VNC Proxy] Forward to server error for VM {vm_id}: {e}")
    
    async def forward_to_client():
        """转发服务器消息到客户端"""
        try:
            async for message in server_ws:
                # 转发到客户端
                if isinstance(message, bytes):
                    await client_ws.send_bytes(message)
                else:
                    await client_ws.send_text(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"[VNC Proxy] Server connection closed for VM {vm_id}")
        except Exception as e:
            logger.error(f"[VNC Proxy] Forward to client error for VM {vm_id}: {e}")
    
    # 并发执行双向转发
    await asyncio.gather(
        forward_to_server(),
        forward_to_client(),
        return_exceptions=True,
    )


# ==================== REST API 代理 ====================

@router.get("/vms/{vm_id}")
async def get_vm(vm_id: str):
    """
    获取 VM 信息
    
    代理到 vmcontrol 服务
    """
    try:
        client = get_vmcontrol_client()
        return await client.get_vm_info(vm_id)
    except Exception as e:
        logger.error(f"[VmControl Proxy] Get VM {vm_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vms")
async def list_vms():
    """
    列出所有 VM
    
    代理到 vmcontrol 服务
    """
    try:
        client = get_vmcontrol_client()
        return await client.list_vms()
    except Exception as e:
        logger.error(f"[VmControl Proxy] List VMs failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str):
    """
    获取 VM 截图（MCP 标准格式）
    
    代理到 vmcontrol 服务，返回 MCP 标准 content 数组格式
    """
    try:
        client = get_vmcontrol_client()
        result = await client.screenshot(vm_id)  # 现在返回 JSON dict
        
        # 转换为 MCP 标准格式
        return {
            "content": [
                {
                    "type": "image",
                    "data": result.get("data", ""),
                    "mimeType": f"image/{result.get('format', 'png')}"
                }
            ]
        }
    except Exception as e:
        logger.error(f"[VmControl Proxy] Screenshot for VM {vm_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/keys")
async def send_keys(vm_id: str, keys: dict):
    """
    发送按键到 VM
    
    代理到 vmcontrol 服务
    """
    try:
        client = get_vmcontrol_client()
        return await client.send_keys(vm_id, keys.get("keys", ""))
    except Exception as e:
        logger.error(f"[VmControl Proxy] Send keys to VM {vm_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/mouse/move")
async def mouse_move(vm_id: str, coords: dict):
    """
    移动鼠标
    
    代理到 vmcontrol 服务
    """
    try:
        client = get_vmcontrol_client()
        return await client.mouse_move(vm_id, coords.get("x", 0), coords.get("y", 0))
    except Exception as e:
        logger.error(f"[VmControl Proxy] Mouse move for VM {vm_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/mouse/click")
async def mouse_click(vm_id: str, button_data: dict):
    """
    鼠标点击
    
    代理到 vmcontrol 服务
    """
    try:
        client = get_vmcontrol_client()
        return await client.mouse_click(vm_id, button_data.get("button", "left"))
    except Exception as e:
        logger.error(f"[VmControl Proxy] Mouse click for VM {vm_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """
    检查 vmcontrol 服务健康状态
    """
    try:
        client = get_vmcontrol_client()
        healthy = await client.health_check()
        return {
            "status": "healthy" if healthy else "unhealthy",
            "service": "vmcontrol",
            "url": ServiceConfig.VMCONTROL_URL,
        }
    except Exception as e:
        logger.error(f"[VmControl Proxy] Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "vmcontrol",
            "url": ServiceConfig.VMCONTROL_URL,
            "error": str(e),
        }
