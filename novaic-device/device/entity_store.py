"""
Device Service Entity Store — thin wrapper over EntangledServiceClient.

Same pattern as BusinessEntityStore. Pure HTTP CRUD against Entangled.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_store: Optional["DeviceEntityStore"] = None


class DeviceEntityStore:
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
             order_by: Optional[str] = None, limit: int = 200, **kw) -> List[Dict[str, Any]]:
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
        return self._ent.get(entity, item_id, user_id=user_id, include_hidden=True)

    def append(self, entity: str, user_id: str, data: Dict[str, Any], **kw) -> Dict[str, Any]:
        return self._ent.append(entity, data, user_id=user_id, **kw)

    def batch_update(self, entity: str, user_id: str, entity_ids: List[str],
                     data: Dict[str, Any], **kw):
        return self._ent.batch_update(entity, entity_ids, data, user_id=user_id, **kw)

    def count(self, entity: str, user_id: str, **kw) -> int:
        return self._ent.count(entity, user_id=user_id, **kw)


def get_entity_store() -> DeviceEntityStore:
    global _store
    if _store is None:
        _store = DeviceEntityStore()
    return _store
