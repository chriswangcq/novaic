"""
Agent Repository

Handles all Agent-related database operations.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import Database


class AgentRepository:
    """Repository for Agent configuration data."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents."""
        rows = await self.db.fetchall(
            "SELECT * FROM agents ORDER BY created_at"
        )
        # Parse JSON fields
        for row in rows:
            row["vm_config"] = json.loads(row.get("vm_config", "{}"))
            row["ports"] = json.loads(row.get("ports", "{}"))
        return rows
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get an agent by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM agents WHERE id = ?",
            (agent_id,)
        )
        if row:
            row["vm_config"] = json.loads(row.get("vm_config", "{}"))
            row["ports"] = json.loads(row.get("ports", "{}"))
        return row
    
    async def create_agent(
        self,
        id: str,
        name: str,
        vm_config: Dict[str, Any],
        ports: Dict[str, Any],
        status: str = "pending",
    ) -> Dict[str, Any]:
        """Create a new agent."""
        created_at = datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT INTO agents (id, name, created_at, vm_config, ports, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id, name, created_at, json.dumps(vm_config), json.dumps(ports), status)
        )
        await self.db.commit()
        
        return await self.get_agent(id)
    
    async def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        vm_config: Optional[Dict[str, Any]] = None,
        ports: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
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
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if not updates:
            return await self.get_agent(agent_id)
        
        params.append(agent_id)
        await self.db.execute(
            f"UPDATE agents SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        await self.db.commit()
        
        return await self.get_agent(agent_id)
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        cursor = await self.db.execute(
            "DELETE FROM agents WHERE id = ?",
            (agent_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    async def get_current_agent_id(self) -> Optional[str]:
        """Get the current agent ID from config."""
        value = await self.db.get_config("current_agent_id")
        if value and value != "null":
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_current_agent_id(self, agent_id: Optional[str]):
        """Set the current agent ID in config."""
        await self.db.set_config(
            "current_agent_id",
            json.dumps(agent_id) if agent_id else "null"
        )
    
    async def get_current_agent(self) -> Optional[Dict[str, Any]]:
        """Get the current agent."""
        agent_id = await self.get_current_agent_id()
        if agent_id:
            return await self.get_agent(agent_id)
        return None
    
    async def get_used_agent_indices(self) -> List[int]:
        """Get list of used agent indices for port allocation."""
        rows = await self.db.fetchall(
            "SELECT vm_config FROM agents"
        )
        indices = []
        for row in rows:
            vm_config = json.loads(row.get("vm_config", "{}"))
            if "agent_index" in vm_config:
                indices.append(vm_config["agent_index"])
        return indices
    
    async def find_next_agent_index(self) -> int:
        """Find the next available agent index."""
        used_indices = set(await self.get_used_agent_indices())
        index = 0
        while index in used_indices:
            index += 1
        return index
