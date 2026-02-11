"""
Agent Repository

Handles all Agent-related database operations.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from common.db.database import Database
from common.utils.time import utc_now_iso


class AgentRepository:
    """Repository for Agent configuration data."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents."""
        rows = self.db.fetchall(
            "SELECT * FROM agents ORDER BY created_at"
        )
        # Parse JSON fields and convert setup_complete to bool
        for row in rows:
            row["vm_config"] = json.loads(row.get("vm_config", "{}"))
            row["ports"] = json.loads(row.get("ports", "{}"))
            row["setup_complete"] = bool(row.get("setup_complete", 0))
        return rows
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID."""
        row = self.db.fetchone(
            "SELECT * FROM agents WHERE id = ?",
            (agent_id,)
        )
        if row:
            row["vm_config"] = json.loads(row.get("vm_config", "{}"))
            row["ports"] = json.loads(row.get("ports", "{}"))
            row["setup_complete"] = bool(row.get("setup_complete", 0))
        return row
    
    def create_agent(
        self,
        id: str,
        name: str,
        vm_config: Dict[str, Any],
        ports: Dict[str, Any],
        setup_complete: bool = False,
        agent_type: str = "linux",  # 'chat' | 'linux' | 'android' | 'hybrid'
    ) -> Dict[str, Any]:
        """
        Create a new agent.
        
        agent_type is stored in vm_config as '_agent_type' for persistence.
        """
        created_at = utc_now_iso()
        
        # Store agent_type in vm_config for persistence
        vm_config_with_type = {**vm_config, "_agent_type": agent_type}
        
        with self.db.transaction("agent", resource_id=id):
            self.db.execute(
                """INSERT INTO agents (id, name, created_at, vm_config, ports, setup_complete)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (id, name, created_at, json.dumps(vm_config_with_type), json.dumps(ports), 1 if setup_complete else 0)
            )
        
        return self.get_agent(id)
    
    def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        vm_config: Optional[Dict[str, Any]] = None,
        ports: Optional[Dict[str, Any]] = None,
        setup_complete: Optional[bool] = None,
        cloud_init_complete: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an agent."""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if vm_config is not None:
            updates.append("vm_config = ?")
            params.append(json.dumps(vm_config))
        if ports is not None:
            updates.append("ports = ?")
            params.append(json.dumps(ports))
        if setup_complete is not None:
            updates.append("setup_complete = ?")
            params.append(1 if setup_complete else 0)
        if cloud_init_complete is not None:
            updates.append("cloud_init_complete = ?")
            params.append(1 if cloud_init_complete else 0)
        
        if not updates:
            return self.get_agent(agent_id)
        
        params.append(agent_id)
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                f"UPDATE agents SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
        
        return self.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        with self.db.transaction("agent", resource_id=agent_id):
            cursor = self.db.execute(
                "DELETE FROM agents WHERE id = ?",
                (agent_id,)
            )
            return cursor.rowcount > 0
    
    def list_setup_complete_ids(self) -> List[str]:
        """列出所有已完成设置的 agent IDs"""
        rows = self.db.fetchall(
            "SELECT id FROM agents WHERE setup_complete = 1"
        )
        return [row["id"] for row in rows]
    
    def exists(self, agent_id: str) -> bool:
        """检查 agent 是否存在"""
        row = self.db.fetchone(
            "SELECT 1 FROM agents WHERE id = ?",
            (agent_id,)
        )
        return row is not None