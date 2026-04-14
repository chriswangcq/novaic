"""
Internal API module: helpers

Provides SubAgent resolution and dict conversion utilities.
Migrated from SubAgentRepository to EntityStore.
"""

from fastapi import HTTPException
from typing import Dict, Any


# ==================== Helpers ====================

def _subagent_to_dict(subagent) -> Dict[str, Any]:
    """Convert SubAgent (dict or dataclass) to API response dictionary.
    
    Handles both EntityStore dict returns and legacy SubAgent dataclass.
    Includes wake_at, need_rest for B2 agent loop.
    """
    if isinstance(subagent, dict):
        return {
            "subagent_id": subagent.get("subagent_id"),
            "agent_id": subagent.get("agent_id"),
            "type": subagent.get("type"),
            "parent_subagent_id": subagent.get("parent_subagent_id"),
            "status": subagent.get("status"),
            "historical_summary": subagent.get("historical_summary"),
            "wake_triggers": subagent.get("wake_triggers"),
            "wake_at": subagent.get("wake_at"),
            "handoff_notes": subagent.get("handoff_notes"),
            "need_rest": bool(subagent.get("need_rest", 0)),
            "created_at": subagent.get("created_at"),
            "updated_at": subagent.get("updated_at"),
        }
    # Legacy dataclass fallback
    return {
        "subagent_id": subagent.subagent_id,
        "agent_id": subagent.agent_id,
        "type": subagent.type,
        "parent_subagent_id": subagent.parent_subagent_id,
        "status": subagent.status,
        "historical_summary": subagent.historical_summary,
        "wake_triggers": subagent.wake_triggers,
        "wake_at": getattr(subagent, "wake_at", None),
        "handoff_notes": subagent.handoff_notes,
        "need_rest": bool(getattr(subagent, "need_rest", 0)),
        "created_at": subagent.created_at,
        "updated_at": subagent.updated_at,
    }

# ==================== SubAgent Resolution (B2: Gateway owns subagent) ====================

def resolve_agent_id_from_subagent(subagent_id: str) -> str:
    """
    Resolve agent_id from subagent_id via EntityStore (B2: Gateway owns subagent).
    
    For Gateway business APIs that accept subagent_id-only input.
    
    Args:
        subagent_id: SubAgent ID (globally unique)
    
    Returns:
        agent_id: Agent that owns this SubAgent
    
    Raises:
        HTTPException: If subagent not found (404)
    """
    from business.entity_store import get_entity_store
    store = get_entity_store()
    # user_id="" bypasses scope for internal system lookup
    subagent = store.get("subagents", "", subagent_id)
    if not subagent:
        raise HTTPException(status_code=404, detail=f"SubAgent not found: {subagent_id}")
    return subagent["agent_id"]


# Exported functions
__all__ = [
    "resolve_agent_id_from_subagent",
    "_subagent_to_dict",
]
