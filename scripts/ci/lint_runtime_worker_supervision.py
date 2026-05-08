#!/usr/bin/env python3
"""Guard explicit runtime worker process supervision."""

from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = ROOT / "novaic-agent-runtime"
sys.path.insert(0, str(RUNTIME_ROOT))

from task_queue.workers.runtime_roster import RUNTIME_PROCESS_ROSTER  # noqa: E402

START_SH = ROOT / "scripts" / "start.sh"
DEPLOY = ROOT / "deploy"
DEPLOY_DOC = ROOT / "docs" / "runbooks" / "deploy.md"
WORKFLOW = ROOT / ".github" / "workflows" / "lint.yml"


def require(text: str, needle: str, label: str, errors: list[str]) -> None:
    if needle not in text:
        errors.append(f"{label}: missing {needle!r}")


def main() -> int:
    errors: list[str] = []
    start = START_SH.read_text(encoding="utf-8")
    deploy = DEPLOY.read_text(encoding="utf-8")
    doc = DEPLOY_DOC.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for needle in [
        "process_count()",
        "require_process_count()",
        "verify_runtime_processes()",
        "Required runtime subprocess supervision failed.",
        "verify_runtime_processes",
        "runtime_roster process-checks",
        "runtime_roster launch-commands",
    ]:
        require(start, needle, "scripts/start.sh", errors)

    if not RUNTIME_PROCESS_ROSTER:
        errors.append("runtime roster is empty")

    for stale in [
        'check_role "task-worker control"',
        'check_role "task-worker execution"',
        'check_role "saga-worker"',
        'check_role "session-outbox-worker"',
        'check_role "saga-outbox-worker"',
        'check_role "health"',
        'check_role "scheduler"',
        'check_role "subscriber"',
    ]:
        if stale in start or stale in deploy:
            errors.append(f"runtime roster is duplicated instead of consumed: {stale}")

    for needle in [
        "ROLE                    EXPECTED ACTUAL STATUS",
        "check_role()",
        "runtime_worker_roster.py",
        "process-checks",
        "log-files",
        "coarse worker",
    ]:
        if needle == "coarse worker":
            if "worker_count=$(pgrep -f" in deploy or "Workers: $((worker_count" in deploy:
                errors.append("deploy: still uses coarse worker_count status instead of role table")
            continue
        require(deploy, needle, "deploy", errors)

    for needle in [
        "required runtime subprocesses",
        "role-level",
        "task-worker control",
        "session-outbox-worker",
        "subscriber.log",
        "runtime_roster.py",
    ]:
        require(doc, needle, "docs/runbooks/deploy.md", errors)

    for stale in [
        "for pool in control execution",
        "$PY $MAIN session-outbox-worker",
        "$PY $MAIN saga-outbox-worker",
        "$PY $MAIN health",
        "$PY $MAIN scheduler",
    ]:
        if stale in start:
            errors.append(f"scripts/start.sh still manually launches a worker role: {stale}")

    require(
        workflow,
        "python3 scripts/ci/lint_runtime_worker_supervision.py",
        ".github/workflows/lint.yml",
        errors,
    )

    if errors:
        print("lint_runtime_worker_supervision FAILED", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("lint_runtime_worker_supervision OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
