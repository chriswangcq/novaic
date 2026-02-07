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
        timeout: int = 600,  # 10 minutes
    ) -> bool:
        """
        Wait for cloud-init to complete.
        
        Args:
            vm_ip: VM IP address
            ssh_port: SSH port
            ssh_user: SSH username
            ssh_password: SSH password
            timeout: Maximum wait time in seconds
        
        Returns:
            True if cloud-init completed successfully
        """
        logger.info(f"[VmuseDeployer] Waiting for cloud-init to complete (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try SSH connection
                result = subprocess.run(
                    [
                        "sshpass", "-p", ssh_password,
                        "ssh",
                        "-p", str(ssh_port),
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "ConnectTimeout=5",
                        f"{ssh_user}@{vm_ip}",
                        "test -f /opt/novaic/.cloud_init_complete && echo 'READY' || echo 'WAITING'"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                
                if result.returncode == 0 and "READY" in result.stdout:
                    logger.info("[VmuseDeployer] ✅ Cloud-init completed!")
                    return True
                
                # Still waiting
                elapsed = int(time.time() - start_time)
                logger.debug(f"[VmuseDeployer] Cloud-init still running... ({elapsed}s)")
                
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                logger.debug(f"[VmuseDeployer] SSH check failed: {e}")
            
            # Wait before retry
            time.sleep(10)
        
        logger.warning(f"[VmuseDeployer] Cloud-init did not complete within {timeout}s")
        return False
    
    def deploy(
        self,
        agent_id: str,
        vm_ip: str = "127.0.0.1",
        ssh_port: int = 20000,
        ssh_user: str = "ubuntu",
        ssh_password: str = "ubuntu",
        wait_for_cloud_init: bool = True,
        cloud_init_timeout: int = 600,
    ) -> Dict[str, Any]:
        """
        Deploy VMUSE code to VM.
        
        Args:
            agent_id: Agent ID (for logging)
            vm_ip: VM IP address
            ssh_port: SSH port
            ssh_user: SSH username
            ssh_password: SSH password
            wait_for_cloud_init: Whether to wait for cloud-init completion
            cloud_init_timeout: Cloud-init timeout in seconds
        
        Returns:
            Deployment result dictionary
        """
        logger.info(f"[VmuseDeployer] Starting deployment for agent {agent_id}")
        
        result = {
            "success": False,
            "agent_id": agent_id,
            "steps": {},
            "error": None,
        }
        
        try:
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
            scp_result = subprocess.run(
                [
                    "sshpass", "-p", ssh_password,
                    "scp",
                    "-P", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
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
tar -xzf /tmp/vmuse.tar.gz

# Install Python dependencies
/opt/novaic/venv/bin/pip install -e . --quiet

# Cleanup
rm -f /tmp/vmuse.tar.gz

echo "VMUSE installation completed"
"""
            
            ssh_result = subprocess.run(
                [
                    "sshpass", "-p", ssh_password,
                    "ssh",
                    "-p", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
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
                    "sshpass", "-p", ssh_password,
                    "ssh",
                    "-p", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
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
                    "sshpass", "-p", ssh_password,
                    "ssh",
                    "-p", str(ssh_port),
                    "-o", "StrictHostKeyChecking=no",
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
