from pathlib import Path
import time

from fastapi.testclient import TestClient

from release_controller import create_app
from release_controller.models import (
    CommandPlan,
    CommandResult,
    ControllerConfig,
    ImageRefs,
    ReleasePointer,
)
from release_controller.poller import BranchHead, InMemoryBranchHeadProvider
from release_controller.runner import PlanExecutionResult
from release_controller.state import ReleaseStateStore


def test_health_and_rules(tmp_path: Path) -> None:
    client = _client(tmp_path)

    assert client.get("/health").json() == {"status": "healthy"}
    rules = client.get("/v1/rules").json()["rules"]
    assert rules[0]["pattern"] == "main"
    assert rules[0]["namespace"] == "staging"


def test_trigger_dry_run_persists_run_without_release_pointer(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    client = _client(tmp_path, state=state)

    response = client.post(
        "/v1/triggers",
        json={"branch": "main", "commit": "abcdef1234567890", "dry_run": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["namespace"] == "staging"
    assert body["execution"]["succeeded"] is True
    assert all(result["skipped"] for result in body["execution"]["results"])
    assert state.get_current_release("staging") is None
    assert len(client.get("/v1/runs").json()["runs"]) == 1


def test_trigger_without_dry_run_executes_and_updates_release_pointer(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    client = _client(tmp_path, state=state, runner=_SuccessfulRunner())

    response = client.post(
        "/v1/triggers",
        json={"branch": "main", "commit": "abcdef1234567890"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["execution"]["dry_run"] is False
    assert body["execution"]["succeeded"] is True
    assert state.get_current_release("staging").commit == "abcdef1234567890"


def test_run_lookup_404(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/v1/runs/missing")

    assert response.status_code == 404


def test_prod_promotion_rejects_mutable_ref(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/v1/promotions/prod",
        json={
            "api_image": "repo/api:latest",
            "factory_image": "repo/factory:sha-abcdef1",
            "commit": "abcdef1234567890",
            "dry_run": True,
        },
    )

    assert response.status_code == 400
    assert "immutable" in response.json()["detail"]


def test_rollback_missing_previous_returns_400(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post("/v1/rollbacks/staging", json={"dry_run": True})

    assert response.status_code == 400
    assert "no previous" in response.json()["detail"]


def test_poll_once_uses_branch_poller(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    client = _client(
        tmp_path,
        state=state,
        branch_heads=(BranchHead("main", "abcdef1234567890"),),
    )

    response = client.post("/v1/polls/once", json={"dry_run": True})

    assert response.status_code == 200
    body = response.json()
    assert body["outcomes"][0]["status"] == "planned"
    assert body["outcomes"][0]["branch"] == "main"
    assert state.read_branch_heads() == {"main": "abcdef1234567890"}


def test_status_reports_release_pointers_and_candidates(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    state.write_branch_head("main", "abcdef1")
    state.update_namespace_release(_pointer("run-1", "abcdef1"))
    state.update_namespace_release(_pointer("run-2", "abcdef2"))
    state.put_candidate("release-abcdef3", _pointer("run-3", "abcdef3"))
    client = _client(tmp_path, state=state)

    body = client.get("/v1/status").json()

    assert body["branch_heads"] == {"main": "abcdef1"}
    assert body["current_releases"][0]["run_id"] == "run-2"
    assert body["previous_releases"][0]["run_id"] == "run-1"
    assert body["candidates"][0]["run_id"] == "run-3"
    assert body["polling"]["enabled"] is False
    assert body["polling"]["running"] is False


def test_autonomous_polling_loop_runs_when_enabled(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    config = _config(tmp_path, polling_enabled=True)
    app = create_app(
        config,
        state=state,
        runner=_SuccessfulRunner(),
        branch_head_provider=InMemoryBranchHeadProvider(
            (BranchHead("main", "abcdef1234567890"),)
        ),
    )

    with TestClient(app) as client:
        polling = _wait_for_polling_iteration(client)

    assert polling["enabled"] is True
    assert polling["iteration_count"] >= 1
    assert polling["last_error"] is None
    assert polling["last_outcomes"][0]["status"] == "planned"
    assert state.read_branch_heads() == {"main": "abcdef1234567890"}


def test_autonomous_polling_loop_stays_idle_when_disabled(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    app = create_app(
        _config(tmp_path, polling_enabled=False),
        state=state,
        branch_head_provider=InMemoryBranchHeadProvider(
            (BranchHead("main", "abcdef1234567890"),)
        ),
    )

    with TestClient(app) as client:
        time.sleep(0.05)
        polling = client.get("/v1/status").json()["polling"]

    assert polling["enabled"] is False
    assert polling["running"] is False
    assert polling["iteration_count"] == 0
    assert state.read_branch_heads() == {}


def _client(
    tmp_path: Path,
    state: ReleaseStateStore | None = None,
    branch_heads: tuple[BranchHead, ...] = (),
    runner: object | None = None,
) -> TestClient:
    config = _config(tmp_path)
    store = state or ReleaseStateStore(tmp_path / "state")
    return TestClient(
        create_app(
            config,
            state=store,
            runner=runner,
            branch_head_provider=InMemoryBranchHeadProvider(branch_heads),
        )
    )


def _config(tmp_path: Path, polling_enabled: bool = False) -> ControllerConfig:
    return ControllerConfig.from_mapping(
        {
            "state_dir": str(tmp_path / "state"),
            "repo": {"path": str(tmp_path / "worktree")},
            "registry": {
                "api_image": "127.0.0.1:5000/novaic/api-backend",
                "factory_image": "127.0.0.1:5000/novaic/llm-factory",
            },
            "deploy": {
                "script_path": "./deploy",
                "verify_commands": [["./scripts/run_all_tests.sh"]],
                "health_urls": {"staging": "https://staging-api.gradievo.com/api/health"},
            },
            "branch_rules": [
                {"pattern": "main", "mode": "auto_deploy", "namespace": "staging"},
                {
                    "pattern": "preview/*",
                    "mode": "auto_deploy",
                    "namespace_template": "preview-{slug}",
                },
                {"pattern": "release/*", "mode": "candidate_only"},
            ],
            "poll_interval_seconds": 1,
            "polling_enabled": polling_enabled,
        }
    )


class _SuccessfulRunner:
    def run(self, plan: CommandPlan) -> PlanExecutionResult:
        return PlanExecutionResult(
            dry_run=plan.dry_run,
            results=(
                CommandResult(
                    name="test-runner",
                    argv=("true",),
                    exit_code=0,
                    stdout="executed by test runner",
                    skipped=plan.dry_run,
                ),
            ),
        )


def _wait_for_polling_iteration(client: TestClient) -> dict:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        polling = client.get("/v1/status").json()["polling"]
        if polling["iteration_count"] >= 1:
            return polling
        time.sleep(0.02)
    raise AssertionError("polling loop did not run")


def _pointer(run_id: str, commit: str) -> ReleasePointer:
    return ReleasePointer(
        namespace="staging",
        commit=commit,
        images=ImageRefs(
            api_image=f"repo/api:sha-{commit}",
            factory_image=f"repo/factory:sha-{commit}",
        ),
        run_id=run_id,
        updated_at="2026-05-24T12:00:00+08:00",
    )
