#!/usr/bin/env python3
"""Guard the nginx-excepted host-infra Docker Compose deployment path."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy"
RUN_ALL_TESTS = ROOT / "scripts" / "run_all_tests.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
API_BACKEND_README = ROOT / "docker" / "api-backend" / "README.md"
HOST_INFRA_DIR = ROOT / "docker" / "host-infra"
COMPOSE = HOST_INFRA_DIR / "compose.yaml"
README = HOST_INFRA_DIR / "README.md"
TURN_EXAMPLE = HOST_INFRA_DIR / "turnserver.conf.example"

REQUIRED_FILES = [
    "docker/host-infra/compose.yaml",
    "docker/host-infra/Dockerfile.quic",
    "docker/host-infra/env.example",
    "docker/host-infra/turnserver.conf.example",
    "docker/host-infra/README.md",
]

EXPECTED_SERVICES = {"redis", "coturn", "quic-relay"}


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"host-infra package file missing: {rel}")

    deploy = DEPLOY.read_text(encoding="utf-8")
    run_all_tests = RUN_ALL_TESTS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    deploy_doc = DEPLOY_DOC.read_text(encoding="utf-8")
    api_readme = API_BACKEND_README.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    turn_example = TURN_EXAMPLE.read_text(encoding="utf-8")

    services = compose_service_names(compose)
    if services != EXPECTED_SERVICES:
        errors.append(f"host-infra compose services drifted: expected {sorted(EXPECTED_SERVICES)}, got {sorted(services)}")

    required_compose_markers = [
        "redis:7-alpine",
        "coturn/coturn:4.6.3",
        "novaic/quic-service:local",
        "network_mode: host",
        "/opt/novaic/host-infra/redis:/data",
        "/opt/novaic/host-infra/coturn/turnserver.conf:/etc/coturn/turnserver.conf:ro",
        "/etc/letsencrypt:/etc/letsencrypt:ro",
        "NOVAIC_QUIC_DISABLE_STUN",
    ]
    require_markers(compose, required_compose_markers, "docker/host-infra/compose.yaml", errors)

    if "REPLACE_ON_HOST" not in turn_example:
        errors.append("turnserver.conf.example must use REPLACE_ON_HOST placeholder")
    secret_match = re.search(r"^static-auth-secret=(?!REPLACE_ON_HOST).+", turn_example, re.M)
    if secret_match:
        errors.append("turnserver.conf.example appears to contain a real static-auth-secret")

    required_deploy_markers = [
        'HOST_INFRA_COMPOSE_DIR="/opt/novaic/docker/host-infra"',
        'HOST_INFRA_ENV_FILE="/opt/novaic/docker/host-infra.env"',
        "deploy_host_infra()",
        "ensure_host_infra_running",
        "stop_host_bare_infra_services",
        "verify_host_infra",
        "cleanup_host_bare_infra_residue",
        "host-infra)     deploy_host_infra ;;",
        "deploy_services()",
        "ensure_host_infra_running",
    ]
    require_markers(deploy, required_deploy_markers, "deploy", errors)

    for marker in [
        "host-infra",
        "Redis/coturn/QUIC Docker",
        "nginx 保留 host",
        "清理 host 残留",
        "/opt/novaic/docker/host-infra",
    ]:
        if marker not in deploy_doc:
            errors.append(f"docs/runbooks/deploy.md missing {marker!r}")

    for marker in [
        "Host infra",
        "Redis",
        "coturn",
        "novaic-quic-service",
        "nginx intentionally remains host-managed",
    ]:
        if marker not in readme:
            errors.append(f"docker/host-infra/README.md missing {marker!r}")

    for marker in [
        "Host infra Docker",
        "Redis",
        "coturn",
        "QUIC",
    ]:
        if marker not in api_readme:
            errors.append(f"docker/api-backend/README.md missing {marker!r}")

    if "scripts/ci/lint_host_infra_compose_path.py" not in run_all_tests:
        errors.append("scripts/run_all_tests.sh missing host-infra guard")
    if "python3 scripts/ci/lint_host_infra_compose_path.py" not in workflow:
        errors.append(".github/workflows/lint.yml missing host-infra guard")

    if errors:
        print("lint_host_infra_compose_path FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_host_infra_compose_path OK")
    return 0


def require_markers(text: str, markers: list[str], label: str, errors: list[str]) -> None:
    for marker in markers:
        if marker not in text:
            errors.append(f"{label} missing {marker!r}")


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


if __name__ == "__main__":
    raise SystemExit(main())
