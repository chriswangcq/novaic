"""Sync version persistence — save/load SyncRegistry versions to SQLite.

Migrated from Gateway's sync_version_persistence.py.
"""

from __future__ import annotations

import logging
from typing import Callable

from entangled.server.sync import SyncRegistry

logger = logging.getLogger(__name__)


def load_all_sync_versions(db, registry: SyncRegistry) -> None:
    """Hydrate SyncRegistry from the entangled_sync_versions table."""
    try:
        rows = db.fetchall("SELECT state_key, version FROM entangled_sync_versions")
        if not rows:
            return
        versions = {r["state_key"]: r["version"] for r in rows}
        registry.hydrate_versions(versions)
        logger.info("[SyncPersistence] Loaded %d version entries", len(versions))
    except Exception as e:
        logger.warning("[SyncPersistence] Failed to load versions: %s", e)


def make_version_bump_handler(db) -> Callable[[str, int], None]:
    """Return a callback for SyncRegistry.on_version_bump that persists to DB."""

    def _on_version_bump(state_key: str, version: int) -> None:
        try:
            with db.transaction("global"):
                db.execute(
                    "INSERT INTO entangled_sync_versions (state_key, version) "
                    "VALUES (?, ?) "
                    "ON CONFLICT(state_key) DO UPDATE SET version = excluded.version",
                    (state_key, version),
                )
        except Exception as e:
            logger.warning("[SyncPersistence] Failed to persist version for %s: %s", state_key, e)

    return _on_version_bump
