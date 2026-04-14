"""
Business Service Entity Store — thin wrapper over EntangledServiceClient.

No gateway.db, no PC client, no LOCAL_ONLY entities.
Pure HTTP CRUD against standalone Entangled service.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_store: Optional["BusinessEntityStore"] = None


class BusinessEntityStore:
    """Lightweight entity store backed entirely by Entangled HTTP."""

    def __init__(self):
        self._ec = None

    @property
    def _ent(self):
        if self._ec is None:
            from common.entangled_client import EntangledServiceClient
            self._ec = EntangledServiceClient()
        return self._ec

    def get(self, entity: str, user_id: str, item_id: str, **kw) -> Optional[Dict[str, Any]]:
        return self._ent.get(entity, item_id, user_id=user_id, **kw)

    def list(self, entity: str, user_id: str, *, params: Optional[Dict] = None,
             filters: Optional[Dict] = None,
             order_by: Optional[str] = None, limit: int = 200,
             skip_default_not_in: bool = False,
             not_in_filters: Optional[Dict] = None,
             **kw) -> List[Dict[str, Any]]:
        if filters is not None or skip_default_not_in or not_in_filters is not None:
            return self._ent.list_advanced(
                entity, user_id=user_id, params=params,
                filters=filters, order_by=order_by, limit=limit,
                skip_default_not_in=skip_default_not_in, **kw,
            )
        return self._ent.list(entity, user_id=user_id, params=params,
                              order_by=order_by, limit=limit, **kw)

    def create(self, entity: str, user_id: str, data: Dict[str, Any], **kw) -> Dict[str, Any]:
        return self._ent.create(entity, data, user_id=user_id, **kw)

    def update(self, entity: str, user_id: str, item_id: str, data: Dict[str, Any], **kw) -> Dict[str, Any]:
        return self._ent.update(entity, item_id, data, user_id=user_id, **kw)

    def upsert(self, entity: str, user_id: str, item_id: str, data: Dict[str, Any], **kw) -> Dict[str, Any]:
        return self._ent.upsert(entity, item_id, data, user_id=user_id, **kw)

    def delete(self, entity: str, user_id: str, item_id: str, **kw):
        return self._ent.delete(entity, item_id, user_id=user_id, **kw)

    def delete_where(self, entity: str, user_id: str, *, params: Optional[Dict] = None, **kw):
        return self._ent.delete_where(entity, user_id=user_id, params=params, **kw)

    def get_raw(self, entity: str, user_id: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get with hidden fields (e.g. api_key plaintext)."""
        return self._ent.get(entity, item_id, user_id=user_id, include_hidden=True)

    def append(self, entity: str, user_id: str, data: Dict[str, Any], **kw) -> Dict[str, Any]:
        return self._ent.append(entity, data, user_id=user_id, **kw)

    def batch_update(self, entity: str, user_id: str, entity_ids: List[str],
                     data: Dict[str, Any], **kw):
        return self._ent.batch_update(entity, entity_ids, data, user_id=user_id, **kw)

    def count(self, entity: str, user_id: str, **kw) -> int:
        return self._ent.count(entity, user_id=user_id, **kw)

    # ── Advanced query methods (used by internal API) ─────────────────────

    def list_stream(
        self, entity: str, user_id: str, *,
        params: Optional[Dict] = None,
        filters: Optional[Dict] = None,
        in_filters: Optional[Dict] = None,
        not_in_filters: Optional[Dict] = None,
        before_id: Optional[str] = None,
        after_id: Optional[str] = None,
        limit: int = 50,
        order_by: str = "timestamp DESC, rowid DESC",
        cursor_field: str = "timestamp",
        skip_default_not_in: bool = False,
    ) -> List[Dict[str, Any]]:
        """Query stream-type entities with cursor pagination."""
        body: Dict[str, Any] = {
            "before_id": before_id,
            "after_id": after_id,
            "limit": limit,
            "filters": filters,
            "in_filters": in_filters,
            "not_in_filters": not_in_filters,
            "order_by": order_by,
            "cursor_field": cursor_field,
            "skip_default_not_in": skip_default_not_in,
        }
        resp = self._ent.query(entity, body, user_id=user_id, params=params)
        return resp.get("data", [])

    def list_advanced(
        self, entity: str, user_id: str, *,
        params: Optional[Dict] = None,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        skip_default_not_in: bool = False,
    ) -> List[Dict[str, Any]]:
        """List with filter/advanced query support."""
        return self._ent.list_advanced(
            entity, user_id=user_id, params=params,
            filters=filters, order_by=order_by, limit=limit,
            skip_default_not_in=skip_default_not_in,
        )

    def cas_update(
        self, entity: str,
        where: Dict[str, Any],
        set_data: Dict[str, Any], **kw,
    ) -> int:
        """Compare-and-swap update (returns affected row count)."""
        return self._ent.cas_update(entity, where, set_data, **kw)

    def get_def(self, entity: str):
        """Return a minimal stub — Business store has no local EntityDef registry."""
        class _Stub:
            name = entity
            sync_type = "list"
        return _Stub()


def get_entity_store() -> BusinessEntityStore:
    global _store
    if _store is None:
        _store = BusinessEntityStore()
    return _store
