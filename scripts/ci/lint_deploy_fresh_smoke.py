#!/usr/bin/env python3
"""Guard timestamp-aware deploy smoke.

Deploy status used to rely on process checks plus stale log tails. The deploy
restart path must keep a fresh timestamp boundary and verify critical logs were
updated after that boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def require(text: str, needle: str, label: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(f"{label}: missing {needle!r}")


def main() -> int:
    errors: list[str] = []
    deploy = DEPLOY.read_text(encoding="utf-8")
    doc = DEPLOY_DOC.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    deploy_required = [
        "remote_epoch()",
        "fresh_smoke_default_epoch()",
        "verify_fresh_backend_logs()",
        "NOVAIC_DEPLOY_SMOKE_SINCE_EPOCH",
        'smoke_since="$(remote_epoch)"',
        'verify_fresh_backend_logs "$smoke_since"',
        'fresh-smoke)    verify_fresh_backend_logs "${2:-}" ;;',
        "stat -c %Y",
        "queue-service.log",
        "sandboxd.log",
        "novaic-logicalfs",
        'remove_retired_backend_package "novaic-sandbox-core"',
        "sync_backend_infra_bootstrap",
        "runtime_logs",
        "runtime_worker_roster.py",
    ]
    for needle in deploy_required:
        require(deploy, needle, "deploy", errors)

    services_start = deploy.find("deploy_legacy_host_services() {")
    services_end = deploy.find("\ndeploy_services()", services_start)
    services_body = deploy[services_start:services_end] if services_start != -1 and services_end != -1 else ""
    require(
        services_body,
        'disabled_backend_release_path "services-legacy"',
        "deploy_legacy_host_services",
        errors,
    )

    doc_required = [
        "./deploy fresh-smoke [epoch]",
        "timestamp-aware",
        "重启前",
        "旧日志",
    ]
    for needle in doc_required:
        require(doc, needle, "docs/runbooks/deploy.md", errors)

    require(
        workflow,
        "python3 scripts/ci/lint_deploy_fresh_smoke.py",
        ".github/workflows/lint.yml",
        errors,
    )

    if errors:
        print("lint_deploy_fresh_smoke FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_deploy_fresh_smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
