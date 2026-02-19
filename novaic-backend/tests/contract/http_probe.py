"""
Shared local probe helper for contract/startup tests.
"""

import httpx


def local_get(url: str, timeout: float = 2.0) -> httpx.Response:
    """HTTP GET for localhost endpoints, never using system proxy env."""
    with httpx.Client(trust_env=False, timeout=timeout) as client:
        return client.get(url)

