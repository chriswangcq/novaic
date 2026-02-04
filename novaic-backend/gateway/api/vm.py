"""
VM API Endpoints

REST API for VM management (setup, start, stop, status).
Replaces Tauri's VM commands.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gateway.vm import get_vm_manager, VmSetup, get_ssh_key_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vm", tags=["vm"])


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
    agent_index: int
    memory: str = "4096"
    cpus: int = 4


class VmStopRequest(BaseModel):
    """Request to stop VM."""
    agent_id: str
    graceful: bool = True
    quick: bool = False  # Use shorter timeouts for app exit


class SshKeyCreateRequest(BaseModel):
    """Request to create SSH key."""
    name: str = "custom"


class VmStatusResponse(BaseModel):
    """VM status response."""
    agent_id: str
    running: bool
    agent_healthy: bool
    mcp_healthy: bool
    websockify_running: bool
    ports: Dict[str, int]
    vnc_url: str
    mcp_url: str
    pid: Optional[int] = None
    started_at: Optional[str] = None
    error_message: Optional[str] = None


# ==================== Environment Check ====================

@router.get("/environment")
def check_environment():
    """
    Check if VM dependencies are installed.
    
    Returns:
        Environment check result with dependency status.
    """
    setup = VmSetup()
    return setup.check_environment()


# ==================== VM Setup ====================

@router.post("/setup")
def setup_vm(request: VmSetupRequest):
    """
    Setup VM for an agent (create disk, cloud-init).
    
    This prepares the VM but doesn't start it.
    """
    try:
        setup = VmSetup()
        result = setup.setup_vm(
            agent_id=request.agent_id,
            source_image=request.source_image,
            disk_size=request.disk_size,
            use_cn_mirrors=request.use_cn_mirrors,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"[VM API] Setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VM Lifecycle ====================

@router.post("/start")
def start_vm(request: VmStartRequest):
    """
    Start VM for an agent.
    
    Starts QEMU and waits for services to be ready.
    """
    try:
        manager = get_vm_manager()
        result = manager.start(
            agent_id=request.agent_id,
            agent_index=request.agent_index,
            memory=request.memory,
            cpus=request.cpus,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"[VM API] Start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
def stop_vm(request: VmStopRequest):
    """
    Stop VM for an agent.
    
    Attempts graceful shutdown via SSH, then force kills if needed.
    Use quick=True for faster shutdown (shorter timeouts).
    """
    try:
        manager = get_vm_manager()
        result = manager.stop(
            agent_id=request.agent_id,
            graceful=request.graceful,
            quick=request.quick,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"[VM API] Stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-all")
def stop_all_vms(quick: bool = False, graceful: bool = True):
    """Stop all running VMs in parallel.
    
    Args:
        quick: Use shorter timeouts for faster shutdown (for app exit)
        graceful: Try SSH poweroff before force kill
    """
    try:
        manager = get_vm_manager()
        result = manager.stop_all(graceful=graceful, quick=quick)
        return {"success": True, "results": result}
    except Exception as e:
        logger.error(f"[VM API] Stop all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VM Status ====================

@router.get("/status/{agent_id}")
def get_vm_status(agent_id: str):
    """Get VM status for a specific agent."""
    manager = get_vm_manager()
    status = manager.get_status(agent_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="VM not found")
    
    return VmStatusResponse(
        agent_id=status.agent_id,
        running=status.running,
        agent_healthy=status.agent_healthy,
        mcp_healthy=status.mcp_healthy,
        websockify_running=status.websockify_running,
        ports=status.ports,
        vnc_url=status.vnc_url,
        mcp_url=status.mcp_url,
        pid=status.pid,
        started_at=status.started_at,
        error_message=status.error_message,
    )


@router.get("/status")
def get_all_vm_status():
    """Get status for all VMs."""
    manager = get_vm_manager()
    all_status = manager.get_all_status()
    
    return {
        agent_id: VmStatusResponse(
            agent_id=status.agent_id,
            running=status.running,
            agent_healthy=status.agent_healthy,
            mcp_healthy=status.mcp_healthy,
            websockify_running=status.websockify_running,
            ports=status.ports,
            vnc_url=status.vnc_url,
            mcp_url=status.mcp_url,
            pid=status.pid,
            started_at=status.started_at,
            error_message=status.error_message,
        )
        for agent_id, status in all_status.items()
    }


@router.get("/running")
def get_running_agents():
    """Get list of running agent IDs."""
    manager = get_vm_manager()
    agents = manager.get_running_agents()
    return {"agents": agents}


@router.get("/is-running/{agent_id}")
def is_vm_running(agent_id: str):
    """Check if a specific VM is running."""
    manager = get_vm_manager()
    running = manager.is_running(agent_id)
    return {"running": running}


# ==================== SSH Key Management ====================

@router.get("/ssh/keys")
def list_ssh_keys():
    """List all SSH keys."""
    manager = get_ssh_key_manager()
    keys = manager.list_keys()
    return {"keys": keys}


@router.get("/ssh/pubkey")
def get_ssh_pubkey():
    """Get the default public key."""
    manager = get_ssh_key_manager()
    pubkey = manager.get_public_key()
    return {"public_key": pubkey}


@router.get("/ssh/private-key")
def get_ssh_private_key():
    """
    Get the default private key.
    
    Used by Tauri for SSH/SCP commands to VM.
    The private key is stored in Gateway's database.
    """
    manager = get_ssh_key_manager()
    key = manager.get_or_create_default_key()
    return {"private_key": key["private_key"]}


@router.post("/ssh/keys")
def create_ssh_key(request: SshKeyCreateRequest):
    """Create a new SSH key pair."""
    manager = get_ssh_key_manager()
    key = manager.create_key(name=request.name)
    return {"success": True, **key}


@router.delete("/ssh/keys/{key_id}")
def delete_ssh_key(key_id: str):
    """Delete an SSH key."""
    manager = get_ssh_key_manager()
    success = manager.delete_key(key_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete key (not found or is default)")
    return {"success": True}
