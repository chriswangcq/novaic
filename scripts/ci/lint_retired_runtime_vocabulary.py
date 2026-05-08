#!/usr/bin/env python3
"""Reject retired runtime vocabulary in active code paths."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()

SCAN_ROOTS = [
    REPO / "novaic-agent-runtime" / "queue_service",
    REPO / "novaic-agent-runtime" / "task_queue",
    REPO / "novaic-agent-runtime" / "tests",
    REPO / "novaic-business" / "business",
    REPO / "novaic-business" / "tests",
    REPO / "scripts" / "ci",
]

FORBIDDEN = [
    "list_active_sessions",
    "rebuild_active_sessions_from_sagas",
    "prompt-splice",
    "prompt_splice",
    "prompt splice",
    "TRANSITIONAL",
]

TEXT_SUFFIXES = {".py", ".sh", ".md", ".txt"}


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path == SCRIPT or not path.is_file():
                continue
            if path.suffix in TEXT_SUFFIXES or path.name in {"deploy", "start.sh"}:
                files.append(path)
    return files


def main() -> int:
    violations: list[str] = []
    for path in _iter_files():
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token in source:
                violations.append(f"{path.relative_to(REPO)} contains retired token {token!r}")

    if violations:
        print("retired runtime vocabulary lint FAILED")
        for violation in violations:
            print(violation)
        return 1

    print("retired runtime vocabulary lint OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
