"""Health check endpoint."""

from fastapi import APIRouter

from ..store.entity_store import get_entity_store

router = APIRouter(tags=["health"])


@router.get("/v1/health")
def health():
    store = get_entity_store()
    return {
        "status": "ok",
        "entities": len(store.entities),
        "entity_names": store.entities,
    }
