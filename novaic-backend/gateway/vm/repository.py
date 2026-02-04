"""
VM Repository - Database operations for VM management
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from gateway.db.access import get_db


def _parse_process_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a vm_processes row into a dict."""
    return {
        "agent_id": row["agent_id"],
        "pid": row["pid"],
        "status": row["status"],
        "started_at": row["started_at"],
        "ports": json.loads(row["ports"] or "{}"),
        "qemu_cmd": row["qemu_cmd"],
        "error_message": row["error_message"],
    }


def _parse_key_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a ssh_keys row into a dict."""
    return {
        "id": row["id"],
        "name": row["name"],
        "public_key": row["public_key"],
        "private_key": row["private_key"],
        "created_at": row["created_at"],
        "is_default": bool(row["is_default"]),
    }


class VmProcessRepository:
    """Repository for vm_processes table."""
    
    def __init__(self):
        self.db = get_db()
    
    def get_process(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get VM process info for an agent."""
        row = self.db.fetchone(
            "SELECT * FROM vm_processes WHERE agent_id = ?",
            (agent_id,)
        )
        return _parse_process_row(row) if row else None
    
    def get_all_processes(self) -> List[Dict[str, Any]]:
        """Get all VM process records."""
        rows = self.db.fetchall("SELECT * FROM vm_processes")
        return [_parse_process_row(row) for row in rows]
    
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get all running VM processes."""
        rows = self.db.fetchall(
            "SELECT * FROM vm_processes WHERE status = 'running'"
        )
        return [_parse_process_row(row) for row in rows]
    
    def upsert_process(
        self,
        agent_id: str,
        pid: Optional[int] = None,
        status: str = "stopped",
        ports: Optional[Dict] = None,
        qemu_cmd: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Insert or update VM process record."""
        started_at = datetime.now().isoformat() if status == "running" else None
        
        self.db.execute("""
            INSERT OR REPLACE INTO vm_processes 
            (agent_id, pid, status, started_at, ports, qemu_cmd, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            pid,
            status,
            started_at,
            json.dumps(ports) if ports else "{}",
            qemu_cmd,
            error_message,
        ))
        self.db.commit()
    
    def update_status(
        self,
        agent_id: str,
        status: str,
        pid: Optional[int] = None,
        error_message: Optional[str] = None,
    ):
        """Update VM process status."""
        if pid is not None:
            self.db.execute(
                "UPDATE vm_processes SET status = ?, pid = ?, error_message = ? WHERE agent_id = ?",
                (status, pid, error_message, agent_id)
            )
        else:
            self.db.execute(
                "UPDATE vm_processes SET status = ?, error_message = ? WHERE agent_id = ?",
                (status, error_message, agent_id)
            )
        self.db.commit()
    
    def delete_process(self, agent_id: str):
        """Delete VM process record."""
        self.db.execute(
            "DELETE FROM vm_processes WHERE agent_id = ?",
            (agent_id,)
        )
        self.db.commit()


class SshKeyRepository:
    """Repository for ssh_keys table."""
    
    def __init__(self):
        self.db = get_db()
    
    def get_default_key(self) -> Optional[Dict[str, Any]]:
        """Get the default SSH key."""
        row = self.db.fetchone(
            "SELECT * FROM ssh_keys WHERE is_default = 1 LIMIT 1"
        )
        return _parse_key_row(row) if row else None
    
    def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get SSH key by ID."""
        row = self.db.fetchone(
            "SELECT * FROM ssh_keys WHERE id = ?",
            (key_id,)
        )
        return _parse_key_row(row) if row else None
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """List all SSH keys."""
        rows = self.db.fetchall("SELECT * FROM ssh_keys ORDER BY created_at DESC")
        return [_parse_key_row(row) for row in rows]
    
    def create_key(
        self,
        key_id: str,
        name: str,
        public_key: str,
        private_key: str,
        is_default: bool = False,
    ):
        """Create a new SSH key."""
        # If setting as default, unset other defaults
        if is_default:
            self.db.execute("UPDATE ssh_keys SET is_default = 0")
        
        self.db.execute("""
            INSERT INTO ssh_keys (id, name, public_key, private_key, is_default)
            VALUES (?, ?, ?, ?, ?)
        """, (key_id, name, public_key, private_key, 1 if is_default else 0))
        self.db.commit()
    
    def delete_key(self, key_id: str):
        """Delete SSH key."""
        self.db.execute("DELETE FROM ssh_keys WHERE id = ?", (key_id,))
        self.db.commit()
    
    def set_default(self, key_id: str):
        """Set a key as the default."""
        self.db.execute("UPDATE ssh_keys SET is_default = 0")
        self.db.execute(
            "UPDATE ssh_keys SET is_default = 1 WHERE id = ?",
            (key_id,)
        )
        self.db.commit()
