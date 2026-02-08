"""
VM API Endpoints

REST API for VM management (setup, start, stop, status).
Replaces Tauri's VM commands.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gateway.vm import get_vm_manager, VmSetup, get_ssh_key_manager
from gateway.vm.deployer import get_vmuse_deployer

logger = logging.getLogger(__name__)

# Constants for setup status monitoring
SSH_TIMEOUT = 5
SSH_CONNECT_TIMEOUT = 3

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
    vnc_url: str  # vmcontrol WebSocket URL: ws://localhost:8080/api/vms/{agent_id}/vnc
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
def start_vm(request: VmStartRequest, auto_deploy_vmuse: bool = True):
    """
    Start VM for an agent.
    
    Starts QEMU and waits for services to be ready.
    
    Args:
        request: VM start request
        auto_deploy_vmuse: Automatically deploy VMUSE after VM starts (default: True)
    """
    try:
        manager = get_vm_manager()
        result = manager.start(
            agent_id=request.agent_id,
            memory=request.memory,
            cpus=request.cpus,
        )
        
        # Trigger automatic VMUSE deployment if enabled
        if auto_deploy_vmuse:
            from gateway.config import get_agent_config_manager
            agent_manager = get_agent_config_manager()
            agent = agent_manager.get_agent(request.agent_id)
            
            if agent and agent.vm.ports:
                # Schedule deployment task (non-blocking)
                import threading
                deploy_thread = threading.Thread(
                    target=_deploy_vmuse_background,
                    args=(request.agent_id, agent.vm.ports.ssh, agent.vm.ports.vmuse),
                    daemon=True
                )
                deploy_thread.start()
                logger.info(f"[VM API] Scheduled VMUSE deployment for agent {request.agent_id}")
                result["vmuse_deployment"] = "scheduled"
        
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
    from pathlib import Path
    from gateway.clients.vmcontrol import get_vmcontrol_client
    
    result = {
        "available": False,
        "vm_running": False,
        "vnc_socket_exists": False,
        "vnc_socket_path": "",
        "vmcontrol_healthy": False,
        "vm_registered": False,
        "vnc_url": f"ws://localhost:8080/api/vms/{agent_id}/vnc",
        "reason": ""
    }
    
    # 1. Check if VM is running
    manager = get_vm_manager()
    process_info = manager.repo.get_process(agent_id)
    
    if not process_info:
        result["reason"] = "VM not started"
        return result
    
    pid = process_info.get("pid")
    if not pid or not manager._is_pid_alive(pid):
        result["reason"] = "VM process not running"
        return result
    
    result["vm_running"] = True
    
    # 2. Check VNC Socket file
    socket_path = Path(f"/tmp/novaic/novaic-vnc-{agent_id}.sock")
    result["vnc_socket_path"] = str(socket_path)
    result["vnc_socket_exists"] = socket_path.exists()
    
    if not result["vnc_socket_exists"]:
        result["reason"] = "VNC socket not found (VM may still be booting)"
        return result
    
    # 3. Check VmControl service health
    try:
        client = get_vmcontrol_client()
        result["vmcontrol_healthy"] = await client.health_check()
    except Exception as e:
        logger.warning(f"[VNC Status] VmControl health check failed: {e}")
        result["vmcontrol_healthy"] = False
    
    if not result["vmcontrol_healthy"]:
        result["reason"] = "VmControl service not available"
        return result
    
    # 4. Check if VM is registered in VmControl
    try:
        vms = await client.list_vms()
        result["vm_registered"] = any(
            vm.get("id") == agent_id or vm.get("agent_id") == agent_id 
            for vm in vms
        )
    except Exception as e:
        logger.warning(f"[VNC Status] Failed to list VMs from VmControl: {e}")
        result["vm_registered"] = False
    
    if not result["vm_registered"]:
        result["reason"] = "VM not registered in VmControl (may need to restart VmControl)"
        return result
    
    # All checks passed
    result["available"] = True
    result["reason"] = "VNC ready"
    
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
):
    """
    Manually trigger VMUSE code deployment to VM.
    
    Useful for:
    - Updating VMUSE code after changes
    - Retrying failed automatic deployment
    - Deploying to VMs created before auto-deployment was added
    
    Args:
        agent_id: Agent ID
        aggressive: Use aggressive deployment (retry until success). Default: True
    
    Returns:
        Deployment result
    """
    try:
        # Get agent ports
        from gateway.config import get_agent_config_manager
        agent_manager = get_agent_config_manager()
        agent = agent_manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if not agent.vm.ports:
            raise HTTPException(status_code=400, detail="Agent ports not configured")
        
        # Deploy
        deployer = get_vmuse_deployer()
        result = deployer.deploy(
            agent_id=agent_id,
            ssh_port=agent.vm.ports.ssh,
            aggressive=aggressive,
        )
        
        # Health check
        if result["success"]:
            result["health_check"] = deployer.health_check(
                vmuse_port=agent.vm.ports.vmuse
            )
        
        return result
    
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
        
        if not agent.vm.ports:
            raise HTTPException(status_code=400, detail="Agent ports not configured")
        
        deployer = get_vmuse_deployer()
        healthy = deployer.health_check(vmuse_port=agent.vm.ports.vmuse)
        
        return {
            "agent_id": agent_id,
            "healthy": healthy,
            "vmuse_port": agent.vm.ports.vmuse,
            "url": f"http://127.0.0.1:{agent.vm.ports.vmuse}",
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
def get_setup_status(agent_id: str):
    """
    Get detailed setup status for a VM during initialization.
    
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
        
        # Phase 1: Check VM process status
        vm_manager = get_vm_manager()
        vm_process = vm_manager.repo.get_process(agent_id)
        
        if not vm_process:
            logger.debug(f"[Setup Status] Agent {agent_id}: VM process not found")
            response.update({
                "phase": "creating",
                "progress": 5,
                "message": "正在创建虚拟机...",
                "steps": {"vm_created": False}
            })
            return response
        
        vm_status = vm_process.get("status", "stopped")
        if vm_status != "running":
            logger.debug(f"[Setup Status] Agent {agent_id}: VM status = {vm_status}")
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
        
        # Phase 2: Check SSH accessibility
        ssh_port = agent.vm.ports.ssh if agent.vm.ports else 20000
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
            
            # Phase 4: Check VMUSE deployment
            vmuse_port = agent.vm.ports.vmuse if agent.vm.ports else 18000
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
