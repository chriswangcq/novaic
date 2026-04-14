"""
NovAIC Device Service — Device/VM management, PC bridge WebSocket, VmControl proxy.

Handles: devices, vm-users entity actions, PC bridge WS, VM lifecycle, VNC proxy
Port: 19993

All device logic uses device-internal modules.
Gateway imports eliminated — only common.* and entangled.sql.* used externally.
"""

import os
import sys
import logging
from datetime import datetime

_cli_args = None
if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser(description="NovAIC Device Service")
    _parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    _parser.add_argument("--port", type=int, default=19993, help="Port to listen")
    _parser.add_argument("--data-dir", required=True, help="Data directory")
    _parser.add_argument("--entangled-url", required=True, help="Entangled Service URL")
    _parser.add_argument("--gateway-url", default="http://127.0.0.1:19999", help="Gateway URL")
    _parser.add_argument("--resource-dir", default="", help="Resource directory (for bundled QEMU, etc.)")
    _cli_args = _parser.parse_args()

from common.config import ServiceConfig

if _cli_args:
    ServiceConfig.DATA_DIR = _cli_args.data_dir
    ServiceConfig.DEVICE_HOST = _cli_args.host
    ServiceConfig.DEVICE_PORT = _cli_args.port
    ServiceConfig.DEVICE_URL = f"http://{_cli_args.host}:{_cli_args.port}"
    ServiceConfig.GATEWAY_URL = _cli_args.gateway_url
    from common.entangled_url import host_port_from_http_url

    _eu = _cli_args.entangled_url.strip().rstrip("/")
    ServiceConfig.ENTANGLED_URL = _eu
    ServiceConfig.ENTANGLED_SERVICE_URL = _eu
    _eh, _ep = host_port_from_http_url(_eu)
    ServiceConfig.ENTANGLED_HOST = _eh
    ServiceConfig.ENTANGLED_PORT = _ep
    if _cli_args.resource_dir:
        ServiceConfig.RESOURCE_DIR = _cli_args.resource_dir

NOVAIC_DATA_DIR = ServiceConfig.DATA_DIR
if not NOVAIC_DATA_DIR:
    sys.exit(1)

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(NOVAIC_DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"device-{datetime.utcnow().strftime('%Y%m%d')}.log")
_log_file_handle = open(LOG_FILE, "a", encoding="utf-8", buffering=1)


class _LogFileOnlyStream:
    def __init__(self, file):
        self.file = file
    def write(self, data):
        if data:
            self.file.write(data)
            self.file.flush()
    def flush(self):
        self.file.flush()
    def isatty(self):
        return False
    def fileno(self):
        return self.file.fileno()


sys.stdout = _LogFileOnlyStream(_log_file_handle)
sys.stderr = _LogFileOnlyStream(_log_file_handle)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("device")

# ── sys.path ─────────────────────────────────────────────────────────────────
from pathlib import Path

_device_path = str(Path(__file__).parent)
if _device_path not in sys.path:
    sys.path.insert(0, _device_path)

_entangled_lib_path = str(Path(__file__).parent.parent / "Entangled" / "packages" / "server-python")
if _entangled_lib_path not in sys.path:
    sys.path.insert(0, _entangled_lib_path)

# ── FastAPI App ──────────────────────────────────────────────────────────────
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    import time
    t0 = time.perf_counter()
    logger.info("Device Service starting on http://%s:%s",
                getattr(ServiceConfig, "DEVICE_HOST", "127.0.0.1"),
                getattr(ServiceConfig, "DEVICE_PORT", 19993))

    from device.db_access import init_database
    init_database(data_dir=NOVAIC_DATA_DIR, db_file="device.db")
    logger.info("Device DB initialized (vm_processes/ssh_keys)")

    # Recover VM processes from previous session
    from device.vm import get_vm_manager
    vm_manager = get_vm_manager()
    vm_manager.recover_processes()
    logger.info("VM process recovery complete")

    logger.info("Ready (startup %.2fs)", time.perf_counter() - t0)
    yield

    # Graceful shutdown: stop all VMs
    try:
        from device.vm import get_vm_manager
        vm_manager = get_vm_manager()
        await vm_manager.stop_all()
        logger.info("All VMs stopped")
    except Exception as e:
        logger.warning("Failed to stop VMs: %s", e)

    from device.db_access import close_database
    close_database()
    logger.info("Device Service shutting down")


app = FastAPI(
    title="NovAIC Device Service",
    description="Device/VM management, PC bridge, VmControl proxy",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "device", "version": "0.1.0"}


# ── Routes ───────────────────────────────────────────────────────────────────

from device.pc_client import router as pc_client_router
from device.vm_routes import router as vm_router
from device.vmcontrol_routes import router as vmcontrol_router
from device.internal_vm_routes import router as internal_vm_router
from device.gateway_facing_api import router as gateway_facing_router

# PC bridge WebSocket: /internal/pc/ws
app.include_router(pc_client_router, prefix="/internal")

# VM REST API: /api/vm/*
app.include_router(vm_router)

# VmControl proxy + VNC: /api/vmcontrol/*
app.include_router(vmcontrol_router)

# Internal VM routes (SSH keys, VM tools discovery): /internal/vm/*
app.include_router(internal_vm_router, prefix="/internal")

# Gateway-facing API (device registry, binding resolution, QEMU, vmcontrol health)
app.include_router(gateway_facing_router, prefix="/internal")


# ── Entity Action Dispatcher ─────────────────────────────────────────────────

DEVICE_ACTIONS = {}


def _load_actions():
    from device.device_actions import (
        setup_action, start_action, stop_action,
        vm_start_action, vm_stop_action,
        android_start_action, android_stop_action,
        webrtc_stop_action, grouped_action,
        get_status_action, get_subjects_action,
        get_tool_capabilities_action, android_status_action,
    )
    from device.vm_user_actions import restart_vnc_action

    DEVICE_ACTIONS["devices"] = {
        "grouped": grouped_action,
        "setup": setup_action,
        "start": start_action,
        "stop": stop_action,
        "vm_start": vm_start_action,
        "vm_stop": vm_stop_action,
        "android_start": android_start_action,
        "android_stop": android_stop_action,
        "webrtc_stop": webrtc_stop_action,
        "get_status": get_status_action,
        "get_subjects": get_subjects_action,
        "get_tool_capabilities": get_tool_capabilities_action,
        "android_status": android_status_action,
    }
    DEVICE_ACTIONS["vm-users"] = {
        "restart_vnc": restart_vnc_action,
    }


_load_actions()


@app.post("/internal/entities/{entity}/action/{action_name}")
async def entity_action(entity: str, action_name: str, request: Request):
    """Entity action hook callback — dispatches to registered handler."""
    body = await request.json()
    user_id = body.get("user_id", "")
    params = body.get("params") or {}
    payload = body.get("payload") or {}

    actions = DEVICE_ACTIONS.get(entity)
    if not actions:
        raise HTTPException(status_code=404, detail=f"No actions for entity '{entity}'")
    handler = actions.get(action_name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"No action '{action_name}' on '{entity}'")

    try:
        from device.entity_store import get_entity_store
        store = get_entity_store()
        result = handler(store, user_id, params, payload)
        if asyncio.iscoroutine(result):
            result = await result
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("[Action] %s.%s failed: %s", entity, action_name, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Agent VM/Mobile/HD Proxy Routes ─────────────────────────────────────────
# These routes are called by Cortex/Tools for device operations on agents.
# Extracted from gateway/api/internal/agent.py

from device.agent_vm_proxy import router as agent_vm_proxy_router
app.include_router(agent_vm_proxy_router, prefix="/internal")

import asyncio

# ── Main ─────────────────────────────────────────────────────────────────────

HOST = getattr(ServiceConfig, "DEVICE_HOST", "127.0.0.1")
PORT = getattr(ServiceConfig, "DEVICE_PORT", 19993)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        timeout_keep_alive=30,
        ws_ping_interval=20,
        ws_ping_timeout=20,
    )
