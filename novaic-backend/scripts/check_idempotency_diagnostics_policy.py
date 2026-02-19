#!/usr/bin/env python3
"""Verify diagnostics policy markers and cross-file drift."""

from pathlib import Path
import re
import sys


RUNBOOK = Path("novaic-backend/task_queue/RETRY_IDEMPOTENCY_RUNBOOK.md")
GOVERNANCE = Path("contracts/AGENT_RUNTIME_DIAGNOSTICS_POLICY.md")

CANONICAL_PATTERNS = [
    r"Default query limit:\s*`20`",
    r"(hard upper bound|Maximum query limit)(:\s*|\s+)`200`",
    r"only_contended=true",
    r"(every|mode: run diagnostics every)\s*`5m`",
    r"(every|mode: run diagnostics every)\s*`60m`",
    r"(at least|Retain .* for at least)\s*`7d`",
    r"(at least|Retain .* for at least)\s*`14d`",
]


def main() -> int:
    for file_path in (RUNBOOK, GOVERNANCE):
        if not file_path.exists():
            print(f"[policy-check] missing file: {file_path}")
            return 1

    failures = 0
    for file_path in (RUNBOOK, GOVERNANCE):
        content = file_path.read_text(encoding="utf-8")
        missing = []
        for pat in CANONICAL_PATTERNS:
            if re.search(pat, content, flags=re.IGNORECASE) is None:
                missing.append(pat)
        if missing:
            failures += 1
            print(f"[policy-check] missing markers in {file_path}:")
            for m in missing:
                print(f"  - {m}")

    if failures:
        return 1

    print("[policy-check] PASS diagnostics policy markers present and aligned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
