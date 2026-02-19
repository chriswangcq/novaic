import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def test_tool_result_service_create_and_get(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVAIC_DATA_DIR", str(tmp_path))

    from tool_result_service import handlers

    handlers._storage = None
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "tool-result-service"}

    app.include_router(handlers.router)
    client = TestClient(app)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json().get("service") == "tool-result-service"

    create_resp = client.post(
        "/api/create",
        json={
            "agent_id": "agent-unit",
            "tool_name": "unit-tool",
            "text": "ok",
            "files_created": [],
            "display_files": [],
        },
    )
    assert create_resp.status_code == 200
    result_id = create_resp.json()["result_id"]

    get_resp = client.get(f"/api/{result_id}")
    assert get_resp.status_code == 200
    normalized = get_resp.json()["normalized"]
    assert set(["text", "files_created", "display_files"]).issubset(set(normalized.keys()))
