#!/usr/bin/env python3
"""
storage_ab_governance_check.py
Rule: STORAGE-GOV-001 (contracts/STORAGE_SCHEMA_GOVERNANCE.md)

Local CI simulation for the `storage-contract-governance` job.
Run this script when `gh` CLI / GITHUB_TOKEN are unavailable.

Usage:
    python3 novaic-backend/scripts/storage_ab_governance_check.py [--base BASE_SHA] [--head HEAD_SHA]

Output:
    Prints governance check result to stdout.
    Exit code 0 = governance_guardrail: PASS
    Exit code 1 = governance_guardrail: FAIL

Evidence capture (for STORAGE-GOV-001 compliance):
    python3 novaic-backend/scripts/storage_ab_governance_check.py \
        | tee ops-rounds/<round>/20-reports/team-storage-ab-ci-governance-trace.md
"""

import os
import pathlib
import subprocess
import sys
import datetime as _dt

SCHEMA_PATH    = "contracts/schema/storage-api.v1.schema.json"
EVIDENCE_PATH  = "contracts/evidence/storage-contract-diff-latest.md"
CHANGELOG_PATH = "contracts/STORAGE_SCHEMA_CHANGELOG.md"

def run_check(base_sha: str, head_sha: str) -> bool:
    print(f"storage-contract-governance local simulation")
    print(f"simulation_note: local execution of storage-contract-governance CI job logic")
    print(f"timestamp: {_dt.datetime.now(_dt.timezone.utc).isoformat()}")
    print(f"base_sha: {base_sha}")
    print(f"head_sha: {head_sha}")
    print()

    try:
        changed_raw = subprocess.check_output(
            ["git", "diff", "--name-only", base_sha, head_sha], text=True
        ).strip()
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: git diff failed: {exc}")
        return False

    changed_set = set(changed_raw.splitlines())
    print("Changed files:")
    for item in sorted(changed_set):
        print(f"  {item}")
    print()

    if SCHEMA_PATH not in changed_set:
        print(f"Schema not changed ({SCHEMA_PATH} not in diff) — guardrail not triggered.")
        print("governance_guardrail: PASS")
        print("exit_code: 0")
        return True

    print(f"Schema changed! Checking companion files...")
    missing = [p for p in (EVIDENCE_PATH, CHANGELOG_PATH) if p not in changed_set]
    if missing:
        print(f"FAIL: companion files not updated: {missing}")
        print("governance_guardrail: FAIL")
        print("exit_code: 1")
        return False

    for path, required_markers in [
        (EVIDENCE_PATH, ["schema_version_check: PASS", "schema_owner_check: PASS"]),
        (CHANGELOG_PATH, ["storage-api.v1.schema.json"]),
    ]:
        text = pathlib.Path(path).read_text(encoding="utf-8")
        for marker in required_markers:
            if marker not in text:
                print(f"FAIL: missing marker '{marker}' in {path}")
                print("governance_guardrail: FAIL")
                print("exit_code: 1")
                return False
        print(f"  {path}: markers OK")

    print()
    print("governance_guardrail: PASS")
    print("exit_code: 0")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="STORAGE-GOV-001 local CI simulation")
    parser.add_argument("--base", default="", help="Base SHA (default: HEAD~1)")
    parser.add_argument("--head", default="", help="Head SHA (default: HEAD)")
    args = parser.parse_args()

    base = args.base or subprocess.check_output(
        ["git", "rev-parse", "HEAD~1"], text=True
    ).strip()
    head = args.head or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()

    ok = run_check(base, head)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
