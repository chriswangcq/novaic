#!/usr/bin/env python3
"""
PR-34 34e invariant guard: internal Wake/dispatch surfaces stay sync.

RFC contract (docs/roadmap/tickets/PR-34-worker-sync.md):
    Async only at the FastAPI edge; every worker/dispatcher/subscriber in
    the Message→Wake loop runs on its own thread/process and MUST NOT
    import asyncio, declare ``async def``, use ``await``, or instantiate
    ``httpx.AsyncClient``.

Why the guard exists (do not delete without replacement):
    Before PR-34 the dispatch loop used ``asyncio.create_task(...)`` inside
    the Business FastAPI lifespan. A single unhandled exception silently
    cancelled the Agent-loop drain until somebody noticed stale work — the
    original "silent failure" ticket that forced the Worker-Sync rewrite.
    Re-introducing async into any guarded file rewinds PR-34 and re-opens
    that failure mode, so we fail CI loudly instead of waiting for an
    Environment notification drain incident.

Scope is an explicit allowlist, not a directory glob, because:
    * Business FastAPI handlers ARE async by design (edge, uvicorn loop).
    * ``device_client.py`` / ``device_orchestrator.py`` speak to remote
      FastAPI services and stay async.
    * Only the files on ``GUARDED`` below are load-bearing for Wake.

Adding a file: append to ``GUARDED`` with a short ``why:`` comment.
Removing a file: only if the file itself is deleted. A "temporarily async"
exception is not a valid removal reason — hoist to an edge handler or
run_in_threadpool instead.

Exit codes:
    0  all guarded files clean, OR all guarded files are absent because
       submodules aren't checked out (CI-without-PAT case; prints a loud
       warning so it's obvious the run didn't actually verify anything)
    1  at least one guarded file re-introduced an async pattern
    2  some (but not all) guarded files are missing — probably a rename
       that skipped the guard, and worth failing on

The "all absent → exit 0" path exists because the main repo's CI workflow
runs without ``submodules: recursive`` (GITHUB_TOKEN can't auth the
cross-org submodules in .gitmodules). Locally and in pre-commit hooks
every file is present, so the script still catches real regressions
before they ship. A "partial present" state is more suspicious — it
usually means one submodule was renamed and the pointer wasn't
updated — so we keep exit 2 for that case.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

GUARDED: list[str] = [
    # why: Wake entry — every trigger hits assemble_sync/dispatch_sync.
    "novaic-common/common/wake/assembler.py",
    # why: agent→user resolution; async lock regression = cross-request deadlock.
    "novaic-common/common/agents/ownership.py",
    # why: DispatchSubscriber runs as its own subprocess (PR-34 34d);
    #      re-adding async collapses it back into a silent lifespan task.
    "novaic-business/business/subscribers/dispatch_subscriber.py",
    # why: subprocess entry; must stay a plain script, not an asyncio.run wrapper.
    "novaic-business/main_subscriber.py",
    # why: HealthWorker recovery loop — Queue/Saga timeout safety net.
    "novaic-agent-runtime/task_queue/workers/health_worker.py",
    # why: SchedulerWorker due-scan + dispatch.
    "novaic-agent-runtime/task_queue/workers/scheduler_worker.py",
    # why: SagaWorker (PR-34 34c) — same contract.
    "novaic-agent-runtime/task_queue/workers/saga_worker.py",
    # why: TaskWorker (PR-34 34c) — same contract.
    "novaic-agent-runtime/task_queue/workers/task_worker.py",
]

# Each rule is (label, compiled regex, hint). Regexes are applied line by
# line on the source (not AST) because a line-based match pinpoints the
# offending text for the CI log without extra dependencies.
#
# The patterns deliberately anchor on real syntax so docstrings / comments
# mentioning the words (e.g. "Before PR-34 this was async def run") don't
# false-positive. The check_line() helper strips leading whitespace before
# matching ``async def`` / ``await`` and skips pure-comment lines.
RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "async-def",
        re.compile(r"^\s*async\s+def\s+"),
        "declare a plain ``def`` and call ``run_in_threadpool`` at the FastAPI edge instead",
    ),
    (
        "asyncio-import",
        re.compile(r"^\s*(?:import\s+asyncio\b|from\s+asyncio\s+import\b)"),
        "use ``threading`` + ``time.sleep`` (sync worker) or hoist the async caller to an edge handler",
    ),
    (
        "httpx-async-client",
        re.compile(r"httpx\.AsyncClient\s*\("),
        "use ``httpx.Client`` (sync); see ``common/http/clients.py`` for the shared factory",
    ),
    (
        "await-expr",
        re.compile(r"^\s*(?:[^#\n]*?[^\w])?await\s+"),
        "remove ``await`` — guarded files are synchronous; call the ``*_sync`` twin",
    ),
]


def check_line(line: str) -> list[tuple[str, str]]:
    """Return a list of (rule_label, hint) violations for a single line.

    Lines whose first non-whitespace character is ``#`` are treated as pure
    comments and skipped; the regexes already anchor structural syntax, but
    this keeps the log output clean when someone writes an explanatory
    ``# was: async def run`` docstring.
    """
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return []
    hits: list[tuple[str, str]] = []
    for label, pattern, hint in RULES:
        if pattern.search(line):
            hits.append((label, hint))
    return hits


def check_file(path: Path) -> list[str]:
    """Return a list of human-readable violation messages for ``path``.

    An empty list means the file is clean. The format is
    ``{relative_path}:{lineno}: [{rule}] {line} -- {hint}``, matching the
    conventions of lint_dispatch.sh / lint_httpx.sh so a human scanning CI
    output can jump straight to the offending line.
    """
    rel = path.relative_to(REPO_ROOT)
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for label, hint in check_line(line):
            errors.append(
                f"{rel}:{lineno}: [{label}] {line.rstrip()}  -- {hint}"
            )
    return errors


def main() -> int:
    missing: list[str] = []
    violations: list[str] = []
    for rel in GUARDED:
        path = REPO_ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        violations.extend(check_file(path))

    if missing and len(missing) == len(GUARDED):
        # All guarded files absent → we're running in an environment without
        # submodule contents (main-repo CI without a PAT). Warn loudly so the
        # run output makes it obvious this invocation verified nothing, then
        # exit 0 so the workflow doesn't fail on a configuration issue that's
        # orthogonal to what the guard checks. Local / pre-commit / submodule-
        # CI invocations always have the files and still catch regressions.
        print(
            "check_no_internal_async: SKIPPED — all guarded files absent "
            "(submodules not checked out). This run did NOT verify the async "
            "invariants; rely on local pre-commit or per-submodule CI.",
            file=sys.stderr,
        )
        return 0

    if missing:
        # Partial presence is suspicious — one of the guarded files either
        # got renamed without updating ``GUARDED`` or the submodule pointer
        # was bumped past the rename. Fail so we notice.
        print(
            "check_no_internal_async: guarded file(s) missing — did a rename "
            "skip this script? (Other guarded files are present, so this "
            "isn't the submodules-absent case.)",
            file=sys.stderr,
        )
        for rel in missing:
            print(f"  MISSING: {rel}", file=sys.stderr)
        return 2

    if violations:
        print(
            "check_no_internal_async: internal Wake surface re-introduced "
            "async patterns. Fix these before merge:",
            file=sys.stderr,
        )
        for line in violations:
            print(f"  {line}", file=sys.stderr)
        print(
            "\nContext: PR-34 RFC mandates sync-by-default for every file "
            "listed in GUARDED. See scripts/ci/check_no_internal_async.py "
            "module docstring for why.",
            file=sys.stderr,
        )
        return 1

    print(f"check_no_internal_async: {len(GUARDED)} files clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
