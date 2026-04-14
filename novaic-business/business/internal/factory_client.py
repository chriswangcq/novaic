"""
Business -> LLM Factory / Provider client

The Business service uses this module to:
1. Resolve model metadata via Factory (e.g. model display names) for agent dispatch.
2. Call providers directly for model lists and API key tests (not via Factory CRUD).

API keys are not duplicated in Factory; they live in NovAIC storage (Entangled /
entity layer), not in the Factory service.
"""

import logging
import httpx
from typing import Dict, Any, List

from common.config import ServiceConfig

logger = logging.getLogger("business")

FACTORY_URL = ServiceConfig.LLM_FACTORY_URL
FACTORY_TIMEOUT = 10.0
PROVIDER_TIMEOUT = 15.0


def _client(timeout: float = FACTORY_TIMEOUT) -> httpx.Client:
    return httpx.Client(timeout=timeout, verify=True)


# ────────────────────────────────────────────────────────────────────────────────
# Provider-Direct: API Key Test & Fetch Models
# (keys come from NovAIC entities; direct provider calls, not Factory CRUD)
# ────────────────────────────────────────────────────────────────────────────────

def _get_headers(provider: str, api_key: str) -> Dict[str, str]:
    """Build provider-specific auth headers."""
    if provider == "anthropic":
        return {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    if provider == "google":
        return {}  # Google uses query param
    return {"Authorization": f"Bearer {api_key}"}


def _models_url(provider: str, api_base: str) -> str:
    """Return the model-list URL for each provider."""
    if provider == "openai":
        base = (api_base or "https://api.openai.com/v1").rstrip("/")
        return f"{base}/models"
    if provider == "anthropic":
        # Anthropic has no public model-list endpoint → hardcode known models
        return ""
    if provider == "google":
        base = (api_base or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        return f"{base}/models"
    if provider == "azure":
        # Azure doesn't have a simple /models endpoint; list deployments via base URL
        return ""
    # openai_compatible
    base = (api_base or "").rstrip("/")
    return f"{base}/models" if base else ""


# Hardcoded model lists for providers without a model-list endpoint
_ANTHROPIC_MODELS = [
    {"id": "claude-opus-4-5", "name": "Claude Opus 4.5"},
    {"id": "claude-opus-4-0", "name": "Claude Opus 4"},
    {"id": "claude-sonnet-4-5", "name": "Claude Sonnet 4.5"},
    {"id": "claude-sonnet-4-0", "name": "Claude Sonnet 4"},
    {"id": "claude-haiku-3-5", "name": "Claude Haiku 3.5"},
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
]

_AZURE_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o"},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
    {"id": "gpt-4", "name": "GPT-4"},
    {"id": "o1", "name": "o1"},
    {"id": "o1-mini", "name": "o1-mini"},
]


def fetch_models_direct(provider: str, api_key: str, api_base: str = "") -> List[Dict[str, Any]]:
    """Fetch model list directly from the provider (not via Factory).

    Returns a list of {"id": ..., "name": ...} dicts.
    """
    # Hardcoded providers
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
        with _client(PROVIDER_TIMEOUT) as client:
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

    # Normalize response
    models = []
    if provider == "google":
        for m in data.get("models", []):
            mid = m.get("name", "").split("/")[-1]  # "models/gemini-pro" → "gemini-pro"
            name = m.get("displayName") or mid
            if mid:
                models.append({"id": mid, "name": name})
    else:
        # OpenAI / openai_compatible format: {"data": [{"id": ..., }, ...]}
        raw = data if isinstance(data, list) else data.get("data", [])
        for m in raw:
            mid = m.get("id", "")
            name = m.get("name") or mid
            if mid:
                models.append({"id": mid, "name": name})

    return models


def test_api_key_direct(provider: str, api_key: str, api_base: str = "",
                        deployment_name: str = "", api_version: str = "") -> Dict[str, Any]:
    """Test API key by making a minimal call to the provider.

    Returns {"success": True} or {"success": False, "error": "..."}.
    """
    headers = _get_headers(provider, api_key)

    try:
        if provider == "anthropic":
            url = f"{(api_base or 'https://api.anthropic.com').rstrip('/')}/v1/messages"
            payload = {
                "model": "claude-haiku-3-5",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
            with _client(PROVIDER_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=payload)

        elif provider == "google":
            base = (api_base or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
            url = f"{base}/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": "hi"}]}],
                       "generationConfig": {"maxOutputTokens": 1}}
            with _client(PROVIDER_TIMEOUT) as client:
                resp = client.post(url, json=payload)

        elif provider == "azure":
            if not deployment_name or not api_base:
                return {"success": False, "error": "Azure requires api_base and deployment_name"}
            base = api_base.rstrip("/")
            ver = api_version or "2024-02-01"
            url = f"{base}/openai/deployments/{deployment_name}/chat/completions?api-version={ver}"
            payload = {"messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}
            headers["api-key"] = api_key
            headers.pop("Authorization", None)
            with _client(PROVIDER_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=payload)

        else:
            # openai / openai_compatible
            base = (api_base or "https://api.openai.com/v1").rstrip("/")
            url = f"{base}/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }
            with _client(PROVIDER_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=payload)

        # 401 / 403 = auth error; 200 / 400 (bad request but auth OK) = key valid
        if resp.status_code in (401, 403):
            try:
                err = resp.json().get("error", {}).get("message") or resp.text[:200]
            except Exception:
                err = resp.text[:200]
            return {"success": False, "error": err}
        return {"success": True, "status_code": resp.status_code}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ────────────────────────────────────────────────────────────────────────────────
# Worker: Agent LLM Config (still via Factory for actual LLM calls)
# ────────────────────────────────────────────────────────────────────────────────

def build_llm_config_for_agent_via_factory(
    db, agent_id: str, use_audio_model: bool = False
) -> Dict[str, Any]:
    """构建 agent 的 LLM 调用配置

    从 Entangled EntityStore 读取 agent 信息（model_id, user_id）。
    返回 model_id + user_id + factory_url，调用方直接 POST Factory /v1/chat/completions。
    Business 不在此返回中嵌入 api_key；推理侧由 Factory 使用其持有的凭据。
    """
    from business.entity_store import get_entity_store
    store = get_entity_store()

    agent = store.get("agents", "", agent_id)
    if not agent:
        return {"success": False, "error": f"Agent '{agent_id}' not found", "agent_id": agent_id}

    agent_model_id = agent.get("model_id") or None
    owner_user_id = agent.get("user_id") or ""

    if not owner_user_id:
        return {"success": False, "error": f"Agent '{agent_id}' has no owner user_id", "agent_id": agent_id}

    model_id = agent_model_id

    if use_audio_model or not model_id:
        prefs = store.get("user-preferences", owner_user_id, owner_user_id)
        if prefs:
            if use_audio_model and prefs.get("audio_model"):
                model_id = prefs["audio_model"]
            if not model_id and prefs.get("default_model"):
                model_id = prefs["default_model"]

    if not model_id:
        return {"success": False, "error": f"No model configured for agent '{agent_id}'", "agent_id": agent_id}

    model_name = _resolve_model_name(model_id)

    return {
        "success": True,
        "agent_id": agent_id,
        "model_id": model_id,
        "model_name": model_name,
        "user_id": owner_user_id,
        "factory_url": FACTORY_URL,
    }


# ────────────────────────────────────────────────────────────────────────────────
# Model Name Cache (for LLM dispatch — model_id → display name)
# ────────────────────────────────────────────────────────────────────────────────

import time as _time

_MODEL_NAME_CACHE: Dict[str, tuple] = {}  # model_id → (model_name, expire_ts)
_CACHE_TTL = 300  # 5 分钟


def _resolve_model_name(model_id: str) -> str:
    """从 Factory 解析 model 显示名，带 TTL 内存缓存"""
    now = _time.time()

    cached = _MODEL_NAME_CACHE.get(model_id)
    if cached and cached[1] > now:
        return cached[0]

    try:
        with _client() as client:
            resp = client.get(f"{FACTORY_URL}/v1/config/models/{model_id}")
            if resp.status_code == 200:
                data = resp.json()
                name = data.get("model_name") or data.get("name") or model_id
                _MODEL_NAME_CACHE[model_id] = (name, now + _CACHE_TTL)
                return name
    except Exception as e:
        logger.warning("[FactoryClient] Failed to resolve model_name for %s: %s", model_id, e)

    _MODEL_NAME_CACHE[model_id] = (model_id, now + 30)
    return model_id
