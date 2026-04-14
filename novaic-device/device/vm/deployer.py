"""
VMUSE Code Deployer

Automatically deploys VMUSE code to VM after cloud-init completion.
"""

import logging
import subprocess
import tarfile
import time
from pathlib import Path
from typing import Optional, Dict, Any
from device.vm.ssh import get_ssh_key_manager

logger = logging.getLogger(__name__)


class VmuseDeployer:
    """
    Handles automatic deployment of VMUSE code to VM.
    """
    
    def __init__(self):
        self.vmuse_src = self._locate_vmuse_source()
    
    def _locate_vmuse_source(self) -> Path:
        """Locate VMUSE source code directory."""
        from common.config import ServiceConfig
        
        candidates = []
        
        if ServiceConfig.RESOURCE_DIR:
            candidates.append(Path(ServiceConfig.RESOURCE_DIR) / "novaic-mcp-vmuse")
        
        # 2. 开发环境：顶级目录的源码
        candidates.extend([
            Path(__file__).parent.parent.parent.parent / "novaic-mcp-vmuse",
            Path.home() / "novaic/novaic-mcp-vmuse",
        ])
        
        # 3. Fallback
        candidates.append(Path("/opt/novaic/novaic-mcp-vmuse"))
        
        for candidate in candidates:
            if candidate.exists() and (candidate / "pyproject.toml").exists():
                logger.info(f"[VmuseDeployer] Found VMUSE source at: {candidate}")
                return candidate
        
        raise RuntimeError(
            f"VMUSE source not found. Searched: {[str(c) for c in candidates]}"
        )
    
    def deploy(
        self,
        agent_id: str,
        vm_ip: str = "127.0.0.1",
        ssh_port: int = 20000,
        ssh_user: str = "ubuntu",
        ssh_password: str = "ubuntu",
        timeout: int = 3600,
        aggressive: bool = True,  # Kept for API compatibility, always uses aggressive strategy
    ) -> Dict[str, Any]:
        """
        Deploy VMUSE code to VM using aggressive strategy.
        
        Aggressive strategy: Start deploying immediately, retry until success.
        Does not wait for cloud-init to complete.
        
        Args:
            agent_id: Agent ID (for logging)
            vm_ip: VM IP address
            ssh_port: SSH port
            ssh_user: SSH username
            ssh_password: SSH password
            timeout: Maximum deployment timeout in seconds
            aggressive: Ignored (kept for API compatibility)
        
        Returns:
            Deployment result dictionary
        """
        logger.info(f"[VmuseDeployer] Starting deployment for agent {agent_id}")
        return self._deploy_with_retry(
            agent_id, vm_ip, ssh_port, ssh_user, ssh_password, timeout
        )
    
    def _wait_for_ssh(self, vm_ip: str, ssh_port: int, ssh_user: str, max_wait: int = 120, key_path=None):
        """Poll until SSH is ready (every 5s). First boot ~60s, subsequent ~15s."""
        if key_path is None:
            raise ValueError(
                "_wait_for_ssh requires key_path; callers must resolve it via "
                "get_ssh_key_manager().get_private_key_path_for_agent(agent_id)"
            )
        poll_interval = 5
        last_log = 0
        
        for elapsed in range(0, max_wait, poll_interval):
            r = subprocess.run(
                ["ssh", "-i", str(key_path), "-p", str(ssh_port),
                 "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
                 "-o", "ConnectTimeout=3", f"{ssh_user}@{vm_ip}", "echo ok"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                if elapsed > 0:
                    logger.info(f"[VmuseDeployer] SSH ready in {elapsed}s")
                return
            if elapsed - last_log >= 15:
                logger.info(f"[VmuseDeployer] Waiting for SSH... ({elapsed}s)")
                last_log = elapsed
            time.sleep(poll_interval)
        logger.warning(f"[VmuseDeployer] SSH not ready after {max_wait}s, will retry in deploy loop")
    
    def _deploy_with_retry(
        self,
        agent_id: str,
        vm_ip: str,
        ssh_port: int,
        ssh_user: str,
        ssh_password: str,
        timeout: int,
    ) -> Dict[str, Any]:
        """
        Aggressive deployment strategy: Start immediately, retry until success.
        
        This doesn't wait for cloud-init to complete. Instead, it:
        1. Starts deploying as soon as SSH is available
        2. Retries if dependencies are not ready
        3. Succeeds automatically when dependencies become ready
        
        Args:
            agent_id: Agent ID
            vm_ip: VM IP
            ssh_port: SSH port
            ssh_user: SSH username
            ssh_password: SSH password
            timeout: Maximum total time to retry
        
        Returns:
            Deployment result
        """
        result = {
            "success": False,
            "agent_id": agent_id,
            "steps": {},
            "error": None,
            "attempts": 0,
        }
        
        start_time = time.time()
        retry_interval = 30  # Check every 30 seconds
        
        # Poll for SSH readiness instead of fixed wait (first boot ~60s, subsequent ~15s)
        logger.info(f"[VmuseDeployer] Starting aggressive deployment (timeout: {timeout//60}m), waiting for SSH...")
        key_path = get_ssh_key_manager().get_private_key_path_for_agent(agent_id)
        self._wait_for_ssh(vm_ip, ssh_port, ssh_user, max_wait=120, key_path=key_path)
        
        while time.time() - start_time < timeout:
            result["attempts"] += 1
            elapsed = int(time.time() - start_time)
            
            logger.info(f"[VmuseDeployer] Deployment attempt #{result['attempts']} ({elapsed//60}m{elapsed%60}s elapsed)")
            
            try:
                # Try to deploy (will fail if dependencies not ready)
                deploy_result = self._try_deploy_once(
                    agent_id, vm_ip, ssh_port, ssh_user, ssh_password
                )
                
                if deploy_result["success"]:
                    result.update(deploy_result)
                    logger.info(f"[VmuseDeployer] ✅ Deployment succeeded on attempt #{result['attempts']}")
                    return result
                
                # Deployment failed, check why
                error = deploy_result.get("error", "")
                result["last_error"] = error
                
                # Check if it's a dependency issue (can retry)
                if any(keyword in error.lower() for keyword in ["venv", "pip", "node", "playwright", "not found"]):
                    logger.info(f"[VmuseDeployer] Dependencies not ready yet, will retry in {retry_interval}s...")
                    result["steps"]["status"] = "waiting_for_dependencies"
                else:
                    # Other error, might not be retryable
                    logger.warning(f"[VmuseDeployer] Deployment failed with non-dependency error: {error}")
                    result["steps"]["status"] = "error_may_not_be_retryable"
                
            except Exception as e:
                logger.debug(f"[VmuseDeployer] Attempt #{result['attempts']} exception: {e}")
                result["last_error"] = str(e)
            
            # Wait before retry
            time.sleep(retry_interval)
        
        # Timeout reached
        result["error"] = f"Deployment timed out after {result['attempts']} attempts ({timeout//60} minutes)"
        logger.error(f"[VmuseDeployer] {result['error']}")
        return result
    
    def _try_deploy_once(
        self,
        agent_id: str,
        vm_ip: str,
        ssh_port: int,
        ssh_user: str,
        ssh_password: str,
    ) -> Dict[str, Any]:
        """
        Try to deploy VMUSE code once (no retry).
        
        Returns:
            Result dict with success=True if successful
        """
        result = {
            "success": False,
            "steps": {},
            "error": None,
        }
        
        try:
            # Step 1: Package code
            tar_path = Path("/tmp") / f"vmuse-{agent_id}-{int(time.time())}.tar.gz"
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(
                    self.vmuse_src,
                    arcname="novaic-mcp-vmuse",
                    filter=lambda tarinfo: None if tarinfo.name.endswith(('.pyc', '__pycache__')) else tarinfo
                )
            result["steps"]["package"] = "ok"
            
            # Step 2: Transfer
            # Get SSH key for the agent's owner
            key_path = get_ssh_key_manager().get_private_key_path_for_agent(agent_id)
            
            scp_result = subprocess.run(
                [
                    "scp",
                    "-i", str(key_path),
                    "-P", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-o", "ConnectTimeout=5",
                    str(tar_path),
                    f"{ssh_user}@{vm_ip}:/tmp/vmuse.tar.gz"
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if scp_result.returncode != 0:
                raise RuntimeError(f"SCP failed: {scp_result.stderr}")
            result["steps"]["transfer"] = "ok"
            
            # Step 3: Install (this is where dependencies are needed)
            # Use sudo for directory operations to handle permission issues from cloud-init
            install_script = """
set -e
cd /opt/novaic
if [ -d "novaic-mcp-vmuse" ]; then
    sudo mv novaic-mcp-vmuse novaic-mcp-vmuse.bak.$(date +%Y%m%d%H%M%S) || true
fi
sudo mkdir -p novaic-mcp-vmuse
sudo chown ubuntu:ubuntu novaic-mcp-vmuse
cd novaic-mcp-vmuse
tar -xzf /tmp/vmuse.tar.gz --strip-components=1
/opt/novaic/venv/bin/pip install -e . --quiet
rm -f /tmp/vmuse.tar.gz
echo "Installation completed"
"""
            # pip install -e . with playwright can take 5-10+ min (downloads browser binaries)
            ssh_result = subprocess.run(
                [
                    "ssh",
                    "-i", str(key_path),
                    "-p", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-o", "ConnectTimeout=5",
                    f"{ssh_user}@{vm_ip}",
                    install_script
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )
            if ssh_result.returncode != 0:
                out = (ssh_result.stdout or "").strip()
                err = (ssh_result.stderr or "").strip()
                err_msg = f"Installation failed (exit {ssh_result.returncode})"
                if out:
                    err_msg += f" stdout: {out[:500]}{'...' if len(out) > 500 else ''}"
                if err:
                    err_msg += f" stderr: {err[:500]}{'...' if len(err) > 500 else ''}"
                logger.warning(f"[VmuseDeployer] {err_msg}")
                raise RuntimeError(err_msg)
            result["steps"]["install"] = "ok"
            
            # Step 4: Start service
            service_result = subprocess.run(
                [
                    "ssh",
                    "-i", str(key_path),
                    "-p", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    f"{ssh_user}@{vm_ip}",
                    "sudo systemctl restart novaic-vmuse"
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            time.sleep(5)
            
            # Check status
            status_result = subprocess.run(
                [
                    "ssh",
                    "-i", str(key_path),
                    "-p", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    f"{ssh_user}@{vm_ip}",
                    "sudo systemctl is-active novaic-vmuse"
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            service_status = status_result.stdout.strip()
            result["steps"]["service"] = service_status
            
            # Cleanup
            tar_path.unlink(missing_ok=True)
            
            result["success"] = service_status == "active"
            if not result["success"]:
                result["error"] = f"Service status: {service_status}"
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def health_check(
        self,
        vmuse_port: int = 18080,
        vm_ip: str = "127.0.0.1",
        timeout: int = 5,
    ) -> bool:
        """
        Check if VMUSE service is healthy.
        
        Args:
            vmuse_port: VMUSE HTTP port
            vm_ip: VM IP address
            timeout: Request timeout
        
        Returns:
            True if service is healthy
        """
        try:
            # Use curl for health check to avoid requests dependency
            result = subprocess.run(
                ["curl", "-s", "-m", str(timeout), f"http://{vm_ip}:{vmuse_port}/health"],
                capture_output=True,
                text=True,
                timeout=timeout + 1,
            )
            return result.returncode == 0 and "healthy" in result.stdout.lower()
        except Exception as e:
            logger.debug(f"[VmuseDeployer] Health check failed: {e}")
            return False


# Singleton instance
_deployer: Optional[VmuseDeployer] = None

def get_vmuse_deployer() -> VmuseDeployer:
    """Get the singleton VMUSE deployer instance."""
    global _deployer
    if _deployer is None:
        _deployer = VmuseDeployer()
    return _deployer
