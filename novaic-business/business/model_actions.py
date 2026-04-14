"""
business/model_actions.py — Model entity action handlers.

Migrated from gateway/entity/defs_models.py action functions +
fetch_models_direct from gateway/api/internal/factory_client.py.

Actions:
  models.add_custom
  api-key-models.refresh, api-key-models.remove
  available-models.toggle
"""

import logging
import uuid as _uuid
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Provider-Direct Model Fetching (from factory_client.py)
# ═══════════════════════════════════════════════════════════════════════════════

_PROVIDER_TIMEOUT = 15.0

_ANTHROPIC_MODELS = [
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
]

_AZURE_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
    {"id": "gpt-4", "name": "GPT-4"},
    {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo"},
]


def _get_headers(provider: str, api_key: str) -> Dict[str, str]:
    if provider == "anthropic":
        return {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    if provider == "google":
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def _models_url(provider: str, api_base: str) -> str:
    if provider == "openai":
        base = (api_base or "https://api.openai.com/v1").rstrip("/")
        return f"{base}/models"
    if provider == "anthropic":
        return ""
    if provider == "google":
        return "https://generativelanguage.googleapis.com/v1beta/models"
    if provider == "azure":
        return ""
    base = (api_base or "").rstrip("/")
    return f"{base}/models" if base else ""


def fetch_models_direct(provider: str, api_key: str, api_base: str = "") -> List[Dict[str, Any]]:
    """Fetch model list directly from the provider."""
    if provider == "anthropic":
        return _ANTHROPIC_MODELS
    if provider == "azure":
        return _AZURE_MODELS

    url = _models_url(provider, api_base)
    if not url:
        logger.warning("[Provider] No model-list URL for provider=%s", provider)
        return []

    headers = _get_headers(provider, api_key)
    params = {}
    if provider == "google":
        params["key"] = api_key

    try:
        with httpx.Client(timeout=_PROVIDER_TIMEOUT) as client:
            resp = client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.warning("[Provider] fetch_models HTTP %s for provider=%s: %s",
                       e.response.status_code, provider, e.response.text[:300])
        return []
    except Exception as e:
        logger.warning("[Provider] fetch_models failed for provider=%s: %s", provider, e)
        return []

    models = []
    if provider == "google":
        for m in data.get("models", []):
            mid = m.get("name", "").split("/")[-1]
            name = m.get("displayName") or mid
            if mid:
                models.append({"id": mid, "name": name})
    else:
        raw = data if isinstance(data, list) else data.get("data", [])
        for m in raw:
            mid = m.get("id", "")
            name = m.get("name") or mid
            if mid:
                models.append({"id": mid, "name": name})

    return models


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _get_api_key_raw(store, user_id: str, api_key_id: str) -> dict | None:
    """Get api_key record including hidden fields (api_key plaintext)."""
    return store.get_raw("api-keys", user_id, api_key_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Action Handlers
# ═══════════════════════════════════════════════════════════════════════════════

def add_custom_model_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """models.add_custom — Add a custom model to the global registry + api-key-models."""
    api_key_id = payload.get("api_key_id")
    model_id = payload.get("model_id")
    name = payload.get("name", model_id)
    if not api_key_id or not model_id:
        raise ValueError("api_key_id and model_id are required")

    api_key = store.get("api-keys", user_id, api_key_id)
    if not api_key:
        raise ValueError(f"API key {api_key_id} not found")
    provider = api_key.get("provider", "openai")

    store.upsert("models", user_id, model_id, {
        "model_id": model_id,
        "name": name,
        "provider": provider,
        "is_custom": 1,
    })

    existing_akm = store.list("api-key-models", user_id, params={"api_key_id": api_key_id})
    if not any(r["model_id"] == model_id for r in existing_akm):
        result = store.create("api-key-models", user_id, {
            "id": str(_uuid.uuid4()),
            "user_id": user_id,
            "api_key_id": api_key_id,
            "model_id": model_id,
        })
        return result
    return {"model_id": model_id, "api_key_id": api_key_id, "already_exists": True}


def refresh_api_key_models_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """api-key-models.refresh — Fetch from provider, upsert into models + api_key_models."""
    api_key_id = payload.get("api_key_id") or (params or {}).get("api_key_id")
    if not api_key_id:
        raise ValueError("api_key_id is required")

    key_record = _get_api_key_raw(store, user_id, api_key_id)
    if not key_record:
        raise ValueError(f"API key {api_key_id} not found")

    provider = key_record.get("provider", "openai")
    api_key = key_record.get("api_key") or ""
    api_base = key_record.get("api_base") or ""

    fetched = fetch_models_direct(provider, api_key, api_base)

    for fm in fetched:
        mid = fm.get("id", "") if isinstance(fm, dict) else str(fm)
        fname = fm.get("name", mid) if isinstance(fm, dict) else mid
        if not mid:
            continue
        store.upsert("models", user_id, mid, {
            "model_id": mid,
            "name": fname,
            "provider": provider,
            "is_custom": 0,
        })

    existing_akm = store.list("api-key-models", user_id, params={"api_key_id": api_key_id})
    existing_mids = {r["model_id"]: r["id"] for r in existing_akm}
    fetched_mids = set()
    for fm in fetched:
        mid = fm.get("id", "") if isinstance(fm, dict) else str(fm)
        if not mid:
            continue
        fetched_mids.add(mid)
        if mid not in existing_mids:
            store.create("api-key-models", user_id, {
                "id": str(_uuid.uuid4()),
                "user_id": user_id,
                "api_key_id": api_key_id,
                "model_id": mid,
            })

    for akm in existing_akm:
        if akm["model_id"] not in fetched_mids:
            model_record = store.get("models", user_id, akm["model_id"])
            if not (model_record and model_record.get("is_custom")):
                store.delete("api-key-models", user_id, akm["id"])

    return {"fetched": len(fetched), "api_key_id": api_key_id}


def remove_api_key_model_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """api-key-models.remove — Delete from api-key-models; if custom and last key, also delete from models."""
    record_id = payload.get("id")
    if not record_id:
        raise ValueError("id (api-key-models UUID) is required")

    record = store.get("api-key-models", user_id, record_id)
    if not record:
        raise ValueError(f"api-key-models record {record_id} not found")

    model_id = record["model_id"]
    store.delete("api-key-models", user_id, record_id)

    model_record = store.get("models", user_id, model_id)
    if model_record and model_record.get("is_custom"):
        remaining_akm = store.count("api-key-models", user_id, filters={"model_id": model_id})
        if remaining_akm == 0:
            store.delete("models", user_id, model_id)

    available = store.list("available-models", user_id)
    for am in available:
        if am["model_id"] == model_id:
            store.delete("available-models", user_id, am["id"])

    return {"deleted": record_id, "model_id": model_id}


def toggle_available_model_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """available-models.toggle — Enable/disable a model for the user."""
    model_id = payload.get("model_id")
    api_key_id = payload.get("api_key_id")
    enable = bool(payload.get("available", payload.get("enable", True)))
    if not model_id or not api_key_id:
        raise ValueError("model_id and api_key_id are required")

    existing = store.list("available-models", user_id)
    existing_record = next((r for r in existing if r["model_id"] == model_id), None)

    if enable:
        if not existing_record:
            store.create("available-models", user_id, {
                "id": str(_uuid.uuid4()),
                "user_id": user_id,
                "model_id": model_id,
                "api_key_id": api_key_id,
            })
    else:
        if existing_record:
            store.delete("available-models", user_id, existing_record["id"])

    return {"model_id": model_id, "available": enable}
