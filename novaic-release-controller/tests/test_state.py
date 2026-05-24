from pathlib import Path

from release_controller.models import ImageRefs, ReleasePointer, ReleaseRun, RunStatus, TriggerKind
from release_controller.state import ReleaseStateStore


def test_branch_heads_survive_store_reload(tmp_path: Path) -> None:
    store = ReleaseStateStore(tmp_path)
    store.write_branch_head("main", "abc123")

    reloaded = ReleaseStateStore(tmp_path)

    assert reloaded.read_branch_heads() == {"main": "abc123"}


def test_run_create_update_fetch_and_list(tmp_path: Path) -> None:
    store = ReleaseStateStore(tmp_path)
    run = ReleaseRun(
        run_id="20260524-main-abc123",
        trigger=TriggerKind.MANUAL,
        branch="main",
        commit="abc123",
        namespace="staging",
        status=RunStatus.QUEUED,
    )

    store.put_run(run)
    updated = store.update_run(run.run_id, status=RunStatus.FAILED, failure="verify failed")

    assert updated.status is RunStatus.FAILED
    assert store.get_run(run.run_id).failure == "verify failed"
    assert [item.run_id for item in store.list_runs()] == [run.run_id]


def test_current_previous_pointer_rollover(tmp_path: Path) -> None:
    store = ReleaseStateStore(tmp_path)
    first = _pointer("run-1", "commit-1")
    second = _pointer("run-2", "commit-2")

    store.update_namespace_release(first)
    store.update_namespace_release(second)

    assert store.get_current_release("staging").run_id == "run-2"
    assert store.get_previous_release("staging").run_id == "run-1"


def test_candidate_persistence(tmp_path: Path) -> None:
    store = ReleaseStateStore(tmp_path)
    pointer = _pointer("run-3", "commit-3")

    store.put_candidate("release-20260524", pointer)

    reloaded = ReleaseStateStore(tmp_path)
    assert reloaded.get_candidate("release-20260524").commit == "commit-3"
    assert reloaded.list_candidates()[0].run_id == "run-3"


def test_failed_run_survives_reload(tmp_path: Path) -> None:
    store = ReleaseStateStore(tmp_path)
    run = ReleaseRun(
        run_id="failed-run",
        trigger=TriggerKind.POLL,
        branch="main",
        commit="badcafe",
        namespace="staging",
        status=RunStatus.FAILED,
        failure="docker build failed",
    )

    store.put_run(run)

    assert ReleaseStateStore(tmp_path).get_run("failed-run").failure == "docker build failed"


def _pointer(run_id: str, commit: str) -> ReleasePointer:
    return ReleasePointer(
        namespace="staging",
        commit=commit,
        images=ImageRefs(
            api_image=f"127.0.0.1:5000/novaic/api-backend@sha256:{commit}",
            factory_image=f"127.0.0.1:5000/novaic/llm-factory@sha256:{commit}",
        ),
        run_id=run_id,
        updated_at="2026-05-24T12:00:00+08:00",
    )
