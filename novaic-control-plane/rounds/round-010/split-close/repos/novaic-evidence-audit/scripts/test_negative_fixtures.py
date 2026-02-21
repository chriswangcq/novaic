"""Negative fixture tests for Round 010.

Tests:
1. negative-unreachable-sha-report.md:
   - repo_url is valid canonical https://github.com/chriswangcq/novaic (PASS for URL check)
   - commit_sha is deadbeefdeadbeefdeadbeefdeadbeefdeadbeef (UNREACHABLE via git cat-file)
   - Audit must report UNREACHABLE and fail.

Exit 0 = all negative tests passed (detections worked).
Exit 1 = a detection was missed (false negative in the audit logic).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = SCRIPT_DIR.parent / "test-fixtures"

REMOTE_TO_LOCAL: dict[str, str] = {
    "https://github.com/chriswangcq/novaic": "/Users/wangchaoqun/novaic",
}

CANONICAL_REPOS = {
    "https://github.com/chriswangcq/novaic",
    "https://github.com/chriswangcq/novaic-gateway",
    "https://github.com/chriswangcq/novaic-runtime-orchestrator",
    "https://github.com/chriswangcq/novaic-agent-runtime",
    "https://github.com/chriswangcq/novaic-tools-server",
    "https://github.com/chriswangcq/novaic-storage-a",
    "https://github.com/chriswangcq/novaic-storage-b",
}


def _normalise(raw: str) -> str:
    u = raw.strip()
    u = re.sub(r"^-\s+", "", u)
    return u.strip("`").rstrip("/")


def check_reachability(repo_url: str, sha: str) -> str:
    u = _normalise(repo_url)
    s = _normalise(sha)
    if len(s) != 40 or u not in CANONICAL_REPOS:
        return "SKIP_REMOTE"
    local_path = REMOTE_TO_LOCAL.get(u)
    if local_path is None:
        return "SKIP_REMOTE"
    try:
        r = subprocess.run(
            ["git", "-C", local_path, "cat-file", "-e", f"{s}^{{commit}}"],
            capture_output=True, timeout=5,
        )
        return "REACHABLE" if r.returncode == 0 else "UNREACHABLE"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "SKIP_REMOTE"


def test_unreachable_sha_fixture() -> bool:
    """deadbeef sha must be reported as UNREACHABLE for chriswangcq/novaic."""
    fixture_path = FIXTURE_DIR / "negative-unreachable-sha-report.md"
    text = fixture_path.read_text(encoding="utf-8")

    urls = [m.group(1).strip() for m in
            re.finditer(r"^\s*- repo_url:[ \t]*(.*)$", text, flags=re.MULTILINE)]
    shas = [m.group(1).strip() for m in
            re.finditer(r"^\s*- commit_sha:[ \t]*(.*)$", text, flags=re.MULTILINE)]

    passed = True
    for url, sha in zip(urls, shas):
        result = check_reachability(url, sha)
        if result != "UNREACHABLE":
            print(f"FAIL: expected UNREACHABLE for sha={_normalise(sha)[:12]}, got {result}")
            passed = False
        else:
            print(f"OK: sha={_normalise(sha)[:12]} correctly detected as UNREACHABLE")

    return passed


def main() -> None:
    all_pass = True

    print("── test: negative-unreachable-sha-report ──")
    if not test_unreachable_sha_fixture():
        all_pass = False

    print()
    if all_pass:
        print("ROUND010_NEGATIVE_FIXTURE_PASS")
    else:
        print("ROUND010_NEGATIVE_FIXTURE_FAIL")
        sys.exit(1)


if __name__ == "__main__":
    main()
