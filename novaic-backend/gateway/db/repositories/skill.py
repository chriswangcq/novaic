"""
Skill Repository

Data access layer for skills and agent_skills tables.
Manages reusable capability bundles (prompt + tools + workflow).
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any


class SkillRepository:
    """Repository for skills and agent_skills tables."""
    
    def __init__(self, db):
        self.db = db
    
    # ---------- Skills CRUD ----------
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all skills."""
        rows = self.db.fetchall(
            "SELECT * FROM skills ORDER BY created_at DESC"
        )
        return [self._row_to_dict(row) for row in rows]
    
    def get_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get a skill by ID."""
        row = self.db.fetchone(
            "SELECT * FROM skills WHERE id = ?",
            (skill_id,)
        )
        return self._row_to_dict(row) if row else None
    
    def create(
        self,
        name: str,
        description: str = "",
        prompt: str = "",
        tools: Optional[List[str]] = None,
        workflow: str = "",
        icon: str = "zap",
    ) -> Dict[str, Any]:
        """Create a new skill."""
        skill_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        tools_json = json.dumps(tools or [], ensure_ascii=False)
        
        self.db.execute(
            """INSERT INTO skills (id, name, description, prompt, tools, workflow, icon, enabled, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (skill_id, name, description, prompt, tools_json, workflow, icon, now, now)
        )
        
        return self.get_by_id(skill_id) or {"id": skill_id, "name": name}
    
    def update(
        self,
        skill_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        workflow: Optional[str] = None,
        icon: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update a skill."""
        now = datetime.utcnow().isoformat()
        updates = ["updated_at = ?"]
        params: list = [now]
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if prompt is not None:
            updates.append("prompt = ?")
            params.append(prompt)
        if tools is not None:
            updates.append("tools = ?")
            params.append(json.dumps(tools, ensure_ascii=False))
        if workflow is not None:
            updates.append("workflow = ?")
            params.append(workflow)
        if icon is not None:
            updates.append("icon = ?")
            params.append(icon)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        
        set_clause = ", ".join(updates)
        params.append(skill_id)
        
        self.db.execute(
            f"UPDATE skills SET {set_clause} WHERE id = ?",
            tuple(params)
        )
        
        return self.get_by_id(skill_id) or {"id": skill_id, "success": True}
    
    def delete(self, skill_id: str) -> Dict[str, Any]:
        """Delete a skill (cascades to agent_skills)."""
        self.db.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        return {"success": True, "id": skill_id}
    
    # ---------- Agent-Skill Assignments ----------
    
    def get_agent_skills(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all skills assigned to an agent."""
        rows = self.db.fetchall(
            """SELECT s.* FROM skills s
               INNER JOIN agent_skills a ON s.id = a.skill_id
               WHERE a.agent_id = ?
               ORDER BY a.priority, s.name""",
            (agent_id,)
        )
        return [self._row_to_dict(row) for row in rows]
    
    def set_agent_skills(self, agent_id: str, skill_ids: List[str]) -> Dict[str, Any]:
        """Set the skills for an agent (replace all)."""
        # Delete existing assignments
        self.db.execute(
            "DELETE FROM agent_skills WHERE agent_id = ?",
            (agent_id,)
        )
        
        # Insert new assignments
        now = datetime.utcnow().isoformat()
        for i, skill_id in enumerate(skill_ids):
            try:
                self.db.execute(
                    """INSERT INTO agent_skills (agent_id, skill_id, priority, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (agent_id, skill_id, i, now)
                )
            except Exception:
                pass  # Skip invalid skill_ids (FK constraint)
        
        return {"success": True, "count": len(skill_ids)}
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"] or "",
            "prompt": row["prompt"] or "",
            "tools": json.loads(row["tools"] or "[]"),
            "workflow": row["workflow"] or "",
            "icon": row["icon"] or "zap",
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
