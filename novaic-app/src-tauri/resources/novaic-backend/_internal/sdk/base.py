"""
Base HTTP Client for Gateway SDK
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import aiohttp

from .exceptions import (
    GatewayError,
    GatewayConnectionError,
    GatewayTimeoutError,
    GatewayNotFoundError,
    GatewayConflictError,
    GatewayValidationError,
    GatewayServerError,
)

logger = logging.getLogger(__name__)


class BaseAPI:
    """Base class for API modules."""
    
    def __init__(self, http: 'HttpClient'):
        self._http = http
    
    @property
    def gateway_url(self) -> str:
        return self._http.gateway_url


class HttpClient:
    """
    HTTP client with retry, timeout, and error handling.
    """
    
    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:19999",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session (thread-safe)."""
        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(timeout=self.timeout)
            return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _handle_error(self, status: int, response_data: dict = None):
        """Convert HTTP status to appropriate exception."""
        msg = response_data.get("detail", "Unknown error") if response_data else "Unknown error"
        
        if status == 404:
            raise GatewayNotFoundError(msg, status, response_data)
        elif status == 409:
            raise GatewayConflictError(msg, status, response_data)
        elif status in (400, 422):
            raise GatewayValidationError(msg, status, response_data)
        elif status >= 500:
            raise GatewayServerError(msg, status, response_data)
        else:
            raise GatewayError(msg, status, response_data)
    
    async def _request(
        self,
        method: str,
        url: str,
        json: dict = None,
        params: dict = None,
        timeout: float = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        """
        session = await self._get_session()
        request_timeout = aiohttp.ClientTimeout(total=timeout) if timeout else self.timeout
        
        last_error = None
        retries = self.max_retries if retry else 1
        
        for attempt in range(retries):
            try:
                async with session.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    timeout=request_timeout,
                ) as resp:
                    # Try to parse response
                    try:
                        data = await resp.json()
                    except Exception as parse_error:
                        # Get raw response for debugging
                        try:
                            raw_text = await resp.text()
                        except Exception:
                            raw_text = "<failed to read>"
                        
                        # Log detailed error info
                        logger.error(
                            f"JSON parse error for {method} {url}:\n"
                            f"  Status: {resp.status}\n"
                            f"  Content-Type: {resp.headers.get('Content-Type', 'unknown')}\n"
                            f"  Content-Length: {resp.headers.get('Content-Length', 'unknown')}\n"
                            f"  Raw response: {raw_text[:500] if raw_text else '<empty>'}\n"
                            f"  Error: {parse_error}"
                        )
                        
                        # For successful responses, this is a critical error
                        if resp.status < 400:
                            raise GatewayError(
                                f"Failed to parse response JSON: {parse_error}. "
                                f"Content-Type: {resp.headers.get('Content-Type')}, "
                                f"Raw: {raw_text[:200] if raw_text else '<empty>'}",
                                resp.status,
                                {"raw_error": str(parse_error), "raw_response": raw_text[:500] if raw_text else None}
                            )
                        data = {}
                    
                    # Handle errors
                    if resp.status >= 400:
                        # Don't retry client errors (4xx) except timeouts
                        if 400 <= resp.status < 500 and resp.status not in (408, 429):
                            self._handle_error(resp.status, data)
                        
                        last_error = GatewayError(
                            data.get("detail", f"HTTP {resp.status}"),
                            resp.status,
                            data
                        )
                        
                        # Retry server errors
                        if attempt < retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        
                        self._handle_error(resp.status, data)
                    
                    return data
                    
            except aiohttp.ClientConnectorError as e:
                last_error = GatewayConnectionError(str(e))
                if attempt < retries - 1:
                    logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise last_error
                
            except asyncio.TimeoutError:
                last_error = GatewayTimeoutError(f"Request timed out after {timeout or self.timeout.total}s")
                if attempt < retries - 1:
                    logger.warning(f"Timeout (attempt {attempt + 1})")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise last_error
        
        raise last_error or GatewayError("Unknown error after retries")
    
    # Convenience methods
    
    async def get(self, url: str, params: dict = None, **kwargs) -> Dict[str, Any]:
        """HTTP GET request."""
        return await self._request("GET", url, params=params, **kwargs)
    
    async def post(self, url: str, json: dict = None, **kwargs) -> Dict[str, Any]:
        """HTTP POST request."""
        return await self._request("POST", url, json=json, **kwargs)
    
    async def patch(self, url: str, json: dict = None, **kwargs) -> Dict[str, Any]:
        """HTTP PATCH request."""
        return await self._request("PATCH", url, json=json, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """HTTP DELETE request."""
        return await self._request("DELETE", url, **kwargs)
    
    async def put(self, url: str, json: dict = None, **kwargs) -> Dict[str, Any]:
        """HTTP PUT request."""
        return await self._request("PUT", url, json=json, **kwargs)
