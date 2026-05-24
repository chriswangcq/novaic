from pathlib import Path

from release_controller.models import ControllerConfig, TriggerKind
from release_controller.planner import ReleasePlanner
from release_controller.poller import (
    BranchHead,
    BranchPoller,
    InMemoryBranchHeadProvider,
    parse_ls_remote_heads,
)
from release_controller.runner import CommandRunner
from release_controller.state import ReleaseStateStore


def test_poll_changed_main_creates_poll_run_and_persists_head(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    poller = _poller(tmp_path, state, (BranchHead("main", "abcdef1234567890"),))

    outcomes = poller.poll_once(dry_run=True)

    assert outcomes[0].status == "planned"
    assert state.read_branch_heads() == {"main": "abcdef1234567890"}
    run = state.list_runs()[0]
    assert run.trigger is TriggerKind.POLL
    assert run.namespace == "staging"


def test_poll_unchanged_head_skips_duplicate_run(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    state.write_branch_head("main", "abcdef1234567890")
    poller = _poller(tmp_path, state, (BranchHead("main", "abcdef1234567890"),))

    outcomes = poller.poll_once(dry_run=True)

    assert outcomes[0].status == "skipped"
    assert outcomes[0].reason == "unchanged branch head"
    assert state.list_runs() == ()


def test_poll_release_branch_creates_candidate_run(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    poller = _poller(tmp_path, state, (BranchHead("release/2026.05", "abcdef1234567890"),))

    outcomes = poller.poll_once(dry_run=True)

    assert outcomes[0].status == "planned"
    run = state.list_runs()[0]
    assert run.trigger is TriggerKind.POLL
    assert run.namespace is None


def test_poll_unmatched_branch_skips_without_recording_head(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    poller = _poller(tmp_path, state, (BranchHead("wip/local", "abcdef1234567890"),))

    outcomes = poller.poll_once(dry_run=True)

    assert outcomes[0].status == "skipped"
    assert outcomes[0].reason == "unmatched branch"
    assert state.read_branch_heads() == {}
    assert state.list_runs() == ()


def test_poll_trigger_cannot_resolve_prod(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    poller = _poller(
        tmp_path,
        state,
        (BranchHead("preview/prod", "abcdef1234567890"),),
        preview_template="{slug}",
    )

    outcomes = poller.poll_once(dry_run=True)

    assert outcomes[0].status == "failed"
    assert "prod" in outcomes[0].reason
    assert state.read_branch_heads() == {}


def test_parse_ls_remote_heads() -> None:
    output = (
        "abcdef1234567890\trefs/heads/main\n"
        "bbbbbb1234567890\trefs/heads/preview/pr-1\n"
        "ignored\trefs/tags/v1\n"
    )

    assert parse_ls_remote_heads(output) == (
        BranchHead("main", "abcdef1234567890"),
        BranchHead("preview/pr-1", "bbbbbb1234567890"),
    )


def _poller(
    tmp_path: Path,
    state: ReleaseStateStore,
    heads: tuple[BranchHead, ...],
    preview_template: str = "preview-{slug}",
) -> BranchPoller:
    config = _config(tmp_path, preview_template=preview_template)
    planner = ReleasePlanner(config, state)
    return BranchPoller(
        config=config,
        state=state,
        planner=planner,
        runner=CommandRunner(),
        provider=InMemoryBranchHeadProvider(heads),
    )


def _config(tmp_path: Path, preview_template: str) -> ControllerConfig:
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
                    "namespace_template": preview_template,
                },
                {"pattern": "release/*", "mode": "candidate_only"},
            ],
            "dry_run_default": True,
        }
    )
