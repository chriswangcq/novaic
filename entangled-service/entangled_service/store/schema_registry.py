"""Dynamic schema registration — receives JSON specs from Gateway at startup."""

from __future__ import annotations

import logging
from typing import List

from .entity_def import EntityDef
from .entity_store import get_entity_store

logger = logging.getLogger(__name__)


def register_entities_from_specs(specs: List[dict]) -> dict:
    """Register entity definitions from JSON specs and ensure schema.

    Called by the POST /v1/schema/register endpoint.
    Returns a summary of what was registered.
    """
    store = get_entity_store()
    registered = []
    errors = []

    for spec in specs:
        name = spec.get("name", "<unknown>")
        try:
            defn = EntityDef.from_spec(spec)
            store.register(defn)
            store.ensure_schema(defn)
            registered.append(name)
            logger.info("[SchemaRegistry] Registered: %s → %s", name, defn.table)
        except Exception as e:
            logger.error("[SchemaRegistry] Failed to register %s: %s", name, e)
            errors.append({"name": name, "error": str(e)})

    return {
        "registered": registered,
        "errors": errors,
        "total": len(registered),
    }
