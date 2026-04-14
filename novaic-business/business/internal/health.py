"""
Internal API module: health

Minimal stubs — Business Service does not own WS push or message queues.
"""

from fastapi import APIRouter

router = APIRouter(tags=["internal"])

# ==================== Health Monitor Operations ====================

@router.get("/health/app-ws-push")
def get_app_ws_push_stats():
    """App WS notifier push queue stats stub.

    Business Service has no local WS notifier; returns empty stats.
    """
    return {
        "queue_depth": 0,
        "total_pushed": 0,
        "total_failed": 0,
    }


@router.get("/health/stuck-sending")
def get_stuck_sending_count(timeout_seconds: int = None):
    """Get count of messages stuck in 'sending' state.

    With Entangled as the message store, messages are written as 'sent'
    directly; the 'sending' queue pattern is legacy. Returns 0.
    """
    return {"count": 0}
