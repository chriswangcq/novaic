"""Repository-level guards for the release-controller control plane."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "novaic-release-controller"
CONFIG_SAMPLE = PACKAGE / "config.sample.json"
DOCKERFILE = ROOT / "docker" / "release-controller" / "Dockerfile"
COMPOSE = ROOT / "docker" / "release-controller" / "compose.yaml"
ENV_SAMPLE = ROOT / "docker" / "release-controller" / "env.sample"
DEPLOY = ROOT / "deploy"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
RELEASE_CONTROLLER_DOC = ROOT / "docs" / "architecture" / "release-controller.md"


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
        "python -m pip install pytest",
        "python -m pip install /opt/novaic/release-controller",
        "release_controller.service",
        "DOCKER_CLI_VERSION",
        "DOCKER_COMPOSE_VERSION",
        "docker compose version",
        'CMD ["python", "-m", "release_controller.main"]',
    ]:
        assert marker in text


def test_release_controller_quality_gate_contract_is_documented() -> None:
    config = json.loads(CONFIG_SAMPLE.read_text(encoding="utf-8"))
    gate_names = [gate["name"] for gate in config["quality_gates"]]
    deploy_doc = DEPLOY_DOC.read_text(encoding="utf-8")
    release_controller_doc = RELEASE_CONTROLLER_DOC.read_text(encoding="utf-8")

    assert gate_names == ["release-controller-ci", "release-path-lints"]
    assert config["deploy"]["verify_commands"] == [
        ["bash", "-n", "deploy"],
        ["python3", "-m", "py_compile", "docker/api-backend/write_env.py"],
    ]
    assert "quality_gates" in deploy_doc
    assert "权威 staging 准入" in deploy_doc
    assert "`quality_gates` are the authoritative CI admission checks" in release_controller_doc
    assert "Prod promotion never rebuilds" in release_controller_doc


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
        "NOVAIC_RELEASE_CONTROLLER_SSH_DIR",
        "127.0.0.1:${NOVAIC_RELEASE_CONTROLLER_PORT:-19880}:19880",
    ]:
        assert marker in compose
    assert "server_name" not in compose
    assert "proxy_pass" not in compose
    assert "NOVAIC_RELEASE_CONTROLLER_IMAGE=127.0.0.1:5000/novaic/release-controller:sha-example" in env_sample
    assert "NOVAIC_RELEASE_CONTROLLER_SSH_DIR=/root/.ssh" in env_sample


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
        "NOVAIC_DEPLOY_CALLER",
        "require_release_controller_invocation",
    ]:
        assert marker in deploy

    result = run_command(["./deploy", "release-controller-image", "novaic/release-controller:latest"])
    assert result.returncode != 0
    assert "禁止使用可变 tag" in result.stdout + result.stderr


def test_backend_image_deploys_reject_manual_invocation() -> None:
    image_refs = {
        "services-image": "127.0.0.1:5000/novaic/api-backend:sha-abcdef1",
        "factory-image": "127.0.0.1:5000/novaic/llm-factory:sha-abcdef1",
    }

    for target, image_ref in image_refs.items():
        result = run_command(["./deploy", target, "staging", image_ref])
        output = result.stdout + result.stderr
        assert result.returncode != 0, output
        assert "Release Controller" in output
        assert "人工发布路径" in output


def test_obsolete_backend_deploy_targets_are_disabled() -> None:
    for target in [
        "services",
        "api-backend",
        "services-legacy",
        "gateway",
        "business",
        "device",
        "runtime",
        "cortex",
        "blob-service",
        "sandboxd",
        "entangled",
        "factory",
        "all",
    ]:
        result = run_command(["./deploy", target])
        output = result.stdout + result.stderr
        assert result.returncode != 0, target + "\n" + output
        assert "Release Controller" in output
        assert "手动后端发布路径" in output


def test_release_controller_guard_is_registered() -> None:
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "scripts/ci/test_release_controller_ci.py" in run_all_tests
    assert "python3 -m pytest -q scripts/ci/test_release_controller_ci.py" in workflow
