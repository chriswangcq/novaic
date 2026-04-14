"""
business/config_actions.py — User preferences entity action handlers.

Migrated from gateway/api/routes.py _build_config_response + agent_actions.py.
Actions: user-preferences.get_config, user-preferences.cleanup
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_config_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """user-preferences.get_config — Build full app configuration response."""
    raw_keys = store.list("api-keys", user_id)

    prefs = None
    try:
        prefs = store.get("user-preferences", user_id, user_id)
    except Exception as e:
        logger.exception("[Config] user-preferences read failed user=%s: %s", user_id, e)

    if not prefs:
        prefs = {
            "default_model": "gpt-4o",
            "audio_model": "",
            "max_tokens": 4096,
            "max_iterations": 20,
            "visible_shell": False,
        }

    return {
        "api_keys": [
            {
                "id": k["id"],
                "name": k["name"],
                "provider": k["provider"],
                "has_api_key": bool(k.get("has_api_key")),
                "api_base": k.get("api_base") or "",
                "deployment_name": k.get("deployment_name"),
                "api_version": k.get("api_version"),
                "created_at": k.get("created_at") or "",
            }
            for k in raw_keys
        ],
        "default_model": prefs.get("default_model", "gpt-4o"),
        "audio_model": prefs.get("audio_model") or "",
        "max_tokens": prefs.get("max_tokens", 4096),
        "max_iterations": prefs.get("max_iterations", 20),
        "visible_shell": prefs.get("visible_shell", False),
    }


def cleanup_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """user-preferences.cleanup — Placeholder."""
    return {"status": "ok", "message": "Cleanup not implemented via action yet"}
