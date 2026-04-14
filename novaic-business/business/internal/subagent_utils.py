"""
SubAgent utility functions — all operations go through EntityStore (Entangled).

No direct gateway.db SQL. CAS operations use EntityStore.cas_update().
Global queries use EntityStore.list() with filters.
Context operations use Cortex service (subagent_context table is deprecated).
"""

import json
import logging
from typing import List, Dict, Any, Optional

from common.utils.time import utc_now_iso

logger = logging.getLogger(__name__)


def _get_store():
    from business.entity_store import get_entity_store
    return get_entity_store()


# ========================================
# FK Helper — No-op (agents managed by Entangled)
# ========================================

def ensure_agent_stub(db, agent_id: str) -> None:
    """No-op. Agents are managed by Entangled; FK stubs are unnecessary."""
    pass


# ========================================
# Main SubAgent get-or-create
# ========================================

def get_or_create_main_subagent(store, db, agent_id: str) -> Dict[str, Any]:
    """Get or create the main SubAgent for an agent.

    Uses EntityStore for CRUD with fallback for concurrency.
    """
    store = store or _get_store()
    subagent_id = f"main-{agent_id[:8]}"
    existing = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    if existing:
        return existing

    try:
        return store.create("subagents", "", {
            "subagent_id": subagent_id,
            "agent_id": agent_id,
            "type": "main",
            "status": "sleeping",
        })
    except Exception:
        result = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
        if result:
            return result
        raise


# ========================================
# CAS Operations via EntityStore.cas_update
# ========================================

def acquire_summary_lock(db, subagent_id: str, agent_id: str) -> bool:
    """CAS: Atomically set summary_lock 0→1.

    Returns True if lock acquired, False if already held.
    """
    store = _get_store()
    result = store.cas_update(
        "subagents", "",
        where_condition={"subagent_id": subagent_id, "agent_id": agent_id, "summary_lock": 0},
        update_data={"summary_lock": 1, "updated_at": utc_now_iso()},
        params={"agent_id": agent_id},
    )
    return result is not None


def release_summary_lock(db, subagent_id: str, agent_id: str) -> None:
    """Release summary_lock (unconditionally set to 0)."""
    store = _get_store()
    store.update(
        "subagents", "", subagent_id,
        {"summary_lock": 0, "updated_at": utc_now_iso()},
        params={"agent_id": agent_id},
    )


def check_and_clear_need_rest(db, subagent_id: str, agent_id: str) -> bool:
    """CAS: Atomically read need_rest and set to 0.

    Returns True if need_rest was 1 (now cleared), False if was already 0.
    """
    store = _get_store()
    result = store.cas_update(
        "subagents", "",
        where_condition={"subagent_id": subagent_id, "agent_id": agent_id, "need_rest": 1},
        update_data={"need_rest": 0, "updated_at": utc_now_iso()},
        params={"agent_id": agent_id},
    )
    return result is not None


# ========================================
# HRL Operations via EntityStore get + update
# ========================================

def add_to_hrl(db, subagent_id: str, agent_id: str, runtime_id: str) -> bool:
    """Add a runtime to HRL (Hot Runtime List). Idempotent.

    Returns True if added, False if already exists or not found.
    """
    store = _get_store()
    row = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    if not row:
        return False

    current_hrl = row.get("hrl") or []
    if isinstance(current_hrl, str):
        try:
            current_hrl = json.loads(current_hrl)
        except (json.JSONDecodeError, TypeError):
            current_hrl = []

    if runtime_id in current_hrl:
        return False

    current_hrl.append(runtime_id)
    store.update(
        "subagents", "", subagent_id,
        {"hrl": json.dumps(current_hrl), "updated_at": utc_now_iso()},
        params={"agent_id": agent_id},
    )
    return True


def atomic_update_history_and_hrl(
    db,
    subagent_id: str,
    agent_id: str,
    new_history: str,
    remove_runtime_ids: List[str]
) -> bool:
    """Update historical_summary and remove runtimes from HRL.

    Returns True if successful, False if SubAgent not found.
    """
    store = _get_store()
    row = store.get("subagents", "", subagent_id, params={"agent_id": agent_id})
    if not row:
        return False

    current_hrl = row.get("hrl") or []
    if isinstance(current_hrl, str):
        try:
            current_hrl = json.loads(current_hrl)
        except (json.JSONDecodeError, TypeError):
            current_hrl = []

    new_hrl = [r for r in current_hrl if r not in remove_runtime_ids]

    store.update(
        "subagents", "", subagent_id,
        {
            "historical_summary": new_history,
            "hrl": json.dumps(new_hrl),
            "updated_at": utc_now_iso(),
        },
        params={"agent_id": agent_id},
    )
    return True


# ========================================
# Tool Ports — EntityStore list
# ========================================

def list_with_tool_ports(db) -> List[Dict[str, Any]]:
    """List all SubAgents that have tool_ports set. For Tools Server restore."""
    store = _get_store()
    all_subagents = store.list("subagents", "")
    result = []
    for sa in all_subagents:
        tp = sa.get("tool_ports")
        if not tp or tp == "null":
            continue
        if isinstance(tp, str):
            try:
                tp = json.loads(tp)
            except (json.JSONDecodeError, TypeError):
                continue
        if tp:
            result.append({
                "agent_id": sa.get("agent_id"),
                "subagent_id": sa.get("subagent_id"),
                "tool_ports": tp,
            })
    return result


# ========================================
# Wake Timer — EntityStore list + filter
# ========================================

def get_due_for_wake(db) -> List[Dict[str, Any]]:
    """Find sleeping SubAgents whose wake_at has passed."""
    now = utc_now_iso()
    store = _get_store()
    all_subagents = store.list("subagents", "")

    result = []
    for sa in all_subagents:
        if sa.get("status") != "sleeping":
            continue
        wake_at = sa.get("wake_at")
        if not wake_at or wake_at > now:
            continue

        wake_triggers = sa.get("wake_triggers")
        if isinstance(wake_triggers, str):
            try:
                wake_triggers = json.loads(wake_triggers)
            except (json.JSONDecodeError, TypeError):
                wake_triggers = None
        if not wake_triggers:
            wake_triggers = [{"type": "user_response"}]

        result.append({
            "subagent_id": sa.get("subagent_id"),
            "agent_id": sa.get("agent_id"),
            "type": sa.get("type"),
            "parent_subagent_id": sa.get("parent_subagent_id"),
            "status": sa.get("status"),
            "wake_triggers": wake_triggers,
            "handoff_notes": sa.get("handoff_notes"),
            "wake_at": wake_at,
            "task": sa.get("task"),
            "created_at": sa.get("created_at"),
            "updated_at": sa.get("updated_at"),
        })

    result.sort(key=lambda x: x.get("wake_at") or "")
    return result


# ========================================
# SubAgent Context — Cortex handles this; gateway.db subagent_context is deprecated
# ========================================

def context_append(
    db,
    agent_id: str,
    subagent_id: str,
    messages: List[Dict[str, Any]],
    round_id: Optional[str] = None,
) -> int:
    """Append context messages via Cortex.

    Gateway subagent_context table is deprecated; Cortex is the source of truth.
    This function delegates to the Cortex HTTP API.
    """
    if not messages:
        return 0

    import httpx
    from common.config import ServiceConfig
    cortex_url = getattr(ServiceConfig, "CORTEX_URL", "http://127.0.0.1:19996")
    try:
        resp = httpx.post(
            f"{cortex_url}/v1/context/append",
            json={
                "scope_id": f"{agent_id}:{subagent_id}",
                "messages": messages,
                "round_id": round_id,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return len(messages)
    except Exception as e:
        logger.warning("[context_append] Cortex call failed, messages lost: %s", e)
        return 0


def context_get_history(
    db,
    agent_id: str,
    subagent_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get context history from Cortex.

    Gateway subagent_context table is deprecated.
    """
    import httpx
    from common.config import ServiceConfig
    cortex_url = getattr(ServiceConfig, "CORTEX_URL", "http://127.0.0.1:19996")
    try:
        resp = httpx.get(
            f"{cortex_url}/v1/context/history",
            params={
                "scope_id": f"{agent_id}:{subagent_id}",
                "limit": limit,
                "offset": offset,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("messages", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.warning("[context_get_history] Cortex call failed: %s", e)
        return []
