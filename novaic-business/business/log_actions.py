"""
business/log_actions.py — Execution log entity action handlers.

Migrated from gateway/api/log_actions.py.
Actions: clear_logs (execution-logs.clear), get_input (log-payloads.get_input)
"""

import json
import logging
from typing import Any, Dict

from business.auth import check_agent_access

logger = logging.getLogger(__name__)


def clear_logs_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """execution-logs.clear — Delete all execution logs and payloads for an agent."""
    agent_id = payload.get("agent_id") or params.get("agent_id")
    if not agent_id:
        raise ValueError("agent_id is required")

    check_agent_access(agent_id, user_id)

    payloads_deleted = store.delete_where(
        "log-payloads", "",
        params={"agent_id": agent_id},
    )

    logs_deleted = store.delete_where(
        "execution-logs", "",
        params={"agent_id": agent_id},
    )

    logger.info("[clear_logs] agent=%s deleted %d logs, %d payloads", agent_id, logs_deleted, payloads_deleted)
    return {"deleted": logs_deleted}


def get_input_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """log-payloads.get_input — Fetch the full input payload for a single log entry."""
    agent_id = payload.get("agent_id") or params.get("agent_id")
    log_id = payload.get("log_id") or params.get("log_id")
    if not agent_id or not log_id:
        raise ValueError("agent_id and log_id are required")

    check_agent_access(agent_id, user_id)

    row = store.get(
        "log-payloads", "",
        str(log_id),
        params={"agent_id": agent_id},
    )

    if not row:
        return {"input": None}

    input_val = row.get("input")
    if isinstance(input_val, str):
        try:
            input_val = json.loads(input_val)
        except json.JSONDecodeError:
            pass

    return {"input": input_val}
