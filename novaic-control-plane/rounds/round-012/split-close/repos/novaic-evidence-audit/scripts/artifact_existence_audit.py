#!/usr/bin/env python3
"""
artifact_existence_audit.py — checks that every artifact_path field in
round-012 team reports physically exists under the repository workspace.

Run from anywhere; resolves paths relative to this script's own location.

Exit 0 + ARTIFACT_EXISTENCE_AUDIT=PASS  when zero missing paths.
Exit 1 + ARTIFACT_EXISTENCE_AUDIT=FAIL  when any path is missing.
"""

import pathlib
import re
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
# Script lives at: <repo>/novaic-control-plane/rounds/round-012/split-close/repos/novaic-evidence-audit/scripts/
REPO_ROOT = SCRIPT_DIR.parents[6]

REPORTS_DIR = REPO_ROOT / "novaic-control-plane" / "rounds" / "round-012" / "20-reports"

ARTIFACT_RE = re.compile(r"artifact_path\s*:\s*`([^`]+)`")

missing = []
checked = []

report_files = sorted(REPORTS_DIR.glob("team-*.md"))
if not report_files:
    print(f"ARTIFACT_EXISTENCE_AUDIT=SKIP (no report files found in {REPORTS_DIR.relative_to(REPO_ROOT)})")
    sys.exit(0)

for report in report_files:
    text = report.read_text()
    for m in ARTIFACT_RE.finditer(text):
        artifact = m.group(1).strip()
        # Paths are relative to repo root
        resolved = REPO_ROOT / artifact
        checked.append(artifact)
        if not resolved.exists():
            missing.append(artifact)
            print(f"  MISSING  {artifact}")
        else:
            print(f"  OK       {artifact}")

print(f"checked={len(checked)}  missing={len(missing)}")

if missing:
    print("ARTIFACT_EXISTENCE_AUDIT=FAIL")
    sys.exit(1)
else:
    print("ARTIFACT_EXISTENCE_AUDIT=PASS")
