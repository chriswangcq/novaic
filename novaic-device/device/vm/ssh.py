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
    
    def get_or_create_default_key(self, user_id: str) -> Dict[str, Any]:
        """
        Get the default SSH key for user_id, creating one if it doesn't exist.

        Returns:
            Dict with id, name, public_key, private_key
        """
        key = self.repo.get_default_key(user_id)
        if key:
            logger.debug(f"[SSH] Using existing default key: {key['id'][:8]}")
            return key

        logger.info("[SSH] No default key found, generating new SSH key pair")
        key_id = str(uuid.uuid4())
        public_key, private_key = self._generate_key_pair()

        self.repo.create_key(
            key_id=key_id,
            name="default",
            public_key=public_key,
            private_key=private_key,
            user_id=user_id,
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

    def get_public_key(self, user_id: str) -> str:
        """Get the default public key for cloud-init."""
        key = self.get_or_create_default_key(user_id)
        return key["public_key"]

    def get_private_key_path(self, user_id: str) -> Path:
        """
        Get path to the private key file (for SSH commands).

        Path: {DATA_DIR}/.ssh/id_rsa_{user_id_hash}
        Each user gets their own key file so the singleton manager never mixes keys.
        """
        import hashlib
        from common.config import ServiceConfig

        key = self.get_or_create_default_key(user_id)

        ssh_dir = Path(ServiceConfig.DATA_DIR) / ".ssh"
        ssh_dir.mkdir(parents=True, exist_ok=True)

        # Use a short stable hash of user_id so filenames are safe for any user_id value
        uid_slug = hashlib.sha256(user_id.encode()).hexdigest()[:16] if user_id else "global"
        key_path = ssh_dir / f"id_rsa_{uid_slug}"

        # Re-write when the content has changed (e.g. after key rotation)
        current_content = key_path.read_text() if key_path.exists() else None
        if current_content != key["private_key"]:
            key_path.write_text(key["private_key"])
            os.chmod(key_path, 0o600)
            logger.info(f"[SSH] Wrote private key for user to {key_path}")

        return key_path

    def list_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """List SSH keys for user_id (without private keys for security)."""
        keys = self.repo.list_keys(user_id)
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

    def create_key(self, user_id: str, name: str = "custom") -> Dict[str, Any]:
        """Create a new SSH key pair for user_id."""
        key_id = str(uuid.uuid4())
        public_key, private_key = self._generate_key_pair()

        self.repo.create_key(
            key_id=key_id,
            name=name,
            public_key=public_key,
            private_key=private_key,
            user_id=user_id,
            is_default=False,
        )

        logger.info(f"[SSH] Created new SSH key: {key_id[:8]} ({name})")

        return {
            "id": key_id,
            "name": name,
            "public_key": public_key,
        }

    def delete_key(self, key_id: str, user_id: str) -> bool:
        """Delete an SSH key owned by user_id."""
        key = self.repo.get_key_for_user(key_id, user_id)
        if not key:
            return False

        if key["is_default"]:
            logger.warning("[SSH] Cannot delete default key")
            return False

        self.repo.delete_key(key_id, user_id)
        logger.info(f"[SSH] Deleted SSH key: {key_id[:8]}")
        return True
    
    # ---- Agent-aware helpers for internal callers ----

    def _user_id_for_agent(self, agent_id: str) -> str:
        """Look up the user_id that owns agent_id. Raises RuntimeError if not found."""
        from device.entity_store import get_entity_store
        row = get_entity_store().get("agents", "", agent_id)
        if not row:
            raise RuntimeError(f"Agent not found: {agent_id}")
        user_id = row.get("user_id", "")
        if not user_id:
            raise RuntimeError(f"Agent {agent_id} has no user_id — cannot resolve SSH key owner")
        return user_id

    def get_public_key_for_agent(self, agent_id: str) -> str:
        """Get the default public key for the agent's owner."""
        return self.get_public_key(self._user_id_for_agent(agent_id))

    def get_private_key_path_for_agent(self, agent_id: str) -> Path:
        """Get the private key path for the agent's owner."""
        return self.get_private_key_path(self._user_id_for_agent(agent_id))

    def get_private_key_for_agent(self, agent_id: str) -> str:
        """Get the private key content for the agent's owner (for deploy-wait forwarding)."""
        key = self.get_or_create_default_key(self._user_id_for_agent(agent_id))
        return key["private_key"]

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
