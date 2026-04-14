"""
VmControl API 代理

将前端的 VNC WebSocket 和 REST API 请求代理到 vmcontrol 服务
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Response
from starlette.websockets import WebSocketState
import websockets
import asyncio

from device.pc_client import get_pc_client_manager

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
    
    # VNC 直连 VmControl（高带宽视频流，不走 CloudBridge）
    vmcontrol_ws_url = f"ws://127.0.0.1:19996/api/vms/{vm_id}/vnc"
    
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
    """
    try:
        manager = get_pc_client_manager()
        result = await manager.forward_request("GET", f"/api/vms/{vm_id}", b"", {})
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        return result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vms")
async def list_vms():
    """
    列出所有 VM
    """
    try:
        manager = get_pc_client_manager()
        result = await manager.forward_request("GET", "/api/vms", b"", {})
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        return result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/screenshot")
async def screenshot(vm_id: str):
    """
    获取 VM 截图（MCP 标准格式）
    
    返回 MCP 标准 content 数组格式
    """
    try:
        manager = get_pc_client_manager()
        result = await manager.forward_request("POST", f"/api/vms/{vm_id}/screenshot", b"", {})
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        body = result.get("body", {})
        return {
            "content": [
                {
                    "type": "image",
                    "data": body.get("data", ""),
                    "mimeType": f"image/{body.get('format', 'png')}"
                }
            ]
        }
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/keys")
async def send_keys(vm_id: str, keys: dict):
    """
    发送按键到 VM
    """
    try:
        manager = get_pc_client_manager()
        body = json.dumps({"keys": keys.get("keys", "")}).encode()
        result = await manager.forward_request("POST", f"/api/vms/{vm_id}/keys", body, {"content-type": "application/json"})
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        return result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/mouse/move")
async def mouse_move(vm_id: str, coords: dict):
    """
    移动鼠标
    """
    try:
        manager = get_pc_client_manager()
        body = json.dumps({"x": coords.get("x", 0), "y": coords.get("y", 0)}).encode()
        result = await manager.forward_request("POST", f"/api/vms/{vm_id}/mouse/move", body, {"content-type": "application/json"})
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        return result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vms/{vm_id}/mouse/click")
async def mouse_click(vm_id: str, button_data: dict):
    """
    鼠标点击
    """
    try:
        manager = get_pc_client_manager()
        body = json.dumps({"button": button_data.get("button", "left")}).encode()
        result = await manager.forward_request("POST", f"/api/vms/{vm_id}/mouse/click", body, {"content-type": "application/json"})
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        return result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ==================== 旧的 per-type WebRTC 路由已移除 ==========================
# 统一由 /webrtc/start 和 /webrtc/stop 处理（见文件末尾）


# ==================== 健康检查 ====================

@router.get("/health")
async def health_check():
    """
    检查 vmcontrol 服务健康状态
    """
    try:
        manager = get_pc_client_manager()
        if not manager.is_connected:
            return {"status": "unhealthy", "service": "vmcontrol", "error": "PC client not connected"}
        result = await manager.forward_request("GET", "/", b"", {}, timeout=5.0)
        healthy = result.get("status", 503) == 200
        return {"status": "healthy" if healthy else "unhealthy", "service": "vmcontrol"}
    except Exception as e:
        return {"status": "unhealthy", "service": "vmcontrol", "error": str(e)}


# ==================== 统一 WebRTC 入口（新）====================

@router.post("/webrtc/start")
async def webrtc_unified_start(body: dict):
    """
    统一 WebRTC 信令入口。
    前端只传 device_id + sdp_offer（可选 username），
    VmControl 从本地 Device Registry 查 device_type 并分发。
    """
    try:
        manager = get_pc_client_manager()
        req_body = json.dumps(body).encode()
        result = await manager.forward_request(
            "POST", "/api/webrtc/start",
            req_body, {"content-type": "application/json"},
            timeout=30.0,
        )
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        return result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webrtc/stop")
async def webrtc_unified_stop(body: dict):
    """
    统一 WebRTC 停止入口。
    """
    try:
        manager = get_pc_client_manager()
        req_body = json.dumps(body).encode()
        result = await manager.forward_request(
            "POST", "/api/webrtc/stop",
            req_body, {"content-type": "application/json"},
            timeout=10.0,
        )
        if result.get("status", 200) >= 400:
            raise HTTPException(status_code=result["status"], detail=str(result.get("body")))
        return result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
