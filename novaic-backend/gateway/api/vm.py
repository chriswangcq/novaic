"""
VM API Endpoints

REST API for VM management (setup, start, stop, status).
Replaces Tauri's VM commands.

Phase3: vmcontrol is the single VM backend for runtime state. No local VM manager
fallback for VM runtime (start/stop/status/setup-status). Local vm_manager is still
used for QEMU process spawning and recovery; runtime queries go to vmcontrol.

Also includes Android emulator management APIs.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from common.config import ServiceConfig
from common.http.clients import internal_async_client
from gateway.vm import VmSetup, get_ssh_key_manager
from gateway.vm.deployer import get_vmuse_deployer
from gateway.clients.vmcontrol import get_vmcontrol_client

logger = logging.getLogger(__name__)

# vmcontrol service URL (use ServiceConfig for consistency)
VMCONTROL_URL = os.environ.get("VMCONTROL_URL") or ServiceConfig.VMCONTROL_URL

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
    """
    # Try devices first (v38)
    if hasattr(agent, 'devices') and agent.devices:
        for device in agent.devices:
            if isinstance(device, dict) and device.get('type') == 'linux':
                path = device.get('image_path')
                if path:
                    from pathlib import Path
                    if Path(path).exists():
                        return path
                break
            elif hasattr(device, 'type') and getattr(device, 'type', None) == 'linux':
                path = getattr(device, 'image_path', None)
                if path:
                    from pathlib import Path
                    if Path(path).exists():
                        return path
                break
    # Fallback to agent.vm.image_path
    if hasattr(agent, 'vm') and agent.vm and agent.vm.image_path:
        from pathlib import Path
        if Path(agent.vm.image_path).exists():
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
    ports: Dict[str, int]
    vnc_url: str  # vmcontrol WebSocket URL: ws://localhost:19996/api/vms/{agent_id}/vnc
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
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    # Debug: log environment variable
    resource_dir = os.environ.get("NOVAIC_RESOURCE_DIR", "")
    logger.info(f"[VM API] check_environment: NOVAIC_RESOURCE_DIR='{resource_dir}'")
    
    setup = VmSetup()
    result = setup.check_environment()
    
    # Add resource_dir to result for debugging
    result["resource_dir"] = resource_dir
    
    return result


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
async def start_vm(request: VmStartRequest, auto_deploy_vmuse: bool = True):
    """
    Register an already-running VM into vmcontrol backend.
    
    Args:
        request: VM start request
        auto_deploy_vmuse: Automatically deploy VMUSE after VM starts (default: True)
    """
    try:
        from gateway.config import get_agent_config_manager

        # Phase3: Gateway only aggregates/forwards VM control to vmcontrol.
        # This endpoint now performs vmcontrol registration for an already-running VM.
        agent_manager = get_agent_config_manager()
        agent = agent_manager.get_agent(request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_id}")

        qmp_socket = f"/tmp/novaic/novaic-qmp-{request.agent_id}.sock"
        if not Path(qmp_socket).exists():
            raise HTTPException(
                status_code=409,
                detail=f"QMP socket not found: {qmp_socket}. VM is not running or not ready."
            )

        client = get_vmcontrol_client()
        try:
            result = await client.register_vm(
                vm_id=request.agent_id,
                name=agent.name,
                qmp_socket=qmp_socket,
            )
            vm_status = "registered"
        except httpx.HTTPStatusError as e:
            # vmcontrol returns 409 when already registered
            if e.response is not None and e.response.status_code == 409:
                result = {"message": "VM already registered in vmcontrol"}
                vm_status = "already_registered"
            else:
                raise

        # Optional: keep existing auto deployment behavior for VMUSE when VM is ready.
        if auto_deploy_vmuse:
            ports = _get_device_ports(agent)
            if ports['ssh'] and ports['vmuse']:
                import threading
                deploy_thread = threading.Thread(
                    target=_deploy_vmuse_background,
                    args=(request.agent_id, ports['ssh'], ports['vmuse']),
                    daemon=True
                )
                deploy_thread.start()
                logger.info(f"[VM API] Scheduled VMUSE deployment for agent {request.agent_id}")
                if isinstance(result, dict):
                    result["vmuse_deployment"] = "scheduled"

        return {"success": True, "status": vm_status, **(result if isinstance(result, dict) else {})}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VM API] Start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_vm(request: VmStopRequest):
    """
    Stop VM for an agent via vmcontrol backend.
    """
    try:
        # Phase3: vmcontrol is the single VM backend.
        # Gateway only forwards/aggregates VM control API.
        client = get_vmcontrol_client()
        result = await client.shutdown_vm(request.agent_id)
        if not isinstance(result, dict):
            result = {"result": result}
        return {"success": True, "status": "shutdown_sent", **result}
    except Exception as e:
        logger.error(f"[VM API] Stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-all")
async def stop_all_vms(quick: bool = False, graceful: bool = True):
    """Stop all running VMs in parallel.
    
    Args:
        quick: Use shorter timeouts for faster shutdown (for app exit)
        graceful: Try SSH poweroff before force kill
    """
    try:
        client = get_vmcontrol_client()
        result = await client.shutdown_all_vms()
        if not isinstance(result, dict):
            result = {"result": result}
        return {"success": True, "results": result}
    except Exception as e:
        logger.error(f"[VM API] Stop all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VM Status ====================

@router.get("/status/{agent_id}")
async def get_vm_status(agent_id: str):
    """Get VM status for a specific agent."""
    client = get_vmcontrol_client()
    try:
        vm_info = await client.get_vm_info(agent_id)
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="VM not found")
        raise HTTPException(status_code=500, detail=f"vmcontrol error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"vmcontrol unavailable: {str(e)}")

    if not vm_info:
        raise HTTPException(status_code=404, detail="VM not found")

    running = (vm_info.get("status") or "").lower() in {"running", "started", "active"}

    ports: Dict[str, int] = {}
    try:
        from gateway.config import get_agent_config_manager
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
async def get_all_vm_status():
    """Get status for all VMs."""
    client = get_vmcontrol_client()
    try:
        vms = await client.list_vms()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"vmcontrol unavailable: {str(e)}")

    result: Dict[str, VmStatusResponse] = {}
    for vm in vms:
        agent_id = vm.get("id")
        if not agent_id:
            continue
        running = (vm.get("status") or "").lower() in {"running", "started", "active"}
        result[agent_id] = VmStatusResponse(
            agent_id=agent_id,
            running=running,
            agent_healthy=True,
            mcp_healthy=False,
            ports={},
            vnc_url=f"ws://localhost:19996/api/vms/{agent_id}/vnc",
            mcp_url="",
            pid=vm.get("pid"),
            started_at=vm.get("started_at"),
            error_message=vm.get("error_message"),
        )
    return result


@router.get("/running")
async def get_running_agents():
    """Get list of running agent IDs."""
    client = get_vmcontrol_client()
    try:
        vms = await client.list_vms()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"vmcontrol unavailable: {str(e)}")
    agents = [
        vm.get("id")
        for vm in vms
        if vm.get("id") and (vm.get("status") or "").lower() in {"running", "started", "active"}
    ]
    return {"agents": agents}


@router.get("/is-running/{agent_id}")
async def is_vm_running(agent_id: str):
    """Check if a specific VM is running."""
    client = get_vmcontrol_client()
    try:
        vm_info = await client.get_vm_info(agent_id)
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 404:
            return {"running": False}
        raise HTTPException(status_code=500, detail=f"vmcontrol error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"vmcontrol unavailable: {str(e)}")
    running = (vm_info.get("status") or "").lower() in {"running", "started", "active"}
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


# ==================== VNC Status Check ====================

@router.get("/vnc/status/{agent_id}")
async def get_vnc_status(agent_id: str):
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
    # Phase3: vmcontrol is the single source of truth for VM runtime status.
    result = {
        "available": False,
        "vm_running": False,
        "vnc_socket_exists": None,
        "vnc_socket_path": None,
        "vmcontrol_healthy": False,
        "vm_registered": False,
        "vnc_url": f"ws://localhost:19996/api/vms/{agent_id}/vnc",
        "reason": ""
    }

    # 1. Check vmcontrol health
    try:
        client = get_vmcontrol_client()
        result["vmcontrol_healthy"] = await client.health_check()
    except Exception as e:
        logger.warning(f"[VNC Status] VmControl health check failed: {e}")
        result["vmcontrol_healthy"] = False
    
    if not result["vmcontrol_healthy"]:
        result["reason"] = "VmControl service not available"
        return result

    # 2. Check VM registration + runtime state via vmcontrol
    try:
        vm_info = await client.get_vm_info(agent_id)
        result["vm_registered"] = True
        vm_status = (vm_info.get("status") or "").lower()
        result["vm_running"] = vm_status in {"running", "started", "active"}
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
    try:
        from gateway.config import get_agent_config_manager
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
def check_vmuse_health(agent_id: str):
    """
    Check VMUSE service health for an agent.
    
    Args:
        agent_id: Agent ID
    
    Returns:
        Health status
    """
    try:
        from gateway.config import get_agent_config_manager
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
async def get_setup_status(agent_id: str):
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
    try:
        from gateway.config import get_agent_config_manager

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

        # Get SSH key path upfront (needed for multiple checks)
        key_path = None
        try:
            ssh_manager = get_ssh_key_manager()
            key_path = ssh_manager.get_private_key_path()
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

        # Check if cloud-init is already complete
        if agent.cloud_init_complete:
            logger.debug(f"[Setup Status] Agent {agent_id} already marked as complete")
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

        # Phase 1: Check VM runtime status via vmcontrol (Phase3: no local vm_processes)
        vm_info = None
        try:
            client = get_vmcontrol_client()
            vm_info = await client.get_vm_info(agent_id)
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.debug(f"[Setup Status] Agent {agent_id}: VM not registered in vmcontrol")
                response.update({
                    "phase": "creating",
                    "progress": 5,
                    "message": "正在创建虚拟机...",
                    "steps": {"vm_created": False}
                })
                return response
            logger.error(f"[Setup Status] vmcontrol error for {agent_id}: {e}")
            return {
                "agent_id": agent_id,
                "phase": "error",
                "progress": 0,
                "message": "获取 VM 状态失败",
                "error": str(e),
                "steps": {},
            }
        except Exception as e:
            logger.error(f"[Setup Status] vmcontrol unavailable for {agent_id}: {e}")
            return {
                "agent_id": agent_id,
                "phase": "error",
                "progress": 0,
                "message": "VM 控制服务不可用",
                "error": str(e),
                "steps": {},
            }

        vm_status = (vm_info.get("status") or "").lower()
        if vm_status not in {"running", "started", "active"}:
            logger.debug(f"[Setup Status] Agent {agent_id}: vmcontrol status = {vm_status}")
            response.update({
                "phase": "booting",
                "progress": 10,
                "message": "正在启动虚拟机...",
                "steps": {
                    "vm_created": True,
                    "vm_booted": False,
                }
            })
            return response

        response["steps"]["vm_created"] = True
        response["steps"]["vm_booted"] = True
        
        # Get device ports (v38 unified model)
        device_ports = _get_device_ports(agent)
        ssh_port = device_ports['ssh']
        vmuse_port = device_ports['vmuse']
        
        # Phase 2: Check SSH accessibility
        ssh_accessible = False
        
        try:
            result = _run_ssh_command(key_path, ssh_port, "echo ok")
            ssh_accessible = result.returncode == 0
        except Exception as e:
            logger.debug(f"[Setup Status] Agent {agent_id}: SSH check failed: {e}")
        
        if not ssh_accessible:
            logger.debug(f"[Setup Status] Agent {agent_id}: SSH not accessible yet")
            response.update({
                "phase": "booting",
                "progress": 15,
                "message": "虚拟机启动中，等待 SSH 可访问...",
                "steps": {
                    "vm_created": True,
                    "vm_booted": True,
                    "ssh_ready": False,
                }
            })
            return response
        
        response["steps"]["ssh_ready"] = True
        logger.debug(f"[Setup Status] Agent {agent_id}: SSH accessible")
        
        # Phase 3: Check cloud-init status
        cloud_init_status = None
        cloud_init_detail = ""
        
        try:
            result = _run_ssh_command(key_path, ssh_port, "cloud-init status --format=json")
            # cloud-init returns: 0 (done), 1 (error), 2 (running)
            # We should parse JSON regardless of exit code
            if result.stdout.strip():
                ci_data = json.loads(result.stdout)
                cloud_init_status = ci_data.get("status")
                cloud_init_detail = ci_data.get("extended_status", "")
                logger.debug(f"[Setup Status] Agent {agent_id}: cloud-init status = {cloud_init_status}")
        except Exception as e:
            logger.debug(f"[Setup Status] Agent {agent_id}: Failed to parse cloud-init JSON: {e}")
            # Fallback to simple status check
            try:
                result = _run_ssh_command(key_path, ssh_port, "cloud-init status")
                # Parse output like "status: running"
                for line in result.stdout.split('\n'):
                    if line.startswith('status:'):
                        cloud_init_status = line.split(':', 1)[1].strip()
                        logger.debug(f"[Setup Status] Agent {agent_id}: cloud-init status (fallback) = {cloud_init_status}")
                        break
            except Exception as e2:
                logger.debug(f"[Setup Status] Agent {agent_id}: Fallback cloud-init check failed: {e2}")
        
        # Handle cloud-init status = None (SSH works but cloud-init not responding)
        if cloud_init_status is None:
            logger.warning(f"[Setup Status] Agent {agent_id}: Cannot determine cloud-init status")
            response.update({
                "phase": "booting",
                "progress": 20,
                "message": "系统初始化中，正在启动 cloud-init...",
                "steps": {
                    "vm_created": True,
                    "vm_booted": True,
                    "ssh_ready": True,
                    "cloud_init": False,
                }
            })
            return response
        
        if cloud_init_status == "running":
            # Cloud-init is still running - try to get more details
            progress_message = "安装系统组件和依赖..."
            progress_pct = 40
            
            # Try to determine what's being installed
            try:
                log_result = _run_ssh_command(key_path, ssh_port, "tail -20 /var/log/cloud-init-output.log")
                log_tail = log_result.stdout.lower()
                
                if "download snap" in log_tail or "fetch and check" in log_tail:
                    progress_message = "下载并安装 Snap 包..."
                    progress_pct = 60
                elif "chromium" in log_tail or "playwright" in log_tail:
                    progress_message = "安装浏览器和自动化工具..."
                    progress_pct = 70
                elif "setting up" in log_tail or "processing triggers" in log_tail:
                    progress_message = "配置系统服务..."
                    progress_pct = 80
            except Exception as e:
                logger.debug(f"[Setup Status] Agent {agent_id}: Failed to read cloud-init log: {e}")
            
            logger.info(f"[Setup Status] Agent {agent_id}: cloud-init running - {progress_message}")
            response.update({
                "phase": "cloud-init",
                "progress": progress_pct,
                "message": f"Cloud-init 初始化中: {progress_message}",
                "steps": {
                    "vm_created": True,
                    "vm_booted": True,
                    "ssh_ready": True,
                    "cloud_init": False,
                    "cloud_init_detail": cloud_init_detail or "running",
                }
            })
            return response
        
        elif cloud_init_status == "done":
            response["steps"]["cloud_init"] = True
            logger.debug(f"[Setup Status] Agent {agent_id}: cloud-init done")
            
            # Phase 4: Check VMUSE deployment (vmuse_port already set above)
            deployer = get_vmuse_deployer()
            vmuse_healthy = deployer.health_check(vmuse_port=vmuse_port)
            
            if not vmuse_healthy:
                logger.debug(f"[Setup Status] Agent {agent_id}: VMUSE not healthy yet")
                response.update({
                    "phase": "vmuse-deploy",
                    "progress": 85,
                    "message": "正在部署 VMUSE 服务...",
                    "steps": {
                        "vm_created": True,
                        "vm_booted": True,
                        "ssh_ready": True,
                        "cloud_init": True,
                        "vmuse_deployed": False,
                    }
                })
                return response
            
            # Everything is ready! Mark as complete in database
            logger.info(f"[Setup Status] Agent {agent_id}: Cloud-init complete!")
            try:
                agent_manager.update_agent(agent_id, cloud_init_complete=True)
                # Also update device's cloud_init_complete flag (v38)
                if agent.devices:
                    from gateway.db.repositories.device import DeviceRepository
                    from gateway.db.access import get_db
                    device_repo = DeviceRepository(get_db())
                    for device in agent.devices:
                        if device.get('type') == 'linux':
                            device_repo.update(device['id'], cloud_init_complete=True)
                            break
            except Exception as e:
                logger.warning(f"[Setup Status] Failed to update cloud_init_complete flag: {e}")
            
            response.update({
                "phase": "complete",
                "progress": 100,
                "message": "环境已就绪",
                "steps": {
                    "vm_created": True,
                    "vm_booted": True,
                    "ssh_ready": True,
                    "cloud_init": True,
                    "vmuse_deployed": True,
                }
            })
            return response
        
        elif cloud_init_status == "error":
            logger.error(f"[Setup Status] Agent {agent_id}: cloud-init error - {cloud_init_detail}")
            response.update({
                "phase": "error",
                "progress": 0,
                "message": "Cloud-init 初始化失败",
                "error": cloud_init_detail or "Unknown error",
            })
            return response
        
        # Unknown cloud-init status
        logger.warning(f"[Setup Status] Agent {agent_id}: Unknown cloud-init status: {cloud_init_status}")
        response.update({
            "phase": "unknown",
            "progress": 20,
            "message": f"未知的初始化状态: {cloud_init_status}",
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
async def start_android(request: AndroidStartRequest):
    """
    Start Android emulator for an agent.
    
    1. Get agent configuration
    2. Check if agent has Android config
    3. Call vmcontrol API to start emulator
    4. Update agent's device_serial
    5. Return result
    """
    from gateway.config import get_agent_config_manager
    from gateway.config.agents_db import AndroidConfig
    
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
        
        # 3. Call vmcontrol API to start emulator
        async with internal_async_client(timeout=180.0) as client:
            vmcontrol_url = f"{VMCONTROL_URL}/api/android/emulator/start"
            payload = {
                "avd": android_config.avd_name,
                "headless": True,
                "wait_boot": True,
                "timeout": 120
            }
            
            logger.info(f"[Android API] Calling vmcontrol: {vmcontrol_url}")
            logger.debug(f"[Android API] Payload: {payload}")
            
            response = await client.post(vmcontrol_url, json=payload)
            
            if response.status_code != 200:
                error_msg = f"vmcontrol returned {response.status_code}: {response.text}"
                logger.error(f"[Android API] {error_msg}")
                return AndroidStartResponse(
                    success=False,
                    message=error_msg
                )
            
            result = response.json()
            logger.info(f"[Android API] vmcontrol response: {result}")
            
            if not result.get("success"):
                return AndroidStartResponse(
                    success=False,
                    message=result.get("message", "Failed to start emulator")
                )
            
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
                manager.update_agent(agent_id, android_config=updated_android_config)
                logger.info(f"[Android API] Updated device_serial to {device_serial}")
            
            # 5. Return result
            return AndroidStartResponse(
                success=True,
                device_serial=device_serial,
                message=result.get("message", "Emulator started successfully")
            )
    
    except httpx.TimeoutException:
        logger.error(f"[Android API] Timeout starting emulator for agent {agent_id}")
        return AndroidStartResponse(
            success=False,
            message="Timeout waiting for emulator to start"
        )
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        return AndroidStartResponse(
            success=False,
            message=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}"
        )
    except Exception as e:
        logger.error(f"[Android API] Error starting emulator: {e}", exc_info=True)
        return AndroidStartResponse(
            success=False,
            message=str(e)
        )


@router.post("/android/stop", response_model=AndroidStopResponse)
async def stop_android(request: AndroidStopRequest):
    """
    Stop Android emulator for an agent.
    
    1. Get agent configuration
    2. Get device_serial
    3. Call vmcontrol API to stop emulator
    4. Return result
    """
    from gateway.config import get_agent_config_manager
    
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
        
        # 3. Call vmcontrol API to stop emulator
        async with internal_async_client(timeout=30.0) as client:
            vmcontrol_url = f"{VMCONTROL_URL}/api/android/emulator/stop"
            payload = {"serial": device_serial}
            
            logger.info(f"[Android API] Calling vmcontrol: {vmcontrol_url}")
            logger.debug(f"[Android API] Payload: {payload}")
            
            response = await client.post(vmcontrol_url, json=payload)
            
            if response.status_code != 200:
                error_msg = f"vmcontrol returned {response.status_code}: {response.text}"
                logger.error(f"[Android API] {error_msg}")
                return AndroidStopResponse(
                    success=False,
                    message=error_msg
                )
            
            result = response.json()
            logger.info(f"[Android API] vmcontrol response: {result}")
            
            # 4. Return result
            return AndroidStopResponse(
                success=result.get("success", False),
                message=result.get("message", "Emulator stopped")
            )
    
    except httpx.TimeoutException:
        logger.error(f"[Android API] Timeout stopping emulator for agent {agent_id}")
        return AndroidStopResponse(
            success=False,
            message="Timeout waiting for emulator to stop"
        )
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        return AndroidStopResponse(
            success=False,
            message=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}"
        )
    except Exception as e:
        logger.error(f"[Android API] Error stopping emulator: {e}", exc_info=True)
        return AndroidStopResponse(
            success=False,
            message=str(e)
        )


@router.get("/android/status/{agent_id}", response_model=AndroidStatusResponse)
async def get_android_status(agent_id: str):
    """
    Get Android emulator status for an agent.
    
    Checks:
    1. Agent configuration for Android settings
    2. Device serial from config
    3. Actual device status from vmcontrol
    """
    from gateway.config import get_agent_config_manager
    
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
        
        # 3. If we have a device_serial, check actual status from vmcontrol
        running = False
        if device_serial:
            try:
                async with internal_async_client(timeout=10.0) as client:
                    # Get device list from vmcontrol
                    vmcontrol_url = f"{VMCONTROL_URL}/api/android/devices"
                    response = await client.get(vmcontrol_url)
                    
                    if response.status_code == 200:
                        result = response.json()
                        devices = result.get("devices", [])
                        
                        # Check if our device is in the list and online
                        for device in devices:
                            if device.get("serial") == device_serial:
                                status = device.get("status", "")
                                running = status in ("online", "device", "connected")
                                break
            except Exception as e:
                logger.warning(f"[Android API] Failed to check device status: {e}")
                # Continue without running status
        
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
async def list_android_devices():
    """列出所有 Android 设备"""
    logger.info("[Android API] Listing Android devices")
    try:
        async with internal_async_client(timeout=30.0) as client:
            response = await client.get(f"{VMCONTROL_URL}/api/android/devices")
            if response.status_code != 200:
                logger.error(f"[Android API] vmcontrol returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}")
    except httpx.TimeoutException:
        logger.error("[Android API] Timeout connecting to vmcontrol")
        raise HTTPException(status_code=504, detail="Timeout connecting to vmcontrol service")


@router.get("/android/avds")
async def list_avds():
    """列出所有 AVD"""
    logger.info("[Android API] Listing AVDs")
    try:
        async with internal_async_client(timeout=30.0) as client:
            response = await client.get(f"{VMCONTROL_URL}/api/android/avds")
            if response.status_code != 200:
                logger.error(f"[Android API] vmcontrol returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}")
    except httpx.TimeoutException:
        logger.error("[Android API] Timeout connecting to vmcontrol")
        raise HTTPException(status_code=504, detail="Timeout connecting to vmcontrol service")


@router.get("/android/system-image/check")
async def check_system_image():
    """检查 Android 系统镜像"""
    logger.info("[Android API] Checking system image")
    try:
        async with internal_async_client(timeout=30.0) as client:
            response = await client.get(f"{VMCONTROL_URL}/api/android/system-image/check")
            if response.status_code != 200:
                logger.error(f"[Android API] vmcontrol returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}")
    except httpx.TimeoutException:
        logger.error("[Android API] Timeout connecting to vmcontrol")
        raise HTTPException(status_code=504, detail="Timeout connecting to vmcontrol service")


@router.get("/android/device-definitions")
async def list_device_definitions():
    """列出设备定义"""
    logger.info("[Android API] Listing device definitions")
    try:
        async with internal_async_client(timeout=30.0) as client:
            response = await client.get(f"{VMCONTROL_URL}/api/android/device-definitions")
            if response.status_code != 200:
                logger.error(f"[Android API] vmcontrol returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}")
    except httpx.TimeoutException:
        logger.error("[Android API] Timeout connecting to vmcontrol")
        raise HTTPException(status_code=504, detail="Timeout connecting to vmcontrol service")


class CreateAvdRequest(BaseModel):
    """Request to create AVD."""
    avd_name: str
    device: Optional[str] = None
    memory: Optional[int] = None
    cores: Optional[int] = None


@router.post("/android/avd/create")
async def create_avd(request: CreateAvdRequest):
    """创建 AVD"""
    logger.info(f"[Android API] Creating AVD: {request.avd_name}")
    try:
        async with internal_async_client(timeout=120.0) as client:
            # vmcontrol expects 'name' not 'avd_name'
            payload = {
                "name": request.avd_name,
            }
            if request.device:
                payload["device"] = request.device
            if request.memory:
                payload["memory"] = str(request.memory)
            if request.cores:
                payload["cores"] = request.cores
            
            response = await client.post(
                f"{VMCONTROL_URL}/api/android/avd/create",
                json=payload
            )
            if response.status_code != 200:
                logger.error(f"[Android API] vmcontrol returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}")
    except httpx.TimeoutException:
        logger.error("[Android API] Timeout creating AVD")
        raise HTTPException(status_code=504, detail="Timeout creating AVD")


@router.delete("/android/avd/{avd_name}")
async def delete_avd(avd_name: str):
    """删除 AVD"""
    logger.info(f"[Android API] Deleting AVD: {avd_name}")
    try:
        async with internal_async_client(timeout=30.0) as client:
            response = await client.delete(f"{VMCONTROL_URL}/api/android/avd/{avd_name}")
            if response.status_code != 200:
                logger.error(f"[Android API] vmcontrol returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}")
    except httpx.TimeoutException:
        logger.error("[Android API] Timeout deleting AVD")
        raise HTTPException(status_code=504, detail="Timeout deleting AVD")


@router.get("/android/scrcpy/status")
async def check_scrcpy_status():
    """检查 scrcpy 可用性"""
    logger.info("[Android API] Checking scrcpy status")
    try:
        async with internal_async_client(timeout=10.0) as client:
            response = await client.get(f"{VMCONTROL_URL}/api/android/scrcpy/status")
            if response.status_code != 200:
                logger.error(f"[Android API] vmcontrol returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.ConnectError:
        logger.error(f"[Android API] Cannot connect to vmcontrol at {VMCONTROL_URL}")
        raise HTTPException(status_code=503, detail=f"Cannot connect to vmcontrol service at {VMCONTROL_URL}")
    except httpx.TimeoutException:
        logger.error("[Android API] Timeout checking scrcpy status")
        raise HTTPException(status_code=504, detail="Timeout checking scrcpy status")
