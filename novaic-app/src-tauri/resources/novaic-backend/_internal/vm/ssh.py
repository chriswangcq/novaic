"""
SSH Key Manager - Generate and manage SSH keys for VM access
"""

import os
import uuid
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from .repository import SshKeyRepository

logger = logging.getLogger(__name__)

# Singleton instance
_ssh_key_manager: Optional["SshKeyManager"] = None


def get_ssh_key_manager() -> "SshKeyManager":
    """Get the global SSH key manager instance."""
    global _ssh_key_manager
    if _ssh_key_manager is None:
        _ssh_key_manager = SshKeyManager()
    return _ssh_key_manager


class SshKeyManager:
    """
    Manages SSH keys for VM access.
    
    Keys are stored in the database and can be used for:
    - Cloud-init user setup
    - SSH access to VMs
    - Graceful VM shutdown
    """
    
    def __init__(self):
        self.repo = SshKeyRepository()
        self._temp_key_dir: Optional[Path] = None
    
    async def get_or_create_default_key(self) -> Dict[str, Any]:
        """
        Get the default SSH key, creating one if it doesn't exist.
        
        Returns:
            Dict with id, name, public_key, private_key
        """
        # Try to get existing default key
        key = await self.repo.get_default_key()
        if key:
            logger.debug(f"[SSH] Using existing default key: {key['id'][:8]}")
            return key
        
        # Generate new key
        logger.info("[SSH] No default key found, generating new SSH key pair")
        key_id = str(uuid.uuid4())
        public_key, private_key = self._generate_key_pair()
        
        await self.repo.create_key(
            key_id=key_id,
            name="default",
            public_key=public_key,
            private_key=private_key,
            is_default=True,
        )
        
        logger.info(f"[SSH] Generated new default SSH key: {key_id[:8]}")
        
        return {
            "id": key_id,
            "name": "default",
            "public_key": public_key,
            "private_key": private_key,
            "is_default": True,
        }
    
    async def get_public_key(self) -> str:
        """Get the default public key for cloud-init."""
        key = await self.get_or_create_default_key()
        return key["public_key"]
    
    async def get_private_key_path(self) -> Path:
        """
        Get path to the private key file (for SSH commands).
        
        Creates a temporary file if needed.
        """
        key = await self.get_or_create_default_key()
        
        # Create temp directory if needed
        if self._temp_key_dir is None:
            data_dir = os.environ.get("NOVAIC_DATA_DIR", "/tmp/novaic")
            self._temp_key_dir = Path(data_dir) / ".ssh"
            self._temp_key_dir.mkdir(parents=True, exist_ok=True)
        
        # Write private key to file with correct permissions
        key_path = self._temp_key_dir / f"id_{key['id'][:8]}"
        if not key_path.exists():
            key_path.write_text(key["private_key"])
            os.chmod(key_path, 0o600)
        
        return key_path
    
    async def list_keys(self) -> List[Dict[str, Any]]:
        """List all SSH keys (without private keys for security)."""
        keys = await self.repo.list_keys()
        # Remove private keys from response
        return [
            {
                "id": k["id"],
                "name": k["name"],
                "public_key": k["public_key"],
                "created_at": k["created_at"],
                "is_default": k["is_default"],
            }
            for k in keys
        ]
    
    async def create_key(self, name: str = "custom") -> Dict[str, Any]:
        """Create a new SSH key pair."""
        key_id = str(uuid.uuid4())
        public_key, private_key = self._generate_key_pair()
        
        await self.repo.create_key(
            key_id=key_id,
            name=name,
            public_key=public_key,
            private_key=private_key,
            is_default=False,
        )
        
        logger.info(f"[SSH] Created new SSH key: {key_id[:8]} ({name})")
        
        return {
            "id": key_id,
            "name": name,
            "public_key": public_key,
        }
    
    async def delete_key(self, key_id: str) -> bool:
        """Delete an SSH key."""
        key = await self.repo.get_key(key_id)
        if not key:
            return False
        
        if key["is_default"]:
            logger.warning("[SSH] Cannot delete default key")
            return False
        
        await self.repo.delete_key(key_id)
        
        # Clean up temp file if exists
        if self._temp_key_dir:
            key_path = self._temp_key_dir / f"id_{key_id[:8]}"
            if key_path.exists():
                key_path.unlink()
        
        logger.info(f"[SSH] Deleted SSH key: {key_id[:8]}")
        return True
    
    def _generate_key_pair(self) -> tuple[str, str]:
        """
        Generate an SSH key pair using ssh-keygen.
        
        Returns:
            Tuple of (public_key, private_key)
        """
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            key_path = Path(tmpdir) / "id_ed25519"
            
            # Generate ED25519 key (more secure and shorter than RSA)
            result = subprocess.run(
                [
                    "ssh-keygen",
                    "-t", "ed25519",
                    "-f", str(key_path),
                    "-N", "",  # No passphrase
                    "-C", "novaic-vm",
                ],
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                logger.error(f"[SSH] ssh-keygen failed: {result.stderr}")
                raise RuntimeError(f"Failed to generate SSH key: {result.stderr}")
            
            # Read generated keys
            private_key = key_path.read_text()
            public_key = Path(f"{key_path}.pub").read_text().strip()
            
            return public_key, private_key
