"""
business/api_key_actions.py — API key entity actions.

Handles api-keys.test via direct provider call.
Uses business-internal modules only (no gateway.* imports).
"""

import logging
from typing import Any, Dict

from business.entity_store import get_entity_store
from business.provider_client import test_api_key_direct

logger = logging.getLogger(__name__)


def test_api_key_action(store, user_id: str, params: Dict[str, str], data: Dict[str, Any]) -> dict:
    """api-keys.test — Test API key connection directly against the provider."""
    key_id = data.get("key_id") or data.get("id") or params.get("key_id", "")
    if not key_id:
        raise ValueError("key_id is required")
    try:
        es = get_entity_store()
        key_record = es.get_raw("api-keys", user_id, key_id)
        if not key_record:
            return {"success": False, "error": "API key not found"}
        result = test_api_key_direct(
            provider=key_record.get("provider", "openai"),
            api_key=key_record.get("api_key") or "",
            api_base=key_record.get("api_base") or "",
            deployment_name=key_record.get("deployment_name") or "",
            api_version=key_record.get("api_version") or "",
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
