"""Repository-level guards for the release-controller control plane."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "novaic-release-controller"
DOCKERFILE = ROOT / "docker" / "release-controller" / "Dockerfile"
COMPOSE = ROOT / "docker" / "release-controller" / "compose.yaml"
ENV_SAMPLE = ROOT / "docker" / "release-controller" / "env.sample"
DEPLOY = ROOT / "deploy"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def run_command(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(kwargs.pop("env", {}))
    return subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        **kwargs,
    )


def test_release_controller_unit_suite_passes() -> None:
    result = run_command(
        [sys.executable, "-m", "pytest", "novaic-release-controller/tests", "-q"],
        env={"PYTHONPATH": str(PACKAGE)},
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_release_controller_dockerfile_invariants() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")

    for marker in [
        "NOVAIC_RELEASE_CONTROLLER_CONFIG",
        "COPY novaic-release-controller",
        "python -m pip install /opt/novaic/release-controller",
        "release_controller.service",
        'CMD ["python", "-m", "release_controller.main"]',
    ]:
        assert marker in text


def test_release_controller_compose_invariants() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")
    env_sample = ENV_SAMPLE.read_text(encoding="utf-8")

    for marker in [
        "release_controller:",
        "NOVAIC_RELEASE_CONTROLLER_IMAGE",
        "NOVAIC_RELEASE_CONTROLLER_CONFIG_HOST",
        "NOVAIC_RELEASE_CONTROLLER_STATE_DIR",
        "NOVAIC_RELEASES_DIR",
        "NOVAIC_RELEASE_CONTROLLER_WORKTREE",
        "NOVAIC_DOCKER_SOCKET",
        "127.0.0.1:${NOVAIC_RELEASE_CONTROLLER_PORT:-19880}:19880",
    ]:
        assert marker in compose
    assert "server_name" not in compose
    assert "proxy_pass" not in compose
    assert "NOVAIC_RELEASE_CONTROLLER_IMAGE=127.0.0.1:5000/novaic/release-controller:sha-example" in env_sample


def test_release_controller_compose_renders_when_tooling_exists() -> None:
    compose_bin = shutil.which("docker-compose")
    if compose_bin is None:
        return

    result = run_command(
        [
            compose_bin,
            "--env-file",
            "docker/release-controller/env.sample",
            "-f",
            "docker/release-controller/compose.yaml",
            "config",
        ]
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "host_ip: 127.0.0.1" in result.stdout
    assert "release_controller:" in result.stdout


def test_deploy_release_controller_image_guard() -> None:
    deploy = DEPLOY.read_text(encoding="utf-8")

    for marker in [
        "release-controller) base=\"novaic/release-controller\"",
        "deploy_release_controller_image()",
        "release-controller-image <image>",
        "release-controller-image) deploy_release_controller_image \"$2\" ;;",
        "services-image) deploy_services_image \"$2\" \"$3\" ;;",
        "factory-image)  deploy_factory_image \"$2\" \"$3\" ;;",
    ]:
        assert marker in deploy

    result = run_command(["./deploy", "release-controller-image", "novaic/release-controller:latest"])
    assert result.returncode != 0
    assert "禁止使用可变 tag" in result.stdout + result.stderr


def test_release_controller_guard_is_registered() -> None:
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "scripts/ci/test_release_controller_ci.py" in run_all_tests
    assert "python3 -m pytest -q scripts/ci/test_release_controller_ci.py" in workflow
