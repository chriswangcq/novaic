"""
Provider-direct API key testing — business-owned copy.

Tests LLM provider keys by making minimal API calls.
No gateway dependency; uses httpx directly.
"""

import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)

PROVIDER_TIMEOUT = 15.0


def _client(timeout: float = PROVIDER_TIMEOUT) -> httpx.Client:
    return httpx.Client(timeout=timeout, verify=True)


def _get_headers(provider: str, api_key: str) -> Dict[str, str]:
    if provider == "anthropic":
        return {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    if provider == "google":
        return {}
    return {"Authorization": f"Bearer {api_key}"}


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
            with _client() as c:
                resp = c.post(url, headers=headers, json=payload)

        elif provider == "google":
            base = (api_base or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
            url = f"{base}/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": "hi"}]}],
                       "generationConfig": {"maxOutputTokens": 1}}
            with _client() as c:
                resp = c.post(url, json=payload)

        elif provider == "azure":
            if not deployment_name or not api_base:
                return {"success": False, "error": "Azure requires api_base and deployment_name"}
            base = api_base.rstrip("/")
            ver = api_version or "2024-02-01"
            url = f"{base}/openai/deployments/{deployment_name}/chat/completions?api-version={ver}"
            payload = {"messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}
            headers["api-key"] = api_key
            headers.pop("Authorization", None)
            with _client() as c:
                resp = c.post(url, headers=headers, json=payload)

        else:
            base = (api_base or "https://api.openai.com/v1").rstrip("/")
            url = f"{base}/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }
            with _client() as c:
                resp = c.post(url, headers=headers, json=payload)

        if resp.status_code in (401, 403):
            try:
                err = resp.json().get("error", {}).get("message") or resp.text[:200]
            except Exception:
                err = resp.text[:200]
            return {"success": False, "error": err}
        return {"success": True, "status_code": resp.status_code}

    except Exception as e:
        return {"success": False, "error": str(e)}
