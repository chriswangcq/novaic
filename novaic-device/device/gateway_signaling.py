"""HTTP client for pushing WebRTC signaling events to Gateway's App WS.

Device Service sends ICE candidates and SDP answers through Gateway,
which broadcasts them to the connected App client via WebSocket.
"""

import logging
import httpx
from common.config import ServiceConfig

logger = logging.getLogger(__name__)


async def push_ice_candidate_to_user(
    user_id: str, device_id: str, session_id: str, candidate: dict,
) -> None:
    """Push ICE candidate to App via Gateway's push endpoint."""
    await _push_to_gateway(user_id, "ice_candidate", {
        "device_id": device_id,
        "session_id": session_id,
        "candidate": candidate,
    })


async def push_webrtc_answer_to_user(
    user_id: str, device_id: str, session_id: str, sdp_answer: str,
) -> None:
    """Push WebRTC SDP answer to App via Gateway's push endpoint."""
    await _push_to_gateway(user_id, "webrtc_answer", {
        "device_id": device_id,
        "session_id": session_id,
        "sdp_answer": sdp_answer,
    })


async def _push_to_gateway(user_id: str, event_type: str, payload: dict) -> None:
    """Send a push event to Gateway for WS broadcast to user."""
    url = f"{ServiceConfig.GATEWAY_URL}/api/app/push"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={
                "user_id": user_id,
                "event_type": event_type,
                "payload": payload,
            })
            if resp.status_code != 200:
                logger.warning("[Signaling] Gateway push failed: %d %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("[Signaling] Gateway push error: %s", e)
