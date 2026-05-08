#!/usr/bin/env python3
"""Fail when current architecture docs and roadmap ticket status drift apart."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class StatusExpectation:
    path: Path
    required: tuple[str, ...]
    forbidden: tuple[str, ...]


EXPECTATIONS = (
    StatusExpectation(
        path=ROOT / "docs/roadmap/tickets/PR-338-business-only-dsl-phase-bill.md",
        required=(
            "Status: Closed",
            "P007 closed: final residue audit and parent closure.",
        ),
        forbidden=(
            "Status: Doing",
            "P007 in progress",
        ),
    ),
    StatusExpectation(
        path=ROOT / "docs/architecture/generic-worker-substrate-plan.md",
        required=(
            "| 13 | Closed | DSL residue audit and closure |",
            "- P019 final audit confirmed business handler modules contain job specs and",
        ),
        forbidden=(
            "| 13 | Doing |",
            "P007 in progress",
        ),
    ),
)


def main() -> int:
    failures: list[str] = []
    for expectation in EXPECTATIONS:
        rel = expectation.path.relative_to(ROOT)
        if not expectation.path.exists():
            failures.append(f"{rel}: expected status document is missing")
            continue
        text = expectation.path.read_text(encoding="utf-8")
        for required in expectation.required:
            if required not in text:
                failures.append(f"{rel}: missing required marker {required!r}")
        for forbidden in expectation.forbidden:
            if forbidden in text:
                failures.append(f"{rel}: forbidden stale marker {forbidden!r}")

    if failures:
        print("Docs status consistency lint failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print("lint_docs_status_consistency: architecture and roadmap status markers are aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
