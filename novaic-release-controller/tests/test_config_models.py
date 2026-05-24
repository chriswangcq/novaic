from pathlib import Path

import pytest

from release_controller import ConfigError, ReleaseMode, load_config
from release_controller.models import (
    BranchRule,
    CommandPlan,
    CommandStep,
    ControllerConfig,
    QualityGate,
)


def test_load_sample_config() -> None:
    config_path = Path(__file__).parents[1] / "config.sample.json"

    config = load_config(config_path)

    assert config.registry.api_image == "127.0.0.1:5000/novaic/api-backend"
    assert config.branch_rules[0].pattern == "main"
    assert config.branch_rules[0].namespace == "staging"
    assert "novaic-common" in config.repo.submodules
    assert [gate.name for gate in config.quality_gates] == [
        "release-controller-ci",
        "release-path-lints",
    ]
    assert config.polling_enabled is False
    assert set(config.to_mapping()) == {
        "state_dir",
        "repo",
        "registry",
        "deploy",
        "quality_gates",
        "branch_rules",
        "poll_interval_seconds",
        "polling_enabled",
        "server",
    }
    assert config.server.port == 19880


def test_rejects_implicit_repo() -> None:
    data = _base_config()
    data["repo"] = {"remote": "origin"}

    with pytest.raises(ValueError, match="repo.path or repo.url"):
        ControllerConfig.from_mapping(data)


def test_rejects_prod_auto_deploy() -> None:
    with pytest.raises(ValueError, match="prod cannot"):
        BranchRule.from_mapping(
            {
                "pattern": "main",
                "mode": "auto_deploy",
                "namespace": "prod",
            }
        )


def test_rejects_non_boolean_polling_enabled() -> None:
    data = _base_config()
    data["polling_enabled"] = "yes"

    with pytest.raises(ValueError, match="polling_enabled"):
        ControllerConfig.from_mapping(data)


def test_quality_gate_config_round_trip() -> None:
    data = _base_config()
    data["quality_gates"] = [
        {
            "name": "controller-tests",
            "argv": ["python3", "-m", "pytest", "novaic-release-controller/tests", "-q"],
        },
        {
            "name": "repo-guards",
            "argv": ["python3", "-m", "pytest", "-q", "scripts/ci/test_release_controller_ci.py"],
        },
    ]

    config = ControllerConfig.from_mapping(data)

    assert config.quality_gates == (
        QualityGate(
            name="controller-tests",
            argv=("python3", "-m", "pytest", "novaic-release-controller/tests", "-q"),
        ),
        QualityGate(
            name="repo-guards",
            argv=("python3", "-m", "pytest", "-q", "scripts/ci/test_release_controller_ci.py"),
        ),
    )
    assert config.to_mapping()["quality_gates"] == data["quality_gates"]


@pytest.mark.parametrize(
    "gate, match",
    [
        ({}, "name"),
        ({"name": "Controller Tests", "argv": ["true"]}, "lowercase slug"),
        ({"name": "controller-tests", "argv": []}, "argv array must not be empty"),
        ({"name": "controller-tests", "argv": "true"}, "argv array"),
    ],
)
def test_rejects_malformed_quality_gates(gate: dict, match: str) -> None:
    data = _base_config()
    data["quality_gates"] = [gate]

    with pytest.raises(ValueError, match=match):
        ControllerConfig.from_mapping(data)


def test_rejects_duplicate_quality_gate_names() -> None:
    data = _base_config()
    data["quality_gates"] = [
        {"name": "controller-tests", "argv": ["true"]},
        {"name": "controller-tests", "argv": ["true"]},
    ]

    with pytest.raises(ValueError, match="unique"):
        ControllerConfig.from_mapping(data)


def test_invalid_json_config_raises_config_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigError, match="not valid JSON"):
        load_config(config_path)


def test_model_mapping_uses_explicit_enum_values() -> None:
    rule = BranchRule(pattern="main", mode=ReleaseMode.AUTO_DEPLOY, namespace="staging")
    plan = CommandPlan(
        dry_run=True,
        steps=(CommandStep(name="verify", argv=("./scripts/run_all_tests.sh",)),),
    )

    assert rule.to_mapping()["mode"] == "auto_deploy"
    assert plan.to_mapping() == {
        "dry_run": True,
        "steps": [
            {
                "name": "verify",
                "argv": ["./scripts/run_all_tests.sh"],
                "env": {},
                "sensitive": False,
            }
        ],
    }


def _base_config() -> dict:
    return {
        "state_dir": "/tmp/release-controller/state",
        "repo": {"path": "/tmp/worktree", "submodules": ["novaic-common"]},
        "registry": {
            "api_image": "127.0.0.1:5000/novaic/api-backend",
            "factory_image": "127.0.0.1:5000/novaic/llm-factory",
        },
        "deploy": {
            "script_path": "/tmp/worktree/deploy",
            "verify_commands": [["./scripts/run_all_tests.sh"]],
            "health_urls": {"staging": "https://staging-api.gradievo.com/api/health"},
        },
        "branch_rules": [
            {
                "pattern": "main",
                "mode": "auto_deploy",
                "namespace": "staging",
            }
        ],
    }
