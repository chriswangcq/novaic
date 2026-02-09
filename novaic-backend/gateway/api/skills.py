"""
Skills & Agent Tools Config API

Public API endpoints for managing skills, agent-skill assignments,
and per-agent tool configuration.

Supports:
- Builtin skills: read-only, loaded from SKILL.md files
- Custom skills: user-created, fully editable
- Fork: create editable copy of builtin skill
- Auto-matching: match skills to tasks based on keywords
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import json

from common.utils.time import utc_now_iso
from gateway.db.access import get_db

router = APIRouter(prefix="/api", tags=["skills"])


# ==================== Skills CRUD ====================
# IMPORTANT: Fixed routes (like /skills/match) must come BEFORE parameterized routes (like /skills/{skill_id})

@router.get("/skills")
def list_skills(include_builtin: bool = Query(True, description="Include builtin skills")):
    """List all skills (builtin + custom)."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    skills = repo.list_all(include_builtin=include_builtin)
    
    # Separate builtin and custom for easier frontend handling
    builtin_skills = [s for s in skills if s.get("source") == "builtin"]
    custom_skills = [s for s in skills if s.get("source") != "builtin"]
    
    return {
        "skills": skills,
        "builtin_skills": builtin_skills,
        "custom_skills": custom_skills,
        "count": len(skills),
        "builtin_count": len(builtin_skills),
        "custom_count": len(custom_skills),
    }


@router.post("/skills")
def create_skill(data: Dict[str, Any]):
    """Create a new custom skill."""
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
        auto_match_keywords=data.get("auto_match_keywords", []),
    )
    return skill


# ==================== Skills Auto-Matching ====================
# NOTE: This MUST be before /skills/{skill_id} routes to avoid being matched as skill_id="match"

@router.post("/skills/match")
def match_skills_for_task(data: Dict[str, Any]):
    """Match skills based on task description using keywords."""
    from gateway.db.repositories.skill import SkillRepository
    
    task = data.get("task", "")
    max_skills = data.get("max_skills", 3)
    
    if not task:
        raise HTTPException(status_code=400, detail="task is required")
    
    db = get_db()
    repo = SkillRepository(db)
    matched_skills = repo.match_skills_for_task(task, max_skills=max_skills)
    
    return {
        "task": task,
        "matched_skills": matched_skills,
        "count": len(matched_skills),
    }


# ==================== Skills with {skill_id} parameter ====================

@router.get("/skills/{skill_id}")
def get_skill(skill_id: str):
    """Get a skill by ID (supports builtin:xxx format)."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    skill = repo.get_by_id(skill_id)
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    return skill


@router.post("/skills/{skill_id}/fork")
def fork_skill(skill_id: str, data: Dict[str, Any] = None):
    """Fork a builtin skill to create an editable custom copy."""
    from gateway.db.repositories.skill import SkillRepository
    
    if data is None:
        data = {}
    
    # Extract builtin_id from skill_id (e.g., "builtin:desktop" -> "desktop")
    if skill_id.startswith("builtin:"):
        builtin_id = skill_id[8:]
    else:
        raise HTTPException(status_code=400, detail="Can only fork builtin skills. Use skill_id format: builtin:xxx")
    
    db = get_db()
    repo = SkillRepository(db)
    
    try:
        skill = repo.fork_builtin(builtin_id, new_name=data.get("name"))
        return skill
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/skills/{skill_id}")
def update_skill(skill_id: str, data: Dict[str, Any]):
    """Update an existing skill. Builtin skills cannot be updated."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    
    existing = repo.get_by_id(skill_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if trying to update a builtin skill
    if existing.get("source") == "builtin":
        raise HTTPException(status_code=400, detail="Cannot update builtin skills. Fork it first to create an editable copy.")
    
    try:
        skill = repo.update(
            skill_id=skill_id,
            name=data.get("name"),
            description=data.get("description"),
            prompt=data.get("prompt"),
            tools=data.get("tools"),
            workflow=data.get("workflow"),
            icon=data.get("icon"),
            enabled=data.get("enabled"),
            auto_match_keywords=data.get("auto_match_keywords"),
        )
        return skill
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: str):
    """Delete a skill. Builtin skills cannot be deleted."""
    from gateway.db.repositories.skill import SkillRepository
    
    db = get_db()
    repo = SkillRepository(db)
    
    # Check if trying to delete a builtin skill
    existing = repo.get_by_id(skill_id)
    if existing and existing.get("source") == "builtin":
        raise HTTPException(status_code=400, detail="Cannot delete builtin skills.")
    
    try:
        return repo.delete(skill_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    # Use pure read (no lock) for GET requests
    drive = repo.get(agent_id)
    
    if not drive:
        # Return defaults if no drive record exists
        return {
            "agent_id": agent_id,
            "disabled_tools": [],
            "custom_instructions": "",
        }
    
    return {
        "agent_id": agent_id,
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
    now_str = utc_now_iso()
    updates = ["updated_at = ?"]
    params = [now_str]
    
    if "disabled_tools" in data:
        updates.append("disabled_tools = ?")
        params.append(json.dumps(data["disabled_tools"], ensure_ascii=False))
    if "custom_instructions" in data:
        updates.append("custom_instructions = ?")
        params.append(data["custom_instructions"])
    
    set_clause = ", ".join(updates)
    params.append(agent_id)
    
    # Execute UPDATE within transaction to ensure proper commit
    with db.transaction(lock_type="agent", resource_id=agent_id):
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
        from task_queue.utils.system_prompt import build_system_prompt, build_wake_message
        
        # System prompt (统一的，不区分场景)
        try:
            system_prompt = build_system_prompt(agent_id, client)
        except Exception as e:
            system_prompt = f"[Error building system prompt: {e}]"
        
        # Wake message (定时唤醒时的消息内容，写入 DB 作为 user message)
        try:
            wake_message = build_wake_message(agent_id, client)
        except Exception as e:
            wake_message = f"[Error building wake message: {e}]"
        
        return {
            "agent_id": agent_id,
            "system_prompt": system_prompt or "",
            "system_prompt_length": len(system_prompt or ""),
            "wake_message": wake_message or "",
            "wake_message_length": len(wake_message or ""),
            "note": "System Prompt 统一。定时唤醒时，wake_message 作为普通消息写入 DB，由 ReactThink 统一读取。",
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


# ==================== Bootstrap Files ====================

@router.get("/agents/{agent_id}/bootstrap-files")
def get_bootstrap_files(agent_id: str):
    """Get agent's bootstrap files and active hours configuration."""
    from gateway.db.repositories.drive import DriveRepository
    
    db = get_db()
    repo = DriveRepository(db)
    
    # 使用 get() 方法（纯读取，不创建）
    drive = repo.get(agent_id)
    if not drive:
        # 返回默认值
        return {
            "soul_md": "",
            "heartbeat_md": "",
            "memory_md": "",
            "user_md": "",
            "active_hours_start": "09:00",
            "active_hours_end": "22:00",
            "active_hours_timezone": "Asia/Shanghai",
        }
    
    return {
        "soul_md": drive.get("soul_md", ""),
        "heartbeat_md": drive.get("heartbeat_md", ""),
        "memory_md": drive.get("memory_md", ""),
        "user_md": drive.get("user_md", ""),
        "active_hours_start": drive.get("active_hours_start", "09:00"),
        "active_hours_end": drive.get("active_hours_end", "22:00"),
        "active_hours_timezone": drive.get("active_hours_timezone", "Asia/Shanghai"),
    }


@router.post("/agents/{agent_id}/bootstrap-files")
def save_bootstrap_files(agent_id: str, data: Dict[str, Any]):
    """Save agent's bootstrap files and active hours configuration."""
    from gateway.db.repositories.drive import DriveRepository
    
    db = get_db()
    repo = DriveRepository(db)
    
    # 确保 agent_drive 记录存在
    repo.get_or_create(agent_id)
    
    # 调用 update_bootstrap_files 方法
    result = repo.update_bootstrap_files(
        agent_id=agent_id,
        soul_md=data.get("soul_md"),
        heartbeat_md=data.get("heartbeat_md"),
        memory_md=data.get("memory_md"),
        user_md=data.get("user_md"),
        active_hours_start=data.get("active_hours_start"),
        active_hours_end=data.get("active_hours_end"),
        active_hours_timezone=data.get("active_hours_timezone"),
    )
    
    return result
