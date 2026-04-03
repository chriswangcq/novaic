"""
Context Stack — Memory Store

In-memory scope record storage. Default implementation.
For persistence, host implements MemoryBackend protocol.

Fix #7: Thread-safe via threading.Lock.
"""
from __future__ import annotations

import threading
from typing import Dict, List, Optional

from ..context.types import ScopeRecord, ScopeState


class MemoryScopeStore:
    """In-memory store with keyword search. Good for single-session."""

    def __init__(self, max_records: int = 200):
        self._records: Dict[str, ScopeRecord] = {}
        self._order: List[str] = []
        self._max_records = max_records
        self._lock = threading.Lock()  # Fix #7

    def save(self, record: ScopeRecord) -> None:
        with self._lock:
            if record.id not in self._records:
                self._order.append(record.id)
            self._records[record.id] = record
            while len(self._order) > self._max_records:
                old_id = self._order.pop(0)
                self._records.pop(old_id, None)

    def load(self, scope_id: str) -> Optional[ScopeRecord]:
        with self._lock:
            return self._records.get(scope_id)

    def search(self, query: str, limit: int = 5) -> List[ScopeRecord]:
        from .search import ScopeSearch
        searcher = ScopeSearch()
        with self._lock:
            compacted = [r for r in self._records.values() if r.state == ScopeState.COMPACTED]
        return searcher.search(compacted, query, limit)

    def list_all(self, limit: int = 50) -> List[ScopeRecord]:
        with self._lock:
            compacted = [
                self._records[sid]
                for sid in reversed(self._order)
                if sid in self._records
                and self._records[sid].state == ScopeState.COMPACTED
            ]
            return compacted[:limit]

    def get_recallable_names(self) -> List[str]:
        return [r.name for r in self.list_all() if r.raw_messages]

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._records)

    @property
    def compacted_count(self) -> int:
        with self._lock:
            return sum(1 for r in self._records.values() if r.state == ScopeState.COMPACTED)
