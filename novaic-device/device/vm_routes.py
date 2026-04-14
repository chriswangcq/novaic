"""
VM API Endpoints

REST API for VM management (setup, start, stop, status).
Replaces Tauri's VM commands.

Phase3: vmcontrol is the single VM backend for runtime state. No local VM manager
fallback for VM runtime (start/stop/status/setup-status). Local vm_manager is still
used for QEMU process spawning and recovery; runtime queries go to vmcontrol.

Also includes Android emulator management APIs.
"""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.auth import check_agent_access, get_current_user
from device.vm import VmSetup, get_ssh_key_manager
from device.vm.deployer import get_vmuse_deployer
from device.pc_client import get_pc_client_manager

logger = logging.getLogger(__name__)

# Constants for setup status monitoring
SSH_TIMEOUT = 5
SSH_CONNECT_TIMEOUT = 3

router = APIRouter(prefix="/api/vm", tags=["vm"])


def _get_device_ports(agent) -> Dict[str, int]:
    """
    Get SSH and VMUSE ports from agent's devices (v38) or fallback to agent.vm.ports.
    When agent.devices is empty, directly queries devices table as fallback.
    
    Returns:
        Dict with 'ssh' and 'vmuse' ports
    """
    ssh_port = 20000  # default
    vmuse_port = 18000  # default
    
    # Try devices first (v38 unified model)
    if hasattr(agent, 'devices') and agent.devices:
        for device in agent.devices:
            if isinstance(device, dict):
                if device.get('type') == 'linux':
                    ports = device.get('ports', {})
                    if ports.get('ssh'):
                        ssh_port = ports['ssh']
                    if ports.get('vmuse'):
                        vmuse_port = ports['vmuse']
                    break
            else:
                # Device object
                if getattr(device, 'type', None) == 'linux':
                    ports = getattr(device, 'ports', {})
                    if ports.get('ssh'):
                        ssh_port = ports['ssh']
                    if ports.get('vmuse'):
                        vmuse_port = ports['vmuse']
                    break
    
    # Fallback to agent.vm.ports (legacy)
    if ssh_port == 20000 and hasattr(agent, 'vm') and agent.vm and agent.vm.ports:
        if agent.vm.ports.ssh:
            ssh_port = agent.vm.ports.ssh
        if agent.vm.ports.vmuse:
            vmuse_port = agent.vm.ports.vmuse
    
    return {'ssh': ssh_port, 'vmuse': vmuse_port}


def _get_device_image_path(agent) -> Optional[str]:
    """
    Get disk image path from agent's Linux device (v38) or fallback to agent.vm.image_path.
    Note: No file existence check - path is on local Mac, not cloud server.
    """
    if hasattr(agent, 'devices') and agent.devices:
        for device in agent.devices:
            if isinstance(device, dict) and device.get('type') == 'linux':
                return device.get('image_path')
            elif hasattr(device, 'type') and getattr(device, 'type', None) == 'linux':
                return getattr(device, 'image_path', None)
    if hasattr(agent, 'vm') and agent.vm:
        return agent.vm.image_path
    return None


# ==================== Request/Response Models ====================

class VmSetupRequest(BaseModel):
    """Request to setup VM for an agent."""
    agent_id: str
    source_image: str
    disk_size: str = "40G"
    use_cn_mirrors: bool = False


class VmStartRequest(BaseModel):
    """Request to start VM."""
    agent_id: str
    memory: str = "4096"
    cpus: int = 4
    pc_client_id: Optional[str] = None  # P2: 多 PC 时指定目标，未传则取第一个


class VmStopRequest(BaseModel):
    """Request to stop VM."""
    agent_id: str
    graceful: bool = True
    quick: bool = False  # Use shorter timeouts for app exit
    pc_client_id: Optional[str] = None  # P2: 多 PC 时指定目标


class SshKeyCreateRequest(BaseModel):
    """Request to create SSH key."""
    name: str = "custom"


class VmStatusResponse(BaseModel):
    """VM status response."""
    agent_id: str
    running: bool
    agent_healthy: bool
    mcp_healthy: bool
    ports: Dict[str, int]
    vnc_url: str  # vmcontrol WebSocket URL: ws://localhost:19996/api/vms/{agent_id}/vnc
    mcp_url: str
    pid: Optional[int] = None
    started_at: Optional[str] = None
    error_message: Optional[str] = None


# ==================== Environment Check ====================

@router.get("/environment")
async def check_environment(user_id: str = Depends(get_current_user)):
    """
    Check VM dependencies on the local Mac via VmControl (CloudBridge).
    Forwards to vmcontrol /api/vm/environment for full QEMU/qemu-img/UEFI/ISO check.
    """
    try:
        pc_manager = get_pc_client_manager(user_id)
        result = await pc_manager.forward_request("GET", "/api/vm/environment", b"", {}, timeout=10.0)
        if result.get("status", 500) >= 400:
            return {"ready": False, "platform": "unknown", "arch": "unknown", "dependencies": [], "message": str(result.get("body", "vmcontrol error"))}
        body = result.get("body", {})
        return body if isinstance(body, dict) else {"ready": False, "platform": "unknown", "arch": "unknown", "dependencies": [], "message": str(body)}
    except ConnectionError as e:
        return {"ready": False, "platform": "unknown", "arch": "unknown", "dependencies": [], "message": f"VmControl not connected: {e}"}


# ==================== Cloud Image (forward to vmcontrol) ====================

@router.get("/cloud-image/check")
async def check_cloud_image(
    os_type: str,
    os_version: str,
    user_id: str = Depends(get_current_user),
):
    """Check if cloud image exists locally. Forward via CloudBridge to vmcontrol."""
    try:
        pc_manager = get_pc_client_manager(user_id)
        path = f"/api/vm/cloud-image/check?os_type={os_type}&os_version={os_version}"
        result = await pc_manager.forward_request("GET", path, b"", {}, timeout=10.0)
        if result.get("status", 500) >= 400:
            raise HTTPException(status_code=500, detail=f"vmcontrol error: {result.get('body', '')}")
        return result.get("body", {})
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"VmControl not connected: {e}")


class CloudImageDownloadRequest(BaseModel):
    os_type: str
    os_version: str
    use_cn_mirrors: bool = False


@router.post("/cloud-image/download")
async def download_cloud_image(
    request: CloudImageDownloadRequest,
    user_id: str = Depends(get_current_user),
):
    """Download cloud image. Forward via CloudBridge to vmcontrol (long-running, timeout 3600s)."""
    try:
        pc_manager = get_pc_client_manager(user_id)
        body = json.dumps({
            "os_type": request.os_type,
            "os_version": request.os_version,
            "use_cn_mirrors": request.use_cn_mirrors,
        }).encode()
        result = await pc_manager.forward_request(
            "POST", "/api/vm/cloud-image/download",
            body, {"Content-Type": "application/json"},
            timeout=3600.0,
        )
        if result.get("status", 500) >= 400:
            err = result.get("body", "vmcontrol error")
            raise HTTPException(status_code=500, detail=str(err) if isinstance(err, str) else err)
        return result.get("body", {})

    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"VmControl not connected: {e}")


class DeployWaitRequest(BaseModel):
    agent_id: str
    ssh_port: int


@router.post("/deploy-wait")
async def deploy_wait(
    request: DeployWaitRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Wait for VM to be ready (SSH + cloud-init).
    Gateway fetches private_key and forwards to vmcontrol via CloudBridge.
    """
    check_agent_access(request.agent_id, user_id, None)
    try:
        private_key = get_ssh_key_manager().get_private_key_for_agent(request.agent_id)
        pc_manager = get_pc_client_manager(user_id)
        body = json.dumps({
            "ssh_port": request.ssh_port,
            "private_key": private_key,
        }).encode()
        result = await pc_manager.forward_request(
            "POST", "/api/vm/deploy-wait",
            body, {"Content-Type": "application/json"},
            timeout=3600.0,  # cloud-init can take 10-30 min
        )
        if result.get("status", 500) >= 400:
            err = result.get("body", "vmcontrol error")
            raise HTTPException(status_code=500, detail=str(err) if isinstance(err, str) else err)
        return result.get("body", {})

    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"VmControl not connected: {e}")


# ==================== VM Setup ====================

@router.post("/setup")
async def setup_vm(request: VmSetupRequest, user_id: str = Depends(get_current_user)):
    """
    Setup VM for an agent — forwarded to local VmControl (which has qemu-img/hdiutil).
    """
    check_agent_access(request.agent_id, user_id, None)
    try:
        # Get SSH pubkey for cloud-init
        ssh_pubkey = ""
        try:
            ssh_pubkey = get_ssh_key_manager().get_public_key_for_agent(request.agent_id)
        except Exception as e:
            logger.warning(f"[VM API] SSH key lookup failed for agent {request.agent_id}: {e}")

        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.vm_setup(request.agent_id, {
            "source_image": request.source_image or "",
            "ssh_pubkey": ssh_pubkey,
            "use_cn_mirrors": request.use_cn_mirrors,
            "disk_size": request.disk_size or "40G",
        })
        status_code = ctrl_result.get("status", 200)
        body = ctrl_result.get("body", {})

        if isinstance(status_code, int) and status_code >= 400:
            err = body.get("error", str(body)) if isinstance(body, dict) else str(body)
            raise HTTPException(status_code=500, detail=err)

        disk_path = body.get("disk_path", "") if isinstance(body, dict) else ""
        if disk_path:
            try:
                from device.config_agents import get_agent_config_manager
                agent_manager = get_agent_config_manager()
                agent_manager.update_agent(
                    request.agent_id,
                    vm_config={"image_path": disk_path},
                    user_id=user_id,
                )
                logger.info(f"[VM API] Saved disk_path to agent {request.agent_id}: {disk_path}")
            except Exception as e:
                logger.warning(f"[VM API] Failed to update agent disk_path: {e}")

        return {"success": True, **(body if isinstance(body, dict) else {})}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"VmControl (Tauri App) not connected: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VM API] Setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VM Lifecycle ====================

def _resolve_vm_id_for_agent(agent_id: str, db=None) -> str:
    """
    Resolve agent_id to device_id for VM operations (start/stop).
    Both main and vm_user bindings use device_id (VM is per-device, not per-subject).
    """
    from device.entity_store import get_entity_store
    binding = get_entity_store().get("agent-binding", "", agent_id, params={"agent_id": agent_id})
    if binding:
        return binding.get("device_id", agent_id)
    return agent_id


def _ensure_device_available_for_vm(vm_id: str, user_id: str, db=None) -> dict:
    """
    CR: 校验 device 存在且可用，否则 raise。返回 device_row 供多 PC 路由使用。
    vm_id 无对应 device 时返回 400（如 agent 未绑定 device）。
    """
    from device.entity_store import get_entity_store
    device_row = get_entity_store().get("devices", user_id, vm_id)
    if device_row is None:
        raise HTTPException(status_code=400, detail="Device not found for this agent")
    from device.devices import ensure_device_available
    ensure_device_available(device_row, user_id)
    return device_row


@router.post("/start")
async def start_vm(request: VmStartRequest, auto_deploy_vmuse: bool = True, user_id: str = Depends(get_current_user)):
    """Start a Linux VM via CloudBridge → VmControl on local Mac."""
    check_agent_access(request.agent_id, user_id, None)
    try:
        from device.config_agents import get_agent_config_manager
        agent_manager = get_agent_config_manager()
        agent = agent_manager.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")

        vm_id = _resolve_vm_id_for_agent(request.agent_id)
        device_row = _ensure_device_available_for_vm(vm_id, user_id)

        # Get VM config from agent/device
        ports = _get_device_ports(agent)
        image_path = _get_device_image_path(agent) or ""

        # Fetch vm_users display_nums so VmControl adds hostfwd for subuser VNC ports (survives VM restart)
        from device.entity_store import get_entity_store
        vm_user_rows = get_entity_store().list(
            "vm-users", user_id,
            params={"device_id": vm_id},
            order_by="display_num ASC",
        )
        vm_user_display_nums = [r["display_num"] for r in vm_user_rows]

        pc_id = request.pc_client_id or device_row.get("pc_client_id")
        pc_manager = get_pc_client_manager(user_id=user_id, pc_client_id=pc_id)
        try:
            body = {
                "memory": str(getattr(getattr(agent, 'vm', None), 'memory', 4096) or 4096),
                "cpus": getattr(getattr(agent, 'vm', None), 'cpus', 4) or 4,
                "ssh_port": ports.get('ssh', 20000),
                "vmuse_port": ports.get('vmuse', 18000),
                "image_path": image_path,
                "name": agent.name or "",
                "vm_user_display_nums": vm_user_display_nums,
            }
            ctrl_result = await pc_manager.vm_start(vm_id=vm_id, body=body)
            status_code = ctrl_result.get("status", 200)
            result = ctrl_result.get("body", {})

            if isinstance(status_code, int) and status_code >= 400:
                raise HTTPException(status_code=500, detail=f"VmControl error: {result}")

            vm_status = result.get("status", "starting") if isinstance(result, dict) else "starting"
        except ConnectionError as e:
            raise HTTPException(status_code=503, detail=f"CloudBridge not connected: {e}")

        # VMUSE deployment is done via VmControl/cloud-init, not SSH from remote Gateway

        return {"success": True, "status": vm_status, **(result if isinstance(result, dict) else {})}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VM API] Start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_vm(request: VmStopRequest, user_id: str = Depends(get_current_user)):
    """
    Stop VM for an agent via vmcontrol backend.
    """
    check_agent_access(request.agent_id, user_id, None)
    vm_id = _resolve_vm_id_for_agent(request.agent_id)
    device_row = _ensure_device_available_for_vm(vm_id, user_id)
    pc_id = request.pc_client_id or device_row.get("pc_client_id")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id, pc_client_id=pc_id)
        ctrl_result = await pc_manager.vm_shutdown(vm_id)
        result = ctrl_result.get("body", {})
        return {"success": True, "status": "shutdown_sent", **result}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        logger.error(f"[VM API] Stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-all")
async def stop_all_vms(quick: bool = False, graceful: bool = True, user_id: str = Depends(get_current_user)):
    """Stop all running VMs belonging to the current user.

    Args:
        quick: Use shorter timeouts for faster shutdown (for app exit)
        graceful: Try SSH poweroff before force kill

    CR R3: 仅停止已绑定 device 的 agent；按 pc_client_id 分组，多 PC 时分别路由。
    """
    from device.entity_store import get_entity_store
    from collections import defaultdict

    user_agent_ids = [
        row["id"]
        for row in get_entity_store().list("agents", user_id)
    ]

    store = get_entity_store()
    vm_to_pc: Dict[str, str] = {}
    for aid in user_agent_ids:
        vm_id = _resolve_vm_id_for_agent(aid)
        if vm_id == aid:
            continue  # 无 device 绑定，跳过
        row = store.get("devices", user_id, vm_id)
        if row:
            pc_id = (row.get("pc_client_id") or "").strip()
            if pc_id:
                vm_to_pc[vm_id] = pc_id

    # 按 pc_client_id 分组
    pc_to_vms: Dict[str, List[str]] = defaultdict(list)
    for vm_id, pc_id in vm_to_pc.items():
        pc_to_vms[pc_id].append(vm_id)

    results = {}
    for pc_id, vm_ids in pc_to_vms.items():
        try:
            pc_manager = get_pc_client_manager(user_id=user_id, pc_client_id=pc_id)
            for vm_id in vm_ids:
                try:
                    ctrl_result = await pc_manager.vm_shutdown(vm_id)
                    results[vm_id] = ctrl_result.get("body", {})
                except Exception as e:
                    results[vm_id] = {"error": str(e)}
        except ConnectionError:
            for vm_id in vm_ids:
                results[vm_id] = {"error": "PC client not connected"}
        except Exception as e:
            for vm_id in vm_ids:
                results[vm_id] = {"error": str(e)}

    return {"success": True, "results": results}


# ==================== VM Status ====================

@router.get("/status/{agent_id}")
async def get_vm_status(agent_id: str, user_id: str = Depends(get_current_user)):
    """Get VM status for a specific agent."""
    check_agent_access(agent_id, user_id, None)
    vm_id = _resolve_vm_id_for_agent(agent_id)
    device_row = _ensure_device_available_for_vm(vm_id, user_id)
    pc_id = device_row.get("pc_client_id")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id, pc_client_id=pc_id)
        ctrl_result = await pc_manager.vm_status(vm_id)
        if ctrl_result.get("status") == 404:
            raise HTTPException(status_code=404, detail="VM not found")
        if ctrl_result.get("status", 200) >= 500:
            raise HTTPException(status_code=500, detail=f"vmcontrol error: {ctrl_result.get('status')}")
        vm_info = ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"vmcontrol unavailable: {str(e)}")

    if not vm_info:
        raise HTTPException(status_code=404, detail="VM not found")

    running = (vm_info.get("status") or "").lower() in {"running", "started", "active"}

    ports: Dict[str, int] = {}
    try:
        from device.config_agents import get_agent_config_manager
        agent = get_agent_config_manager().get_agent(agent_id)
        if agent:
            ports = _get_device_ports(agent)
    except Exception:
        ports = {}

    return VmStatusResponse(
        agent_id=agent_id,
        running=running,
        agent_healthy=True,
        mcp_healthy=False,
        ports=ports,
        vnc_url=f"ws://localhost:19996/api/vms/{agent_id}/vnc",
        mcp_url="",
        pid=vm_info.get("pid"),
        started_at=vm_info.get("started_at"),
        error_message=vm_info.get("error_message"),
    )


@router.get("/status")
async def get_all_vm_status(user_id: str = Depends(get_current_user)):
    """Get VM status for all agents belonging to the current user."""
    from device.entity_store import get_entity_store
    user_agent_ids = {
        row["id"]
        for row in get_entity_store().list("agents", user_id)
    }

    vm_id_to_agents: Dict[str, List[str]] = {}
    for agent_id in user_agent_ids:
        vm_id = _resolve_vm_id_for_agent(agent_id)
        vm_id_to_agents.setdefault(vm_id, []).append(agent_id)

    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.vm_list()
        status_code = ctrl_result.get("status", 200)
        if isinstance(status_code, int) and status_code >= 400:
            logger.warning("[VM API] vm_list returned error: status=%s body=%s", status_code, ctrl_result.get("body"))
            return {}
        vms = ctrl_result.get("body", [])
        if not isinstance(vms, list):
            vms = []
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except asyncio.TimeoutError:
        logger.warning("[VM API] vm_list timeout — PC client may be slow or disconnected")
        return {}
    except Exception as e:
        logger.warning("[VM API] vm_list failed: %s", e)
        raise HTTPException(status_code=503, detail=f"vmcontrol unavailable: {str(e)}")

    result: Dict[str, VmStatusResponse] = {}
    for vm in vms:
        vm_id = vm.get("id")
        if not vm_id:
            continue
        agent_ids = vm_id_to_agents.get(vm_id, [])
        running = (vm.get("status") or "").lower() in {"running", "started", "active"}
        for agent_id in agent_ids:
            result[agent_id] = VmStatusResponse(
                agent_id=agent_id,
                running=running,
                agent_healthy=True,
                mcp_healthy=False,
                ports={},
                vnc_url=f"ws://localhost:19996/api/vms/{vm_id}/vnc",
                mcp_url="",
                pid=vm.get("pid"),
                started_at=vm.get("started_at"),
                error_message=vm.get("error_message"),
            )
    return result


@router.get("/running")
async def get_running_agents(user_id: str = Depends(get_current_user)):
    """Get list of running agent IDs for the current user."""
    from device.entity_store import get_entity_store
    user_agent_ids = {
        row["id"]
        for row in get_entity_store().list("agents", user_id)
    }
    vm_id_to_agents: Dict[str, List[str]] = {}
    for agent_id in user_agent_ids:
        vm_id = _resolve_vm_id_for_agent(agent_id)
        vm_id_to_agents.setdefault(vm_id, []).append(agent_id)

    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.vm_list()
        status_code = ctrl_result.get("status", 200)
        if isinstance(status_code, int) and status_code >= 400:
            logger.warning("[VM API] vm_list (running) returned error: status=%s", status_code)
            return {"agents": []}
        vms = ctrl_result.get("body", [])
        if not isinstance(vms, list):
            vms = []
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except asyncio.TimeoutError:
        return {"agents": []}
    except Exception as e:
        logger.warning("[VM API] vm_list (running) failed: %s", e)
        raise HTTPException(status_code=503, detail=f"vmcontrol unavailable: {str(e)}")

    agents = []
    for vm in vms:
        vm_id = vm.get("id")
        if not vm_id or (vm.get("status") or "").lower() not in {"running", "started", "active"}:
            continue
        for agent_id in vm_id_to_agents.get(vm_id, []):
            agents.append(agent_id)
    return {"agents": agents}


@router.get("/is-running/{agent_id}")
async def is_vm_running(agent_id: str, user_id: str = Depends(get_current_user)):
    """Check if a specific VM is running."""
    check_agent_access(agent_id, user_id, None)
    vm_id = _resolve_vm_id_for_agent(agent_id)
    device_row = _ensure_device_available_for_vm(vm_id, user_id)
    pc_id = device_row.get("pc_client_id")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id, pc_client_id=pc_id)
        ctrl_result = await pc_manager.vm_status(vm_id)
        status_code = ctrl_result.get("status", 200)
        if status_code == 404:
            return {"running": False}
        if isinstance(status_code, int) and status_code >= 400:
            logger.warning("[VM API] vm_status failed for %s: status=%s", agent_id, status_code)
            return {"running": False}
        vm_info = ctrl_result.get("body", {})
        running = (vm_info.get("status") or "").lower() in {"running", "started", "active"}
        return {"running": running}
    except (ConnectionError, asyncio.TimeoutError):
        return {"running": False}
    except Exception as e:
        logger.warning("[VM API] vm_status failed for %s: %s", agent_id, e)
        return {"running": False}


# ==================== SSH Key Management ====================

@router.get("/ssh/keys")
def list_ssh_keys(user_id: str = Depends(get_current_user)):
    """List SSH keys for the current user."""
    manager = get_ssh_key_manager()
    keys = manager.list_keys(user_id)
    return {"keys": keys}


@router.get("/ssh/pubkey")
def get_ssh_pubkey(user_id: str = Depends(get_current_user)):
    """Get the default public key for the current user."""
    manager = get_ssh_key_manager()
    pubkey = manager.get_public_key(user_id)
    return {"public_key": pubkey}


@router.get("/ssh/private-key")
def get_ssh_private_key(user_id: str = Depends(get_current_user)):
    """
    Get the default private key.

    Used by Tauri for SSH/SCP commands to VM.
    The private key is stored in Gateway's database.
    """
    manager = get_ssh_key_manager()
    key = manager.get_or_create_default_key(user_id)
    return {"private_key": key["private_key"]}


@router.post("/ssh/keys")
def create_ssh_key(request: SshKeyCreateRequest, user_id: str = Depends(get_current_user)):
    """Create a new SSH key pair."""
    manager = get_ssh_key_manager()
    key = manager.create_key(user_id=user_id, name=request.name)
    return {"success": True, **key}


@router.delete("/ssh/keys/{key_id}")
def delete_ssh_key(key_id: str, user_id: str = Depends(get_current_user)):
    """Delete an SSH key."""
    manager = get_ssh_key_manager()
    success = manager.delete_key(key_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete key (not found or is default)")
    return {"success": True}


# ==================== VNC Status Check ====================

@router.get("/vnc/status/{agent_id}")
async def get_vnc_status(agent_id: str, user_id: str = Depends(get_current_user)):
    """
    Check VNC connection status for a specific agent.
    
    Performs multi-layer checks:
    1. VM process status (PID exists and running)
    2. VNC socket file existence
    3. VmControl service health
    4. VmControl VM registration
    
    Args:
        agent_id: Agent ID (UUID)
    
    Returns:
        {
            "available": bool,              # VNC is ready to connect
            "vm_running": bool,             # VM process is running
            "vnc_socket_exists": bool,      # VNC socket file exists
            "vnc_socket_path": str,         # VNC socket file path
            "vmcontrol_healthy": bool,      # VmControl service is healthy
            "vm_registered": bool,          # VM is registered in VmControl
            "vnc_url": str,                 # VNC WebSocket URL
            "reason": str                   # Status reason or error message
        }
    """
    check_agent_access(agent_id, user_id, None)
    vm_id = _resolve_vm_id_for_agent(agent_id)
    device_row = _ensure_device_available_for_vm(vm_id, user_id)
    pc_id = device_row.get("pc_client_id")
    result = {
        "available": False,
        "vm_running": False,
        "vnc_socket_exists": None,
        "vnc_socket_path": None,
        "vmcontrol_healthy": False,
        "vm_registered": False,
        "vnc_url": f"ws://localhost:19996/api/vms/{vm_id}/vnc",
        "reason": ""
    }

    # 1. Check vmcontrol health via CloudBridge
    try:
        pc_manager = get_pc_client_manager(user_id=user_id, pc_client_id=pc_id)
        result["vmcontrol_healthy"] = await pc_manager.vm_health()
    except Exception as e:
        logger.warning(f"[VNC Status] VmControl health check failed: {e}")
        result["vmcontrol_healthy"] = False

    if not result["vmcontrol_healthy"]:
        result["reason"] = "VmControl service not available"
        return result

    # 2. Check VM registration + runtime state via vmcontrol
    try:
        ctrl_result = await pc_manager.vm_status(vm_id)
        if ctrl_result.get("status", 200) < 400:
            vm_info = ctrl_result.get("body", {})
            result["vm_registered"] = True
            vm_status_str = (vm_info.get("status") or "").lower()
            result["vm_running"] = vm_status_str in {"running", "started", "active"}
        else:
            result["vm_registered"] = False
    except Exception as e:
        logger.warning(f"[VNC Status] Failed to get VM status from VmControl: {e}")
        result["vm_registered"] = False

    if not result["vm_registered"]:
        result["reason"] = "VM not registered in VmControl"
        return result

    if not result["vm_running"]:
        result["reason"] = "VM is registered but not running"
        return result

    result["available"] = True
    result["reason"] = "VNC ready (vmcontrol)"
    return result


# ==================== VMUSE Deployment ====================

def _deploy_vmuse_background(agent_id: str, ssh_port: int, vmuse_port: int):
    """
    Background task for VMUSE deployment.
    Uses aggressive deployment strategy by default (retry until success).
    """
    try:
        logger.info(f"[VMUSE Deploy] Starting background deployment for agent {agent_id}")
        deployer = get_vmuse_deployer()
        
        # Deploy with aggressive strategy (retry until success)
        result = deployer.deploy(
            agent_id=agent_id,
            ssh_port=ssh_port,
            aggressive=True,  # Use aggressive strategy: deploy immediately, retry until success
        )
        
        if result["success"]:
            attempts = result.get("attempts", "unknown")
            logger.info(f"[VMUSE Deploy] ✅ Deployment succeeded for agent {agent_id} (attempts: {attempts})")
            
            # Verify health
            if deployer.health_check(vmuse_port=vmuse_port):
                logger.info(f"[VMUSE Deploy] ✅ Health check passed for agent {agent_id}")
            else:
                logger.warning(f"[VMUSE Deploy] ⚠️  Health check failed for agent {agent_id}")
        else:
            attempts = result.get("attempts", "unknown")
            logger.error(f"[VMUSE Deploy] ❌ Deployment failed for agent {agent_id} after {attempts} attempts: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"[VMUSE Deploy] Background task error for agent {agent_id}: {e}", exc_info=True)


@router.post("/{agent_id}/deploy-vmuse")
def deploy_vmuse_manual(
    agent_id: str,
    aggressive: bool = True,
    wait: bool = False,
    user_id: str = Depends(get_current_user),
):
    """
    Manually trigger VMUSE code deployment to VM.
    
    Runs in background by default (returns immediately). Deploy takes 5-10+ min
    (pip install playwright downloads browser binaries).
    
    Useful for:
    - Updating VMUSE code after changes
    - Retrying failed automatic deployment
    - Deploying to VMs created before auto-deployment was added
    
    Args:
        agent_id: Agent ID
        aggressive: Use aggressive deployment (retry until success). Default: True
        wait: If True, wait for deploy to complete (can take 10+ min). Default: False
    
    Returns:
        {"scheduled": true} if wait=False, else full deployment result
    """
    check_agent_access(agent_id, user_id, None)
    try:
        from device.config_agents import get_agent_config_manager
        agent_manager = get_agent_config_manager()
        agent = agent_manager.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        ports = _get_device_ports(agent)
        if not ports['ssh']:
            raise HTTPException(status_code=400, detail="Agent ports not configured")
        logger.info(f"[VM API] Deploy VMUSE for agent {agent_id}: ssh_port={ports['ssh']}, vmuse_port={ports['vmuse']}")
        
        def _run_deploy():
            deployer = get_vmuse_deployer()
            result = deployer.deploy(
                agent_id=agent_id,
                ssh_port=ports['ssh'],
                aggressive=aggressive,
            )
            if result["success"]:
                deployer.health_check(vmuse_port=ports['vmuse'])
        
        if wait:
            # Synchronous: caller waits (can take 10+ min)
            deployer = get_vmuse_deployer()
            result = deployer.deploy(
                agent_id=agent_id,
                ssh_port=ports['ssh'],
                aggressive=aggressive,
            )
            if result["success"]:
                result["health_check"] = deployer.health_check(vmuse_port=ports['vmuse'])
            return result
        
        # Background: return immediately
        import threading
        t = threading.Thread(target=_run_deploy, daemon=True)
        t.start()
        logger.info(f"[VM API] Deploy VMUSE scheduled for agent {agent_id}")
        return {
            "scheduled": True,
            "agent_id": agent_id,
            "ssh_port": ports["ssh"],
            "vmuse_port": ports["vmuse"],
            "message": f"Deployment started in background. Check GET /api/vm/{agent_id}/vmuse-health for status.",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VM API] Deploy VMUSE failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/vmuse-health")
def check_vmuse_health(agent_id: str, user_id: str = Depends(get_current_user)):
    """
    Check VMUSE service health for an agent.

    Args:
        agent_id: Agent ID

    Returns:
        Health status
    """
    check_agent_access(agent_id, user_id, None)
    try:
        from device.config_agents import get_agent_config_manager
        agent_manager = get_agent_config_manager()
        agent = agent_manager.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        ports = _get_device_ports(agent)
        if not ports['vmuse']:
            raise HTTPException(status_code=400, detail="Agent ports not configured")
        
        deployer = get_vmuse_deployer()
        healthy = deployer.health_check(vmuse_port=ports['vmuse'])
        
        return {
            "agent_id": agent_id,
            "healthy": healthy,
            "vmuse_port": ports['vmuse'],
            "url": f"http://127.0.0.1:{ports['vmuse']}",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VM API] Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _run_ssh_command(key_path: Path, ssh_port: int, command: str, timeout: int = SSH_TIMEOUT) -> subprocess.CompletedProcess:
    """Helper function to run SSH commands with standard options."""
    return subprocess.run(
        [
            "ssh",
            "-i", str(key_path),
            "-p", str(ssh_port),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT}",
            "ubuntu@127.0.0.1",
            command
        ],
        capture_output=True,
        timeout=timeout,
        text=True,
    )


@router.get("/{agent_id}/setup-status")
async def get_setup_status(agent_id: str, user_id: str = Depends(get_current_user)):
    """
    Get detailed setup status for a VM during initialization.

    Phase3: vmcontrol is the sole source of VM runtime truth.
    VM process status (created/booting/running) is determined via vmcontrol get_vm_info.
    Cloud-init and SSH checks remain unchanged.

    Returns progress information for frontend to display:
    - Phase: creating/booting/cloud-init/vmuse-deploy/complete/error
    - Progress: 0-100%
    - Message: Human-readable status
    - Steps: Detailed breakdown of each phase

    Args:
        agent_id: Agent ID

    Returns:
        Detailed setup status
    """
    check_agent_access(agent_id, user_id, None)
    try:
        from device.config_agents import get_agent_config_manager

        agent_manager = get_agent_config_manager()
        agent = agent_manager.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        logger.debug(f"[Setup Status] Checking status for agent {agent_id}")

        # Base response structure
        response = {
            "agent_id": agent_id,
            "phase": "unknown",
            "progress": 0,
            "message": "初始化中...",
            "steps": {},
            "error": None,
        }

        # Get SSH key path for the agent's owner
        key_path = None
        try:
            key_path = get_ssh_key_manager().get_private_key_path_for_agent(agent_id)
        except Exception as e:
            logger.error(f"[Setup Status] Failed to get SSH key: {e}")
            return {
                "agent_id": agent_id,
                "phase": "error",
                "progress": 0,
                "message": "SSH 密钥配置错误",
                "error": str(e),
                "steps": {},
            }

        # Product design change: VM is ready as soon as it boots, no need to wait for cloud-init.
        # Always return "complete" to skip the initialization progress display.
        response.update({
            "phase": "complete",
            "progress": 100,
            "message": "环境已就绪",
            "steps": {
                "vm_created": True,
                "vm_booted": True,
                "cloud_init": True,
                "vmuse_deployed": True,
            }
        })
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VM API] Get setup status failed for {agent_id}: {e}", exc_info=True)
        return {
            "agent_id": agent_id,
            "phase": "error",
            "progress": 0,
            "message": "获取状态失败",
            "error": str(e),
            "steps": {},
        }


# ==================== Android Emulator Management ====================

class AndroidStartRequest(BaseModel):
    """Request to start Android emulator."""
    agent_id: str


class AndroidStartResponse(BaseModel):
    """Response for Android emulator start."""
    success: bool
    device_serial: Optional[str] = None
    message: Optional[str] = None


class AndroidStopRequest(BaseModel):
    """Request to stop Android emulator."""
    agent_id: str


class AndroidStopResponse(BaseModel):
    """Response for Android emulator stop."""
    success: bool
    message: Optional[str] = None


class AndroidStatusResponse(BaseModel):
    """Response for Android emulator status."""
    agent_id: str
    has_android: bool
    avd_name: Optional[str] = None
    device_serial: Optional[str] = None
    running: bool = False
    message: Optional[str] = None


@router.post("/android/start", response_model=AndroidStartResponse)
async def start_android(request: AndroidStartRequest, user_id: str = Depends(get_current_user)):
    """
    Start Android emulator for an agent.

    1. Get agent configuration
    2. Check if agent has Android config
    3. Call vmcontrol API to start emulator
    4. Update agent's device_serial
    5. Return result
    """
    check_agent_access(request.agent_id, user_id, None)
    from device.config_agents import get_agent_config_manager
    from device.config_agents_db import AndroidConfig

    agent_id = request.agent_id
    logger.info(f"[Android API] Starting emulator for agent {agent_id}")
    
    try:
        # 1. Get agent configuration
        manager = get_agent_config_manager()
        agent = manager.get_agent(agent_id)
        
        if not agent:
            return AndroidStartResponse(
                success=False,
                message=f"Agent not found: {agent_id}"
            )
        
        # 2. Check if agent has Android config (now independent field)
        if not agent.android:
            return AndroidStartResponse(
                success=False,
                message="Agent does not have Android configuration"
            )
        
        android_config = agent.android
        
        # Check if AVD name is configured
        if not android_config.avd_name:
            return AndroidStartResponse(
                success=False,
                message="AVD name not configured for this agent"
            )
        
        # 3. Call VmControl via CloudBridge to start emulator
        pc_manager = get_pc_client_manager(user_id=user_id)
        payload = {
            "avd": android_config.avd_name,
            "headless": True,
            "wait_boot": True,
            "timeout": 120
        }
        logger.info(f"[Android API] Calling VmControl via CloudBridge: android_emulator_start")
        logger.debug(f"[Android API] Payload: {payload}")

        try:
            ctrl_result = await pc_manager.android_emulator_start(payload)
        except ConnectionError as e:
            return AndroidStartResponse(success=False, message=f"PC client not connected: {e}")

        result = ctrl_result.get("body", {})
        logger.info(f"[Android API] VmControl response: {result}")

        if ctrl_result.get("status", 200) != 200:
            return AndroidStartResponse(success=False, message=result.get("message", f"Failed: status {ctrl_result.get('status')}"))

        if not result.get("success"):
            return AndroidStartResponse(success=False, message=result.get("message", "Failed to start emulator"))

        # 4. Update agent's device_serial
        device_info = result.get("device", {})
        device_serial = device_info.get("serial")

        if device_serial:
            # Update Android config with new device_serial
            updated_android_config = AndroidConfig(
                device_serial=device_serial,
                managed=android_config.managed,
                avd_name=android_config.avd_name
            )
            manager.update_agent(agent_id, android_config=updated_android_config, user_id=user_id)
            logger.info(f"[Android API] Updated device_serial to {device_serial}")

        # 5. Return result
        return AndroidStartResponse(
            success=True,
            device_serial=device_serial,
            message=result.get("message", "Emulator started successfully")
        )

    except Exception as e:
        logger.error(f"[Android API] Error starting emulator: {e}", exc_info=True)
        return AndroidStartResponse(
            success=False,
            message=str(e)
        )


@router.post("/android/stop", response_model=AndroidStopResponse)
async def stop_android(request: AndroidStopRequest, user_id: str = Depends(get_current_user)):
    """
    Stop Android emulator for an agent.

    1. Get agent configuration
    2. Get device_serial
    3. Call vmcontrol API to stop emulator
    4. Return result
    """
    check_agent_access(request.agent_id, user_id, None)
    from device.config_agents import get_agent_config_manager

    agent_id = request.agent_id
    logger.info(f"[Android API] Stopping emulator for agent {agent_id}")
    
    try:
        # 1. Get agent configuration
        manager = get_agent_config_manager()
        agent = manager.get_agent(agent_id)
        
        if not agent:
            return AndroidStopResponse(
                success=False,
                message=f"Agent not found: {agent_id}"
            )
        
        # 2. Get device_serial (android is now independent field)
        if not agent.android:
            return AndroidStopResponse(
                success=False,
                message="Agent does not have Android configuration"
            )
        
        device_serial = agent.android.device_serial
        
        if not device_serial:
            return AndroidStopResponse(
                success=False,
                message="No device_serial found for this agent. Emulator may not be running."
            )
        
        # 3. Call VmControl via CloudBridge to stop emulator
        pc_manager = get_pc_client_manager(user_id=user_id)
        try:
            ctrl_result = await pc_manager.android_emulator_stop({"serial": device_serial})
        except ConnectionError as e:
            return AndroidStopResponse(success=False, message=f"PC client not connected: {e}")

        result = ctrl_result.get("body", {})
        logger.info(f"[Android API] VmControl response: {result}")

        if ctrl_result.get("status", 200) != 200:
            return AndroidStopResponse(success=False, message=f"vmcontrol returned {ctrl_result.get('status')}: {result}")

        # 4. Return result
        return AndroidStopResponse(success=result.get("success", False), message=result.get("message", "Emulator stopped"))

    except Exception as e:
        logger.error(f"[Android API] Error stopping emulator: {e}", exc_info=True)
        return AndroidStopResponse(
            success=False,
            message=str(e)
        )


@router.get("/android/status/{agent_id}", response_model=AndroidStatusResponse)
async def get_android_status(agent_id: str, user_id: str = Depends(get_current_user)):
    """
    Get Android emulator status for an agent.
    
    Checks:
    1. Agent configuration for Android settings
    2. Device serial from config
    3. Actual device status from vmcontrol
    """
    check_agent_access(agent_id, user_id, None)
    from device.config_agents import get_agent_config_manager

    logger.info(f"[Android API] Getting status for agent {agent_id}")

    try:
        # 1. Get agent configuration
        manager = get_agent_config_manager()
        agent = manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        # 2. Check if agent has Android config (now independent field)
        if not agent.android:
            return AndroidStatusResponse(
                agent_id=agent_id,
                has_android=False,
                message="Agent does not have Android configuration"
            )
        
        android_config = agent.android
        device_serial = android_config.device_serial
        avd_name = android_config.avd_name
        
        # 3. If we have a device_serial, check actual status via CloudBridge
        running = False
        if device_serial:
            try:
                pc_manager = get_pc_client_manager(user_id=user_id)
                ctrl_result = await pc_manager.android_devices()
                if ctrl_result.get("status") == 200:
                    result = ctrl_result.get("body", {})
                    devices = result.get("devices", [])
                    for device in devices:
                        if device.get("serial") == device_serial:
                            status = device.get("status", "")
                            running = status in ("online", "device", "connected")
                            break
            except Exception as e:
                logger.warning(f"[Android API] Failed to check device status: {e}")
        
        return AndroidStatusResponse(
            agent_id=agent_id,
            has_android=True,
            avd_name=avd_name,
            device_serial=device_serial if device_serial else None,
            running=running,
            message="Emulator is running" if running else "Emulator is not running"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Android API] Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Android Device/AVD Management (Proxy to vmcontrol) ====================

@router.get("/android/devices")
async def list_android_devices(user_id: str = Depends(get_current_user)):
    """列出所有 Android 设备"""
    logger.info("[Android API] Listing Android devices")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.android_devices()
        if ctrl_result.get("status", 200) != 200:
            raise HTTPException(status_code=ctrl_result.get("status", 503), detail=str(ctrl_result.get("body", {})))
        return ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/android/avds")
async def list_avds(user_id: str = Depends(get_current_user)):
    """列出所有 AVD"""
    logger.info("[Android API] Listing AVDs")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.android_avds()
        if ctrl_result.get("status", 200) != 200:
            raise HTTPException(status_code=ctrl_result.get("status", 503), detail=str(ctrl_result.get("body", {})))
        return ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/android/system-image/check")
async def check_system_image(user_id: str = Depends(get_current_user)):
    """检查 Android 系统镜像"""
    logger.info("[Android API] Checking system image")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.android_system_image_check()
        if ctrl_result.get("status", 200) != 200:
            raise HTTPException(status_code=ctrl_result.get("status", 503), detail=str(ctrl_result.get("body", {})))
        return ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/android/device-definitions")
async def list_device_definitions(user_id: str = Depends(get_current_user)):
    """列出设备定义"""
    logger.info("[Android API] Listing device definitions")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.android_device_definitions()
        if ctrl_result.get("status", 200) != 200:
            raise HTTPException(status_code=ctrl_result.get("status", 503), detail=str(ctrl_result.get("body", {})))
        return ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateAvdRequest(BaseModel):
    """Request to create AVD."""
    avd_name: str
    device: Optional[str] = None
    memory: Optional[int] = None
    cores: Optional[int] = None


@router.post("/android/avd/create")
async def create_avd(request: CreateAvdRequest, user_id: str = Depends(get_current_user)):
    """创建 AVD"""
    logger.info(f"[Android API] Creating AVD: {request.avd_name}")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        payload = {"name": request.avd_name}
        if request.device:
            payload["device"] = request.device
        if request.memory:
            payload["memory"] = str(request.memory)
        if request.cores:
            payload["cores"] = request.cores
        ctrl_result = await pc_manager.android_avd_create(payload)
        if ctrl_result.get("status", 200) != 200:
            raise HTTPException(status_code=ctrl_result.get("status", 503), detail=str(ctrl_result.get("body", {})))
        return ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/android/avd/{avd_name}")
async def delete_avd(avd_name: str, user_id: str = Depends(get_current_user)):
    """删除 AVD — 仅允许删除属于当前用户某个 agent 的 AVD"""
    from device.entity_store import get_entity_store
    # Verify ownership: the avd_name must match an agent owned by this user
    user_agents = get_entity_store().list("agents", user_id)
    owned_avd_names = {
        avd
        for a in user_agents
        if (avd := (a.get("android_config") or {}).get("avd_name")) is not None
    }
    if avd_name not in owned_avd_names:
        raise HTTPException(
            status_code=403,
            detail=f"AVD '{avd_name}' does not belong to any of your agents",
        )
    logger.info(f"[Android API] Deleting AVD: {avd_name}")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.android_avd_delete(avd_name)
        if ctrl_result.get("status", 200) != 200:
            raise HTTPException(status_code=ctrl_result.get("status", 503), detail=str(ctrl_result.get("body", {})))
        return ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/android/scrcpy/status")
async def check_scrcpy_status(user_id: str = Depends(get_current_user)):
    """检查 scrcpy 可用性"""
    logger.info("[Android API] Checking scrcpy status")
    try:
        pc_manager = get_pc_client_manager(user_id=user_id)
        ctrl_result = await pc_manager.android_scrcpy_status()
        if ctrl_result.get("status", 200) != 200:
            raise HTTPException(status_code=ctrl_result.get("status", 503), detail=str(ctrl_result.get("body", {})))
        return ctrl_result.get("body", {})
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"PC client not connected: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
