from datetime import datetime, timezone
from pathlib import Path

import pytest

from release_controller.models import (
    ControllerConfig,
    ImageRefs,
    ReleasePointer,
    ReleaseMode,
)
from release_controller.planner import (
    PlanningError,
    ReleasePlanner,
    assert_immutable_image_ref,
    is_immutable_image_ref,
)
from release_controller.runner import CommandRunner
from release_controller.state import ReleaseStateStore


def test_main_maps_to_staging_deploy_plan(tmp_path: Path) -> None:
    planner = _planner(tmp_path)

    planned = planner.plan_branch_release("main", "abcdef1234567890", dry_run=True)

    assert planned.namespace == "staging"
    assert planned.mode is ReleaseMode.AUTO_DEPLOY
    assert [step.name for step in planned.plan.steps[:4]] == [
        "git-fetch",
        "git-checkout",
        "git-submodule-sync",
        "git-submodule-update",
    ]
    assert any(step.argv[1:3] == ("services-image", "staging") for step in planned.plan.steps)
    assert any(step.name == "smoke-staging" for step in planned.plan.steps)


def test_preview_namespace_uses_template_slug(tmp_path: Path) -> None:
    planner = _planner(tmp_path)

    planned = planner.plan_branch_release("preview/PR-123_test", "abcdef1234567890")

    assert planned.namespace == "preview-pr-123-test"


def test_release_branch_is_candidate_only_without_deploy(tmp_path: Path) -> None:
    planner = _planner(tmp_path)

    planned = planner.plan_branch_release("release/2026.05", "abcdef1234567890")

    assert planned.mode is ReleaseMode.CANDIDATE_ONLY
    assert planned.namespace is None
    assert planned.candidate_id == "release-2026-05-abcdef123456"
    assert not any("services-image" in step.argv for step in planned.plan.steps)


def test_branch_trigger_cannot_resolve_prod(tmp_path: Path) -> None:
    config = _config(tmp_path, preview_template="{slug}")
    planner = ReleasePlanner(config, ReleaseStateStore(tmp_path / "state"), clock=_clock)

    with pytest.raises(PlanningError, match="prod"):
        planner.plan_branch_release("preview/prod", "abcdef1234567890")


def test_immutable_image_ref_validation() -> None:
    assert is_immutable_image_ref("repo/api:sha-abcdef1")
    assert is_immutable_image_ref("repo/api@sha256:" + "a" * 64)
    assert not is_immutable_image_ref("repo/api:latest")
    assert not is_immutable_image_ref("repo/api:v1.2.3")
    with pytest.raises(PlanningError):
        assert_immutable_image_ref("repo/api:staging")


def test_prod_promotion_requires_immutable_refs(tmp_path: Path) -> None:
    planner = _planner(tmp_path)

    with pytest.raises(PlanningError, match="immutable"):
        planner.plan_prod_promotion("repo/api:latest", "repo/factory:sha-abcdef1", "abcdef1")

    planned = planner.plan_prod_promotion(
        "repo/api:sha-abcdef1",
        "repo/factory@sha256:" + "b" * 64,
        "abcdef1234567890",
    )

    assert planned.namespace == "prod"
    assert any(step.argv[1:3] == ("services-image", "prod") for step in planned.plan.steps)


def test_rollback_uses_previous_pointer(tmp_path: Path) -> None:
    state = ReleaseStateStore(tmp_path / "state")
    config = _config(tmp_path)
    planner = ReleasePlanner(config, state, clock=_clock)

    with pytest.raises(PlanningError, match="no previous"):
        planner.plan_rollback("staging")

    state.update_namespace_release(_pointer("run-1", "abcdef1"))
    state.update_namespace_release(_pointer("run-2", "abcdef2"))
    planned = planner.plan_rollback("staging")

    assert planned.images.api_image.endswith(":sha-abcdef1")
    assert any(step.argv[1:3] == ("services-image", "staging") for step in planned.plan.steps)


def test_dry_run_runner_does_not_execute_commands() -> None:
    planner = _planner(Path("/tmp/release-controller-test"))
    plan = planner.plan_branch_release("main", "abcdef1234567890", dry_run=True).plan

    result = CommandRunner().run(plan)

    assert result.succeeded
    assert all(item.skipped for item in result.results)
    assert result.results[0].stdout == "dry-run: command not executed"


def test_runner_captures_subprocess_failure() -> None:
    from release_controller.models import CommandPlan, CommandStep

    plan = CommandPlan(
        dry_run=False,
        steps=(
            CommandStep(
                name="fail",
                argv=("python3", "-c", "import sys; print('bad'); sys.exit(7)"),
            ),
            CommandStep(name="not-run", argv=("python3", "-c", "print('no')")),
        ),
    )

    result = CommandRunner().run(plan)

    assert not result.succeeded
    assert result.failure == "fail failed with exit code 7"
    assert result.results[0].stdout == "bad\n"
    assert len(result.results) == 1


def _planner(tmp_path: Path) -> ReleasePlanner:
    return ReleasePlanner(_config(tmp_path), ReleaseStateStore(tmp_path / "state"), clock=_clock)


def _config(tmp_path: Path, preview_template: str = "preview-{slug}") -> ControllerConfig:
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
                "health_urls": {
                    "staging": "https://staging-api.gradievo.com/api/health",
                    "prod": "https://api.gradievo.com/api/health",
                },
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


def _clock() -> datetime:
    return datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc)
