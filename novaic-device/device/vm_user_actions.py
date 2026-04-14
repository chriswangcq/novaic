"""
gateway/api/vm_user_actions.py — VM User Entity Actions.

Migrated from _dispatch_vm_user_restart in app_client.py.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def restart_vnc_action(store, user_id: str, params: Dict[str, str], payload: Dict[str, Any]) -> dict:
    """
    vm-users.restart_vnc — Restart VNC desktop for a VM user.

    Payload:
        device_id: str (required)
        username:  str (required)
    """
    from device.entity_store import get_entity_store
    from device.pc_client import get_pc_client_manager

    device_id = payload.get("device_id") or params.get("device_id")
    username = payload.get("username")
    if not device_id or not username:
        raise ValueError("device_id and username are required")

    s = get_entity_store()
    device_row = s.get("devices", user_id, device_id)
    if not device_row:
        raise ValueError(f"Device {device_id} not found")
    if device_row.get("status") != "running":
        raise ValueError(f"Device must be running (status: {device_row.get('status')})")

    # 通过 EntityStore list + filters 查 vm_users，不再裸 SQL
    vm_users = s.list(
        "vm-users", user_id,
        params={"device_id": device_id},
        filters={"username": username},
    )
    if not vm_users:
        raise ValueError(f"VM user '{username}' not found")

    display_num = vm_users[0].get("display_num")
    pc_client_id = device_row.get("pc_client_id") or None
    mgr = get_pc_client_manager(user_id=user_id, pc_client_id=pc_client_id)
    await mgr.restart_vm_user_vnc(device_id, username, display_num=display_num)
    return {"success": True}
