"""
Business-level agent access check — no FastAPI dependency.

Raises ValueError (translated to HTTP 4xx at the edge in main_business.py).
"""

from business.entity_store import get_entity_store


def check_agent_access(agent_id: str, user_id: str) -> dict:
    """Verify agent exists and belongs to user_id.

    Returns the agent dict on success.
    Raises ValueError on 404 / 403.
    """
    agent = get_entity_store().get("agents", "", agent_id)
    if not agent:
        raise ValueError(f"Agent not found: {agent_id}")
    if agent.get("user_id") != user_id:
        raise ValueError(f"Access denied to agent {agent_id}")
    return agent
