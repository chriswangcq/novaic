"""
Skills & Agent Tools Config API

Public API endpoints for managing skills, agent-skill assignments,
and per-agent tool configuration.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json

from gateway.db.access import get_db

router = APIRouter(prefix="/api", tags=["skills"])


# ==================== Skills CRUD ====================

@router.get("/skills")
def list_skills():
    """List all skills."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    skills = repo.list_all()
    return {"skills": skills, "count": len(skills)}


@router.post("/skills")
def create_skill(data: Dict[str, Any]):
    """Create a new skill."""
    from gateway.db.repositories.skill import SkillRepository
    
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    db = get_db()
    repo = SkillRepository(db)
    skill = repo.create(
        name=name,
        description=data.get("description", ""),
        prompt=data.get("prompt", ""),
        tools=data.get("tools", []),
        workflow=data.get("workflow", ""),
        icon=data.get("icon", "zap"),
    )
    return skill


@router.put("/skills/{skill_id}")
def update_skill(skill_id: str, data: Dict[str, Any]):
    """Update an existing skill."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    
    existing = repo.get_by_id(skill_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    skill = repo.update(
        skill_id=skill_id,
        name=data.get("name"),
        description=data.get("description"),
        prompt=data.get("prompt"),
        tools=data.get("tools"),
        workflow=data.get("workflow"),
        icon=data.get("icon"),
        enabled=data.get("enabled"),
    )
    return skill


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: str):
    """Delete a skill."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    return repo.delete(skill_id)


# ==================== Agent Skills Assignment ====================

@router.get("/agents/{agent_id}/skills")
def get_agent_skills(agent_id: str):
    """Get skills assigned to an agent."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    skills = repo.get_agent_skills(agent_id)
    return {"skills": skills, "count": len(skills)}


@router.post("/agents/{agent_id}/skills")
def set_agent_skills(agent_id: str, data: Dict[str, Any]):
    """Set skills for an agent (replace all)."""
    from gateway.db.repositories.skill import SkillRepository
    
    skill_ids = data.get("skill_ids", [])
    
    db = get_db()
    repo = SkillRepository(db)
    return repo.set_agent_skills(agent_id, skill_ids)


# ==================== Agent Tools Config ====================

@router.get("/agents/{agent_id}/tools-config")
def get_agent_tools_config(agent_id: str):
    """Get agent's tool configuration."""
    from gateway.db.repositories.drive import DriveRepository
    
    db = get_db()
    repo = DriveRepository(db)
    drive = repo.get_or_create(agent_id)
    
    return {
        "agent_id": agent_id,
        "enabled_tool_categories": drive.get("enabled_tool_categories", []),
        "disabled_tools": drive.get("disabled_tools", []),
        "custom_instructions": drive.get("custom_instructions", ""),
    }


@router.post("/agents/{agent_id}/tools-config")
def save_agent_tools_config(agent_id: str, data: Dict[str, Any]):
    """Save agent's tool configuration."""
    from gateway.db.repositories.drive import DriveRepository
    
    db = get_db()
    repo = DriveRepository(db)
    
    # Ensure drive record exists
    repo.get_or_create(agent_id)
    
    # Build update fields
    now_str = __import__('datetime').datetime.utcnow().isoformat()
    updates = ["updated_at = ?"]
    params = [now_str]
    
    if "enabled_tool_categories" in data:
        updates.append("enabled_tool_categories = ?")
        params.append(json.dumps(data["enabled_tool_categories"], ensure_ascii=False))
    if "disabled_tools" in data:
        updates.append("disabled_tools = ?")
        params.append(json.dumps(data["disabled_tools"], ensure_ascii=False))
    if "custom_instructions" in data:
        updates.append("custom_instructions = ?")
        params.append(data["custom_instructions"])
    
    set_clause = ", ".join(updates)
    params.append(agent_id)
    
    db.execute(
        f"UPDATE agent_drive SET {set_clause} WHERE agent_id = ?",
        tuple(params)
    )
    
    return {"success": True, "agent_id": agent_id}


# ==================== Prompts Preview ====================

@router.get("/agents/{agent_id}/prompts-preview")
def get_prompts_preview(agent_id: str):
    """Preview the system prompt and drive prompt for an agent."""
    from task_queue.client import GatewayInternalClient
    from common.config import ServiceConfig
    
    # Build prompts using the same builders that runtime uses
    client = GatewayInternalClient(ServiceConfig.GATEWAY_URL)
    
    try:
        # System prompt
        try:
            from task_queue.utils.system_prompt import build_system_prompt
            system_prompt = build_system_prompt(agent_id, client)
        except Exception as e:
            system_prompt = f"[Error building system prompt: {e}]"
        
        # Drive prompt
        try:
            from task_queue.utils.drive_prompt import build_drive_prompt
            drive_prompt = build_drive_prompt(agent_id, client)
        except Exception as e:
            drive_prompt = f"[Error building drive prompt: {e}]"
        
        return {
            "agent_id": agent_id,
            "system_prompt": system_prompt or "",
            "system_prompt_length": len(system_prompt or ""),
            "drive_prompt": drive_prompt or "",
            "drive_prompt_length": len(drive_prompt or ""),
        }
    finally:
        client.close()


# ==================== Available Tools ====================

@router.get("/tools/categories")
def get_tool_categories():
    """Get all available tool categories and their tools."""
    from tools_server.tools import BUILTIN_TOOLS
    
    categories = {}
    for cat_name, tools_list in BUILTIN_TOOLS.items():
        categories[cat_name] = {
            "name": cat_name,
            "count": len(tools_list),
            "tools": [{"name": t["name"], "description": t.get("description", "")} for t in tools_list],
        }
    
    return {"categories": categories}
