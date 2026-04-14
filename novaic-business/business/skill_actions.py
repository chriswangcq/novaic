"""
business/skill_actions.py — Skills entity actions (Entangled hooks).

All handlers: (store, user_id, params, data) -> Any
Uses business-internal modules only (no gateway.* imports).
"""

import logging

from business.skill_repository import SkillRepository
from business.entity_store import get_entity_store
from business.auth import check_agent_access

logger = logging.getLogger(__name__)


def match_skills_action(store, user_id: str, params: dict, data: dict):
    task = data.get("task", "")
    max_skills = int(data.get("max_skills", 3))
    if not task:
        raise ValueError("task is required")
    repo = SkillRepository()
    matched = repo.match_skills_for_task(task, user_id=user_id, max_skills=max_skills)
    return {"task": task, "matched_skills": matched, "count": len(matched)}


def fork_skill_action(store, user_id: str, params: dict, data: dict):
    skill_id = data.get("skill_id") or data.get("id", "")
    if not skill_id:
        raise ValueError("skill_id is required")
    if not skill_id.startswith("builtin:"):
        raise ValueError("Can only fork builtin skills (skill_id must start with 'builtin:')")
    repo = SkillRepository()
    return repo.fork_builtin(skill_id[8:], user_id=user_id, new_name=data.get("name"))


def get_tool_categories_action(store, user_id: str, params: dict, data: dict):
    """Return all available tool categories."""
    from common.tools import BUILTIN_TOOLS

    categories = {}
    for cat_name, tools_list in BUILTIN_TOOLS.items():
        categories[cat_name] = {
            "name": cat_name,
            "count": len(tools_list),
            "tools": [{"name": t["name"], "description": t.get("description", "")}
                      for t in tools_list],
        }
    return {"categories": categories}


def get_agent_skills_action(store, user_id: str, params: dict, data: dict):
    agent_id = data.get("agent_id") or params.get("agent_id", "")
    if not agent_id:
        raise ValueError("agent_id is required")
    repo = SkillRepository()
    skills = repo.get_agent_skills(agent_id, user_id)
    return {"skills": skills, "count": len(skills)}


def set_agent_skills_action(store, user_id: str, params: dict, data: dict):
    agent_id = data.get("agent_id") or params.get("agent_id", "")
    skill_ids = data.get("skill_ids", [])
    if not agent_id:
        raise ValueError("agent_id is required")
    repo = SkillRepository()
    repo.set_agent_skills(agent_id, skill_ids, user_id=user_id)
    return {"success": True}


def get_agent_tools_config_action(store, user_id: str, params: dict, data: dict):
    agent_id = data.get("agent_id") or params.get("agent_id", "")
    if not agent_id:
        raise ValueError("agent_id is required")
    check_agent_access(agent_id, user_id)
    es = get_entity_store()
    drive = es.get("agent-tools", user_id, agent_id)
    if not drive:
        return {"agent_id": agent_id, "disabled_tools": [], "custom_instructions": ""}
    return {
        "agent_id": agent_id,
        "disabled_tools": drive.get("disabled_tools", []),
        "custom_instructions": drive.get("custom_instructions", ""),
    }


def save_agent_tools_config_action(store, user_id: str, params: dict, data: dict):
    agent_id = data.get("agent_id") or params.get("agent_id", "")
    if not agent_id:
        raise ValueError("agent_id is required")
    check_agent_access(agent_id, user_id)
    es = get_entity_store()
    update_data = {}
    if data.get("disabled_tools") is not None:
        update_data["disabled_tools"] = [x for x in data["disabled_tools"] if isinstance(x, str)]
    if data.get("custom_instructions") is not None:
        update_data["custom_instructions"] = data["custom_instructions"]
    es.upsert("agent-tools", user_id, agent_id, update_data)
    return {"success": True, "agent_id": agent_id}
