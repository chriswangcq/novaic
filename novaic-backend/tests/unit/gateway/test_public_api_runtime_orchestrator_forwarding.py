from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from gateway.api import agents as agents_api
from gateway.api import routes as routes_api


def _agent(agent_id: str, name: str, *, setup_complete: bool = False):
    class _FakeAgent:
        def __init__(self):
            self.id = agent_id
            self.name = name
            self.setup_complete = setup_complete
            self.android = None

        def model_dump(self):
            return {
                "id": agent_id,
                "name": name,
                "created_at": "2026-01-01T00:00:00Z",
                "vm": {
                    "backend": "qemu",
                    "image_path": "",
                    "os_type": "ubuntu",
                    "os_version": "24.04",
                    "memory": "4096",
                    "cpus": 4,
                    "ports": {"ssh": 0, "vmuse": 0},
                },
                "setup_complete": setup_complete,
                "model_id": None,
                "devices": [],
            }

    return _FakeAgent()


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(routes_api.router, prefix="/api")
    app.include_router(agents_api.router)
    return app


def _stub_config_manager():
    class _Cfg:
        default_model = None
        api_keys = []

        def get_api_key_by_id(self, _key_id):
            return None

    return SimpleNamespace(load=lambda: _Cfg())


def test_chat_forwards_to_runtime_orchestrator_messages():
    app = _build_app()
    client = TestClient(app)

    forwarded = {}

    def _forward(method, path, *, params=None, json_body=None):
        forwarded["method"] = method
        forwarded["path"] = path
        forwarded["json"] = json_body
        return {"id": "msg-1", "timestamp": "2026-01-01T00:00:00Z"}

    with (
        patch(
            "gateway.config.agents.get_agent_config_manager",
            return_value=SimpleNamespace(get_agent=lambda _aid: object()),
        ),
        patch("gateway.api.routes.get_config_manager", return_value=_stub_config_manager()),
        patch("gateway.api.routes.forward_to_runtime_orchestrator", side_effect=_forward),
    ):
        resp = client.post(
            "/api/chat",
            json={"agent_id": "agent-1", "message": "hello"},
        )

    assert resp.status_code == 200
    assert forwarded["method"] == "POST"
    assert forwarded["path"] == "/internal/messages"
    assert forwarded["json"]["type"] == "USER_MESSAGE"
    assert forwarded["json"]["agent_id"] == "agent-1"


def test_history_and_interrupt_forward_to_runtime_orchestrator():
    app = _build_app()
    client = TestClient(app)

    calls = []

    def _forward(method, path, *, params=None, json_body=None):
        calls.append((method, path, params, json_body))
        if path == "/internal/chat/history":
            return {"messages": []}
        return {"status": "ok"}

    with patch("gateway.api.routes.forward_to_runtime_orchestrator", side_effect=_forward):
        history_resp = client.get("/api/history", params={"agent_id": "agent-1"})
        interrupt_resp = client.post("/api/interrupt", params={"agent_id": "agent-1"})

    assert history_resp.status_code == 200
    assert interrupt_resp.status_code == 200
    assert calls[0][0] == "GET"
    assert calls[0][1] == "/internal/chat/history"
    assert calls[1][0] == "POST"
    assert calls[1][1] == "/internal/agents/agent-1/interrupt"


def test_create_agent_forwards_subagent_init_and_wake_message():
    app = _build_app()
    client = TestClient(app)

    created = _agent("agent-1", "Agent One")
    manager = SimpleNamespace(create_agent=lambda name: created)

    calls = []

    def _forward(method, path, *, params=None, json_body=None):
        calls.append((method, path, params, json_body))
        if path.endswith("/main"):
            return {"subagent_id": "main-agent-1"}
        return {"id": "wake-1"}

    with (
        patch("gateway.api.agents.get_agent_config_manager", return_value=manager),
        patch("gateway.api.agents.forward_to_runtime_orchestrator", side_effect=_forward),
    ):
        resp = client.post("/api/agents", json={"name": "Agent One"})

    assert resp.status_code == 200
    assert calls[0][0] == "GET"
    assert calls[0][1] == "/internal/subagents/agent-1/main"
    assert calls[1][0] == "POST"
    assert calls[1][1] == "/internal/messages"
    assert calls[1][3]["type"] == "SYSTEM_WAKE"


def test_update_agent_setup_complete_forwards_bootstrap_message():
    app = _build_app()
    client = TestClient(app)

    old_agent = _agent("agent-1", "Agent One", setup_complete=False)
    new_agent = _agent("agent-1", "Agent One", setup_complete=True)
    manager = SimpleNamespace(
        get_agent=lambda _agent_id: old_agent,
        update_agent=lambda _agent_id, **_kwargs: new_agent,
    )

    forwarded = {}

    def _forward(method, path, *, params=None, json_body=None):
        forwarded["method"] = method
        forwarded["path"] = path
        forwarded["json"] = json_body
        return {"id": "bootstrap-1"}

    with (
        patch("gateway.api.agents.get_agent_config_manager", return_value=manager),
        patch("gateway.api.agents.forward_to_runtime_orchestrator", side_effect=_forward),
    ):
        resp = client.patch(
            "/api/agents/agent-1",
            json={"setup_complete": True},
        )

    assert resp.status_code == 200
    assert forwarded["method"] == "POST"
    assert forwarded["path"] == "/internal/messages"
    assert forwarded["json"]["type"] == "SYSTEM_WAKE"
