from task_queue.client import GatewayInternalClient


class _FakeResponse:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload
        self.text = "{\"ok\": true}"

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.calls = []

    def request(self, method, url, json=None, params=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "json": json,
                "params": params,
            }
        )
        return _FakeResponse({"ok": True})


def test_internal_paths_use_runtime_orchestrator_url(monkeypatch):
    monkeypatch.setenv("RUNTIME_ORCHESTRATOR_URL", "http://127.0.0.1:19993")
    client = GatewayInternalClient("http://127.0.0.1:19999")
    fake = _FakeSession()
    monkeypatch.setattr(client, "_get_session", lambda: fake)

    client.get_runtime("rt-1")

    assert fake.calls[0]["url"] == "http://127.0.0.1:19993/internal/runtimes/rt-1"


def test_public_paths_still_use_gateway_url(monkeypatch):
    monkeypatch.setenv("RUNTIME_ORCHESTRATOR_URL", "http://127.0.0.1:19993")
    client = GatewayInternalClient("http://127.0.0.1:19999")
    fake = _FakeSession()
    monkeypatch.setattr(client, "_get_session", lambda: fake)

    client.broadcast_log(agent_id="agent-1", log_type="TEST", data={"x": 1})

    assert fake.calls[0]["url"] == "http://127.0.0.1:19999/api/logs/broadcast"


def test_internal_url_falls_back_to_default_ro_when_env_missing(monkeypatch):
    monkeypatch.delenv("RUNTIME_ORCHESTRATOR_URL", raising=False)
    client = GatewayInternalClient("http://127.0.0.1:19999", internal_url="")
    fake = _FakeSession()
    monkeypatch.setattr(client, "_get_session", lambda: fake)

    client.get_runtime("rt-2")

    assert fake.calls[0]["url"] == "http://127.0.0.1:19993/internal/runtimes/rt-2"


def test_agent_memory_path_uses_gateway_url(monkeypatch):
    monkeypatch.setenv("RUNTIME_ORCHESTRATOR_URL", "http://127.0.0.1:19993")
    client = GatewayInternalClient("http://127.0.0.1:19999")
    fake = _FakeSession()
    monkeypatch.setattr(client, "_get_session", lambda: fake)

    client._request("GET", "/internal/agents/agent-1/memory/all")

    assert fake.calls[0]["url"] == "http://127.0.0.1:19999/internal/agents/agent-1/memory/all"


def test_ro_owned_agent_drive_path_uses_runtime_orchestrator_url(monkeypatch):
    monkeypatch.setenv("RUNTIME_ORCHESTRATOR_URL", "http://127.0.0.1:19993")
    client = GatewayInternalClient("http://127.0.0.1:19999")
    fake = _FakeSession()
    monkeypatch.setattr(client, "_get_session", lambda: fake)

    client._request("GET", "/internal/agents/agent-1/drive")

    assert fake.calls[0]["url"] == "http://127.0.0.1:19993/internal/agents/agent-1/drive"
