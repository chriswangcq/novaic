"""
Internal Entity API — thin CRUD proxy for Worker→Entangled Service access.

No authentication. Entangled handles notifications (notify=True by default).
Also exposes /entities/{entity}/action/{action} for Entangled action hook callbacks.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from common.entangled_client import EntangledClientError, EntangledServiceClient
from business.entity_store import get_entity_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entities", tags=["internal-entities"])


@router.get("/{entity}")
def internal_list_entities(
    entity: str,
    request: Request,
    id_gt: Optional[str] = None,
    id_lt: Optional[str] = None,
    limit: int = 50,
):
    """List entities (no auth, internal use only)."""
    params = dict(request.query_params)
    params.pop("id_gt", None)
    params.pop("id_lt", None)
    params.pop("limit", None)

    try:
        store = get_entity_store()
        defn = store.get_def(entity)
        with EntangledServiceClient() as client:
            if getattr(defn, "sync_type", "list") == "stream":
                result = client.query(
                    entity,
                    {
                        "after_id": id_gt,
                        "before_id": id_lt,
                        "limit": min(limit, 500),
                    },
                    params=params,
                )
                return {
                    "success": True,
                    "entries": result.get("data", []),
                    "has_more": result.get("has_more", False),
                }

            entries = client.list(
                entity,
                params=params,
                limit=min(limit, 500),
            )
            return {"success": True, "entries": entries}
    except (ValueError, EntangledClientError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{entity}/{item_id}")
def internal_get_entity(
    entity: str,
    item_id: str,
    request: Request,
):
    """Get single entity (no auth, internal use only)."""
    try:
        with EntangledServiceClient() as client:
            data = client.get(
                entity,
                item_id,
                params=dict(request.query_params),
            )
        if not data:
            raise HTTPException(status_code=404, detail=f"{entity} {item_id} not found")
        return {"success": True, "data": data}
    except (ValueError, EntangledClientError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{entity}/{item_id}")
async def internal_update_entity(
    entity: str,
    item_id: str,
    request: Request,
):
    """Update entity (no auth, internal use only)."""
    data = await request.json()
    params = dict(request.query_params)
    try:
        with EntangledServiceClient() as client:
            result = client.update(entity, item_id, data, params=params)
        if not result:
            raise HTTPException(status_code=404, detail="Entity not found")
        return {"success": True, "data": result}
    except (ValueError, EntangledClientError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{entity}")
async def internal_create_entity(
    entity: str,
    request: Request,
):
    """Create entity or append to stream (no auth, internal use only)."""
    data = await request.json()
    params = dict(request.query_params)
    try:
        store = get_entity_store()
        defn = store.get_def(entity)
        with EntangledServiceClient() as client:
            if getattr(defn, "sync_type", "list") == "stream":
                result = client.append(entity, data, params=params)
            else:
                result = client.create(entity, data, params=params)
        return {"success": True, "data": result}
    except (ValueError, EntangledClientError) as e:
        raise HTTPException(status_code=400, detail=str(e))
