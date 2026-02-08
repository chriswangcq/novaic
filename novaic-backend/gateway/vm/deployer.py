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
import paramiko
from gateway.vm.ssh import get_ssh_key_manager

logger = logging.getLogger(__name__)


class VmuseDeployer:
    """
    Handles automatic deployment of VMUSE code to VM.
    """
    
    def __init__(self):
        self.vmuse_src = self._locate_vmuse_source()
    
    def _locate_vmuse_source(self) -> Path:
        """Locate VMUSE source code directory."""
        # Try multiple possible locations
        candidates = [
            Path(__file__).parent.parent.parent.parent / "novaic-app/src-tauri/resources/novaic-mcp-vmuse",
            Path.home() / "novaic/novaic-app/src-tauri/resources/novaic-mcp-vmuse",
            Path("/opt/novaic/novaic-mcp-vmuse"),  # Fallback
        ]
        
        for candidate in candidates:
            if candidate.exists() and (candidate / "pyproject.toml").exists():
                logger.info(f"[VmuseDeployer] Found VMUSE source at: {candidate}")
                return candidate
        
        raise RuntimeError(
            f"VMUSE source not found. Searched: {[str(c) for c in candidates]}"
        )
    
    def check_cloud_init_complete(
        self, 
        vm_ip: str = "127.0.0.1",
        ssh_port: int = 20000,
        ssh_user: str = "ubuntu",
        ssh_password: str = "ubuntu",
        timeout: int = 3600,  # 1 hour (increased from 10 minutes)
    ) -> bool:
        """
        Wait for cloud-init to complete.
        
        Args:
            vm_ip: VM IP address
            ssh_port: SSH port
            ssh_user: SSH username
            ssh_password: SSH password (not used, kept for compatibility)
            timeout: Maximum wait time in seconds (default: 1 hour)
        
        Returns:
            True if cloud-init completed successfully
        """
        logger.info(f"[VmuseDeployer] Waiting for cloud-init to complete (timeout: {timeout}s / {timeout//60} minutes)...")
        
        # Get SSH key
        ssh_manager = get_ssh_key_manager()
        key_path = ssh_manager.get_private_key_path()
        
        start_time = time.time()
        check_interval = 10  # Start with 10 seconds
        
        while time.time() - start_time < timeout:
            try:
                # Try SSH connection
                result = subprocess.run(
                    [
                        "ssh",
                        "-i", str(key_path),
                        "-p", str(ssh_port),
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "UserKnownHostsFile=/dev/null",
                        "-o", "ConnectTimeout=5",
                        f"{ssh_user}@{vm_ip}",
                        "test -f /opt/novaic/.cloud_init_complete && echo 'READY' || echo 'WAITING'"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                
                if result.returncode == 0 and "READY" in result.stdout:
                    elapsed = int(time.time() - start_time)
                    logger.info(f"[VmuseDeployer] ✅ Cloud-init completed in {elapsed}s ({elapsed//60}m{elapsed%60}s)!")
                    return True
                
                # Still waiting
                elapsed = int(time.time() - start_time)
                if elapsed % 60 == 0:  # Log every minute
                    logger.info(f"[VmuseDeployer] Cloud-init still running... ({elapsed//60}m)")
                
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                logger.debug(f"[VmuseDeployer] SSH check failed: {e}")
            
            # Dynamic wait interval: 10s for first 5 minutes, then 30s
            if time.time() - start_time > 300:  # After 5 minutes
                check_interval = 30
            
            time.sleep(check_interval)
        
        logger.warning(f"[VmuseDeployer] Cloud-init did not complete within {timeout}s ({timeout//60} minutes)")
        return False
    
    def deploy(
        self,
        agent_id: str,
        vm_ip: str = "127.0.0.1",
        ssh_port: int = 20000,
        ssh_user: str = "ubuntu",
        ssh_password: str = "ubuntu",
        wait_for_cloud_init: bool = True,
        cloud_init_timeout: int = 3600,  # 1 hour (increased from 10 minutes)
        aggressive: bool = True,  # New: aggressive deployment strategy
    ) -> Dict[str, Any]:
        """
        Deploy VMUSE code to VM.
        
        Deployment strategies:
        - Conservative (aggressive=False): Wait for cloud-init, then deploy once
        - Aggressive (aggressive=True): Start deploying immediately, retry until success
        
        Args:
            agent_id: Agent ID (for logging)
            vm_ip: VM IP address
            ssh_port: SSH port
            ssh_user: SSH username
            ssh_password: SSH password
            wait_for_cloud_init: Whether to wait for cloud-init completion (conservative mode)
            cloud_init_timeout: Cloud-init timeout in seconds
            aggressive: Use aggressive deployment (retry until dependencies ready)
        
        Returns:
            Deployment result dictionary
        """
        logger.info(f"[VmuseDeployer] Starting deployment for agent {agent_id} (strategy: {'aggressive' if aggressive else 'conservative'})")
        
        result = {
            "success": False,
            "agent_id": agent_id,
            "steps": {},
            "error": None,
        }
        
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Strategy 1: Aggressive - Start deploying immediately, retry until success
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if aggressive:
                logger.info("[VmuseDeployer] Using aggressive strategy: deploy immediately, auto-retry")
                result["steps"]["strategy"] = "aggressive"
                return self._deploy_with_retry(
                    agent_id, vm_ip, ssh_port, ssh_user, ssh_password, cloud_init_timeout
                )
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Strategy 2: Conservative - Wait for cloud-init, then deploy once
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            result["steps"]["strategy"] = "conservative"
            
            # Step 1: Wait for cloud-init (if enabled)
            if wait_for_cloud_init:
                logger.info("[VmuseDeployer] Step 1/5: Waiting for cloud-init...")
                if not self.check_cloud_init_complete(
                    vm_ip, ssh_port, ssh_user, ssh_password, cloud_init_timeout
                ):
                    raise RuntimeError("Cloud-init did not complete in time")
                result["steps"]["cloud_init"] = "completed"
            else:
                result["steps"]["cloud_init"] = "skipped"
            
            # Step 2: Package VMUSE code
            logger.info("[VmuseDeployer] Step 2/5: Packaging VMUSE code...")
            tar_path = Path("/tmp") / f"vmuse-{agent_id}-{int(time.time())}.tar.gz"
            
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(
                    self.vmuse_src,
                    arcname="novaic-mcp-vmuse",
                    filter=lambda tarinfo: None if tarinfo.name.endswith(('.pyc', '__pycache__')) else tarinfo
                )
            
            tar_size = tar_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"[VmuseDeployer] Package created: {tar_path} ({tar_size:.2f} MB)")
            result["steps"]["package"] = f"{tar_size:.2f} MB"
            
            # Step 3: Transfer to VM
            logger.info("[VmuseDeployer] Step 3/5: Transferring to VM...")
            # Get SSH key
            ssh_manager = get_ssh_key_manager()
            key_path = ssh_manager.get_private_key_path()
            
            scp_result = subprocess.run(
                [
                    "scp",
                    "-i", str(key_path),
                    "-P", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    str(tar_path),
                    f"{ssh_user}@{vm_ip}:/tmp/vmuse.tar.gz"
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if scp_result.returncode != 0:
                raise RuntimeError(f"SCP failed: {scp_result.stderr}")
            
            logger.info("[VmuseDeployer] Transfer completed")
            result["steps"]["transfer"] = "completed"
            
            # Step 4: Extract and install
            logger.info("[VmuseDeployer] Step 4/5: Installing in VM...")
            install_script = """
set -e
cd /opt/novaic

# Backup old version
if [ -d "novaic-mcp-vmuse" ]; then
    mv novaic-mcp-vmuse novaic-mcp-vmuse.bak.$(date +%Y%m%d%H%M%S) || true
fi

# Extract new version
mkdir -p novaic-mcp-vmuse
cd novaic-mcp-vmuse
tar -xzf /tmp/vmuse.tar.gz --strip-components=1

# Install Python dependencies
/opt/novaic/venv/bin/pip install -e . --quiet

# Cleanup
rm -f /tmp/vmuse.tar.gz

echo "VMUSE installation completed"
"""
            
            ssh_result = subprocess.run(
                [
                    "ssh",
                    "-i", str(key_path),
                    "-p", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    f"{ssh_user}@{vm_ip}",
                    install_script
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if ssh_result.returncode != 0:
                raise RuntimeError(f"Installation failed: {ssh_result.stderr}")
            
            logger.info("[VmuseDeployer] Installation completed")
            result["steps"]["install"] = "completed"
            
            # Step 5: Start service
            logger.info("[VmuseDeployer] Step 5/5: Starting VMUSE service...")
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
            
            if service_result.returncode != 0:
                logger.warning(f"[VmuseDeployer] Service restart warning: {service_result.stderr}")
            
            # Wait for service to start
            time.sleep(5)
            
            # Check service status
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
            
            if service_status == "active":
                logger.info("[VmuseDeployer] ✅ Service running")
            else:
                logger.warning(f"[VmuseDeployer] ⚠️  Service status: {service_status}")
            
            # Cleanup local temp file
            tar_path.unlink(missing_ok=True)
            
            # Success
            result["success"] = True
            logger.info(f"[VmuseDeployer] 🎉 Deployment completed for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"[VmuseDeployer] Deployment failed: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result
    
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
        
        logger.info(f"[VmuseDeployer] Starting aggressive deployment (timeout: {timeout//60}m)")
        
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
            # Get SSH key
            ssh_manager = get_ssh_key_manager()
            key_path = ssh_manager.get_private_key_path()
            
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
                timeout=120,
            )
            if scp_result.returncode != 0:
                raise RuntimeError(f"SCP failed: {scp_result.stderr}")
            result["steps"]["transfer"] = "ok"
            
            # Step 3: Install (this is where dependencies are needed)
            install_script = """
set -e
cd /opt/novaic
if [ -d "novaic-mcp-vmuse" ]; then
    mv novaic-mcp-vmuse novaic-mcp-vmuse.bak.$(date +%Y%m%d%H%M%S) || true
fi
mkdir -p novaic-mcp-vmuse
cd novaic-mcp-vmuse
tar -xzf /tmp/vmuse.tar.gz --strip-components=1
/opt/novaic/venv/bin/pip install -e . --quiet
rm -f /tmp/vmuse.tar.gz
echo "Installation completed"
"""
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
                timeout=120,
            )
            if ssh_result.returncode != 0:
                raise RuntimeError(f"Installation failed: {ssh_result.stderr}")
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
