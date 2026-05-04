#!/usr/bin/env python3
"""Require risky retired-path terms in old roadmap tickets to be fenced.

Historical tickets can mention old mechanisms, but they must not look like
current architecture or active backlog. Any ticket/review that mentions one of
the high-risk retired terms below needs the standard archive banner.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TICKETS = ROOT / "docs" / "roadmap" / "tickets"

RISKY = re.compile(
    r"message_outbox|SPAWN_SUBAGENT|SUBAGENT_COMPLETED|"
    r"subagent_completed|subagent_report|subagent_query|subagent_cancel"
)
BANNER = "Historical ticket archive:"
EXEMPT = {
    TICKETS / "README.md",
    TICKETS / "PR-210-maintenance-tail-cleanup.md",
}


def main() -> int:
    failures: list[str] = []
    for path in sorted(TICKETS.rglob("*.md")):
        if path in EXEMPT:
            continue
        text = path.read_text(encoding="utf-8")
        if RISKY.search(text) and BANNER not in text:
            failures.append(str(path.relative_to(ROOT)))

    if failures:
        print(
            "Roadmap ticket archaeology mentions retired paths without an "
            "archive banner:",
            file=sys.stderr,
        )
        for rel in failures:
            print(f"  - {rel}", file=sys.stderr)
        print(
            "Add the standard 'Historical ticket archive:' banner or remove "
            "the stale wording.",
            file=sys.stderr,
        )
        return 1

    print("lint_roadmap_ticket_archaeology: historical retired-path tickets are fenced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
