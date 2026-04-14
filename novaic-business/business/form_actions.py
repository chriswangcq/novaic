"""
business/form_actions.py — Agent form entity action handlers.

Migrated from gateway/entity/defs_agent_forms.py inline functions.
Actions: agent-tools.get_bootstrap, agent-tools.save_bootstrap
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def bootstrap_get_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """agent-tools.get_bootstrap — Read bootstrap files from agent-tools entity cache."""
    agent_id = data.get("agent_id") or data.get("id") or (params or {}).get("agent_id", "")
    if not agent_id:
        raise ValueError("agent_id required")
    drive = store.get("agent-tools", "", agent_id, params={"agent_id": agent_id}) or {}
    return {
        "soul_md":               drive.get("soul_md", ""),
        "heartbeat_md":          drive.get("heartbeat_md", ""),
        "memory_md":             drive.get("memory_md", ""),
        "user_md":               drive.get("user_md", ""),
        "behavior_guide_md":     drive.get("behavior_guide_md", ""),
        "capability_list_md":    drive.get("capability_list_md", ""),
        "sub_subagent_guide_md": drive.get("sub_subagent_guide_md", ""),
        "active_hours_start":    drive.get("active_hours_start", "09:00"),
        "active_hours_end":      drive.get("active_hours_end", "22:00"),
        "active_hours_timezone":  drive.get("active_hours_timezone", "Asia/Shanghai"),
    }


def bootstrap_save_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """agent-tools.save_bootstrap — Write bootstrap fields to agent-tools entity (upsert)."""
    agent_id = data.get("agent_id") or data.get("id") or (params or {}).get("agent_id", "")
    if not agent_id:
        raise ValueError("agent_id required")
    bootstrap_fields = [
        "soul_md", "heartbeat_md", "memory_md", "user_md",
        "behavior_guide_md", "capability_list_md", "sub_subagent_guide_md",
        "active_hours_start", "active_hours_end", "active_hours_timezone",
    ]
    update = {k: data[k] for k in bootstrap_fields if k in data and data[k] is not None}
    if not update:
        return {"success": True, "agent_id": agent_id, "no_changes": True}
    store.upsert("agent-tools", "", agent_id, update, params={"agent_id": agent_id})
    return {"success": True, "agent_id": agent_id}
