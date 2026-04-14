"""
NovAIC Business Service — Entity action hooks for non-PC-dependent entities.

Handles: skills, api-keys
Port: 19998

All business logic uses business-internal modules.
Gateway imports eliminated — only common.* and entangled.sql.* used externally.
"""

import os
import sys
import logging
from datetime import datetime

_cli_args = None
if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser(description="NovAIC Business Service")
    _parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    _parser.add_argument("--port", type=int, default=19998, help="Port to listen")
    _parser.add_argument("--data-dir", required=True, help="Data directory")
    _parser.add_argument("--entangled-url", required=True, help="Entangled Service URL")
    _parser.add_argument("--gateway-url", default="http://127.0.0.1:19999", help="Gateway URL (for cross-service calls)")
    _cli_args = _parser.parse_args()

from common.config import ServiceConfig

if _cli_args:
    ServiceConfig.DATA_DIR = _cli_args.data_dir
    ServiceConfig.BUSINESS_HOST = _cli_args.host
    ServiceConfig.BUSINESS_PORT = _cli_args.port
    ServiceConfig.BUSINESS_URL = f"http://{_cli_args.host}:{_cli_args.port}"
    ServiceConfig.GATEWAY_URL = _cli_args.gateway_url
    from common.entangled_url import host_port_from_http_url

    _eu = _cli_args.entangled_url.strip().rstrip("/")
    ServiceConfig.ENTANGLED_URL = _eu
    ServiceConfig.ENTANGLED_SERVICE_URL = _eu
    _eh, _ep = host_port_from_http_url(_eu)
    ServiceConfig.ENTANGLED_HOST = _eh
    ServiceConfig.ENTANGLED_PORT = _ep

NOVAIC_DATA_DIR = ServiceConfig.DATA_DIR
if not NOVAIC_DATA_DIR:
    sys.exit(1)

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(NOVAIC_DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"business-{datetime.utcnow().strftime('%Y%m%d')}.log")
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
logger = logging.getLogger("business")

# ── sys.path ─────────────────────────────────────────────────────────────────
# Business Service is fully independent from novaic-gateway.
# Only novaic-common (common.*) and Entangled library (entangled.sql.*) needed.
from pathlib import Path

_business_path = str(Path(__file__).parent)
if _business_path not in sys.path:
    sys.path.insert(0, _business_path)

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
    logger.info("Business Service starting on http://%s:%s",
                getattr(ServiceConfig, "BUSINESS_HOST", "127.0.0.1"),
                getattr(ServiceConfig, "BUSINESS_PORT", 19998))

    _svc_token = ServiceConfig.JWT_SECRET
    from business.schema_push import push_business_schemas
    push_business_schemas(ServiceConfig.ENTANGLED_URL, service_token=_svc_token)
    logger.info("Business entity schemas pushed to Entangled")

    logger.info("Ready (startup %.2fs)", time.perf_counter() - t0)
    yield
    logger.info("Business Service shutting down")


app = FastAPI(
    title="NovAIC Business Service",
    description="All business logic: entity action hooks + internal API",
    version="0.3.0",
    lifespan=lifespan,
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "business", "version": "0.3.0"}


# ── Internal API (moved from Gateway) ────────────────────────────────────────
from business.internal import router as internal_router

app.include_router(internal_router)


# ── Entity Action Dispatcher ─────────────────────────────────────────────────

BUSINESS_ACTIONS = {}


def _load_actions():
    """Register ALL entity action handlers.

    Business-safe actions are handled locally.
    Device-dependent actions (devices, vm-users) are proxied to the Device Service.
    """
    from business.skill_actions import (
        match_skills_action,
        fork_skill_action,
        get_tool_categories_action,
        get_agent_skills_action,
        set_agent_skills_action,
        get_agent_tools_config_action,
        save_agent_tools_config_action,
    )
    from business.api_key_actions import test_api_key_action
    from business.agent_actions import (
        interrupt_action,
        init_action,
        get_model_action,
        prompts_preview_action,
        available_images_action,
    )
    from business.message_actions import (
        send_action,
        mark_all_read_action,
        clear_action as messages_clear_action,
    )
    from business.log_actions import (
        clear_logs_action,
        get_input_action,
    )
    from business.model_actions import (
        add_custom_model_action,
        refresh_api_key_models_action,
        remove_api_key_model_action,
        toggle_available_model_action,
    )
    from business.form_actions import (
        bootstrap_get_action,
        bootstrap_save_action,
    )
    from business.config_actions import (
        get_config_action,
        cleanup_action,
    )
    from business.gateway_proxy import make_proxy_handler, make_device_proxy_handler

    BUSINESS_ACTIONS["skills"] = {
        "match": match_skills_action,
        "fork": fork_skill_action,
        "get_tool_categories": get_tool_categories_action,
        "get_agent_skills": get_agent_skills_action,
        "set_agent_skills": set_agent_skills_action,
        "get_agent_tools_config": get_agent_tools_config_action,
        "save_agent_tools_config": save_agent_tools_config_action,
    }
    BUSINESS_ACTIONS["api-keys"] = {
        "test": test_api_key_action,
    }
    BUSINESS_ACTIONS["agents"] = {
        "interrupt": interrupt_action,
        "init": init_action,
        "get_model": get_model_action,
        "prompts_preview": prompts_preview_action,
        "available_images": available_images_action,
    }
    BUSINESS_ACTIONS["user-preferences"] = {
        "get_config": get_config_action,
        "cleanup": cleanup_action,
    }
    BUSINESS_ACTIONS["agent-tools"] = {
        "get_bootstrap": bootstrap_get_action,
        "save_bootstrap": bootstrap_save_action,
    }
    BUSINESS_ACTIONS["models"] = {
        "add_custom": add_custom_model_action,
    }
    BUSINESS_ACTIONS["api-key-models"] = {
        "refresh": refresh_api_key_models_action,
        "remove": remove_api_key_model_action,
    }
    BUSINESS_ACTIONS["available-models"] = {
        "toggle": toggle_available_model_action,
    }
    BUSINESS_ACTIONS["messages"] = {
        "send": send_action,
        "mark_all_read": mark_all_read_action,
        "clear": messages_clear_action,
    }
    BUSINESS_ACTIONS["execution-logs"] = {
        "clear": clear_logs_action,
    }
    BUSINESS_ACTIONS["log-payloads"] = {
        "get_input": get_input_action,
    }

    # Device-dependent: devices + vm-users (proxied to Device Service)
    BUSINESS_ACTIONS["devices"] = {
        action: make_device_proxy_handler("devices", action)
        for action in [
            "grouped", "setup", "start", "stop",
            "vm_start", "vm_stop", "android_start", "android_stop",
            "webrtc_stop", "get_status", "get_subjects", "get_tool_capabilities",
            "android_status",
        ]
    }
    BUSINESS_ACTIONS["vm-users"] = {
        "restart_vnc": make_device_proxy_handler("vm-users", "restart_vnc"),
    }


_load_actions()


@app.post("/internal/entities/{entity}/action/{action_name}")
async def entity_action(entity: str, action_name: str, request: Request):
    """Entangled action hook callback — dispatches to registered handler."""
    body = await request.json()
    user_id = body.get("user_id", "")
    params = body.get("params") or {}
    payload = body.get("payload") or {}

    actions = BUSINESS_ACTIONS.get(entity)
    if not actions:
        raise HTTPException(status_code=404, detail=f"No actions for entity '{entity}'")
    handler = actions.get(action_name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"No action '{action_name}' on '{entity}'")

    try:
        from business.entity_store import get_entity_store
        store = get_entity_store()
        result = handler(store, user_id, params, payload)
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("[Action] %s.%s failed: %s", entity, action_name, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Main ─────────────────────────────────────────────────────────────────────

HOST = getattr(ServiceConfig, "BUSINESS_HOST", "127.0.0.1")
PORT = getattr(ServiceConfig, "BUSINESS_PORT", 19998)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
        timeout_keep_alive=30,
    )
