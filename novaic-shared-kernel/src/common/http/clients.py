"""Unified HTTP client helpers with trust_env semantics."""

from __future__ import annotations

from typing import Any
import httpx

from common.config import ServiceConfig


def internal_async_client(**kwargs: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(**{**kwargs, "trust_env": ServiceConfig.INTERNAL_HTTP_TRUST_ENV})


def internal_sync_client(**kwargs: Any) -> httpx.Client:
    return httpx.Client(**{**kwargs, "trust_env": ServiceConfig.INTERNAL_HTTP_TRUST_ENV})


def external_async_client(**kwargs: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(**{**kwargs, "trust_env": False})


def external_sync_client(**kwargs: Any) -> httpx.Client:
    return httpx.Client(**{**kwargs, "trust_env": False})


internal_client = internal_sync_client
external_client = external_sync_client
