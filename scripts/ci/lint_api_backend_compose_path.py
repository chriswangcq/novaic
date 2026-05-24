#!/usr/bin/env python3
"""Guard the API backend Docker Compose deployment path."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy"
START_SH = ROOT / "scripts" / "start.sh"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"
COMPOSE = ROOT / "docker" / "api-backend" / "compose.yaml"

EXPECTED_SERVICES = {
    "entangled",
    "queue-service",
    "service-registry",
    "blob-service",
    "sandboxd",
    "gateway",
    "business",
    "device",
    "cortex",
    "task-worker-control-1",
    "task-worker-control-2",
    "task-worker-execution-1",
    "task-worker-execution-2",
    "saga-worker-1",
    "saga-worker-2",
    "session-outbox-worker",
    "saga-outbox-worker",
    "runtime-health",
    "runtime-scheduler",
    "subscriber",
}

RETIRED_COMPOSE_TEXT = [
    "--db-backend",
    "operational-sqlite",
    "operational-store",
    "aiosqlite",
    "sqlite",
]

REQUIRED_PACKAGE_FILES = [
    "docker/api-backend/Dockerfile",
    "docker/api-backend/README.md",
    "docker/api-backend/compose.yaml",
    "docker/api-backend/env.example",
    "docker/api-backend/requirements.txt",
    "docker/api-backend/write_env.py",
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def require_text(text: str, needle: str, label: str, errors: list[str]) -> None:
    require(needle in text, f"{label}: missing {needle!r}", errors)


def function_body(text: str, name: str, errors: list[str]) -> str:
    match = re.search(rf"^{re.escape(name)}\(\) \{{\n(?P<body>.*?)^\}}\n", text, re.M | re.S)
    if not match:
        errors.append(f"deploy: missing function {name}()")
        return ""
    return match.group("body")


def compose_service_names(text: str) -> set[str]:
    names: set[str] = set()
    in_services = False
    for line in text.splitlines():
        if line == "services:":
            in_services = True
            continue
        if not in_services:
            continue
        if line and not line.startswith(" "):
            break
        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if match:
            names.add(match.group(1))
    return names


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_PACKAGE_FILES:
        require((ROOT / rel).exists(), f"compose package file missing: {rel}", errors)

    deploy = DEPLOY.read_text(encoding="utf-8")
    start = START_SH.read_text(encoding="utf-8")
    doc = DEPLOY_DOC.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")

    require_text(deploy, "API_BACKEND_COMPOSE_DIR=\"/opt/novaic/docker/api-backend\"", "deploy", errors)
    require_text(deploy, "deploy_api_backend_compose()", "deploy", errors)
    require_text(deploy, "deploy_legacy_host_services()", "deploy", errors)
    require_text(deploy, "api-backend)    deploy_services ;;", "deploy", errors)
    require_text(deploy, "services)       deploy_services ;;", "deploy", errors)
    require_text(deploy, "services-legacy) deploy_legacy_host_services ;;", "deploy", errors)

    services_body = function_body(deploy, "deploy_services", errors)
    require_text(services_body, "disabled_backend_release_path \"services\"", "deploy_services", errors)
    for stale in ["restart_all", "sync_start_sh", "deploy_legacy_host_services", "deploy_api_backend_compose"]:
        require(stale not in services_body, f"deploy_services must not call {stale}", errors)

    compose_body = function_body(deploy, "deploy_api_backend_compose", errors)
    require_text(compose_body, "disabled_backend_release_path \"services/api-backend\"", "deploy_api_backend_compose", errors)
    for stale in [
        "sync_api_backend_compose",
        "sync_api_backend_build_context",
        "build_api_backend_image",
        "write_api_backend_env",
        "validate_api_backend_compose",
        "stop_legacy_host_backends",
        "up -d --remove-orphans",
        "sync_start_sh",
        "restart_all",
    ]:
        require(stale not in compose_body, f"deploy_api_backend_compose must not call {stale}", errors)

    legacy_body = function_body(deploy, "deploy_legacy_host_services", errors)
    require_text(legacy_body, "disabled_backend_release_path \"services-legacy\"", "deploy_legacy_host_services", errors)
    for stale in ["sync_start_sh", "restart_all", "rsync_service"]:
        require(stale not in legacy_body, f"deploy_legacy_host_services must not call {stale}", errors)

    actual_services = compose_service_names(compose)
    missing_services = sorted(EXPECTED_SERVICES - actual_services)
    extra_services = sorted(actual_services - EXPECTED_SERVICES)
    if missing_services:
        errors.append(f"compose missing services: {missing_services}")
    if extra_services:
        errors.append(f"compose has unexpected services: {extra_services}")

    lower_compose = compose.lower()
    for needle in RETIRED_COMPOSE_TEXT:
        require(needle not in lower_compose, f"compose contains retired text {needle!r}", errors)

    require_text(start, "Legacy rollback only", "scripts/start.sh", errors)
    require_text(doc, "Release Controller 是后端和 LLM Factory 的唯一发布入口", "docs/runbooks/deploy.md", errors)
    require_text(doc, "已关闭的后端手动路径", "docs/runbooks/deploy.md", errors)
    require_text(doc, "deploy services", "docs/runbooks/deploy.md", errors)
    require_text(doc, "deploy api-backend", "docs/runbooks/deploy.md", errors)

    require_text(run_all_tests, "scripts/ci/lint_api_backend_compose_path.py", "scripts/run_all_tests.sh", errors)
    require_text(workflow, "python3 scripts/ci/lint_api_backend_compose_path.py", ".github/workflows/lint.yml", errors)

    if errors:
        print("lint_api_backend_compose_path FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_api_backend_compose_path OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
