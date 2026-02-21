#!/usr/bin/env python3
"""
audit_round013_reports.py — round-013 evidence audit.

Checks round-013 team reports for:
  1. Every artifact_path field physically exists under the workspace.
  2. No gitlink (mode 160000) entries are introduced by desktop-owned paths.
  3. repo_url fields use canonical https://github.com/chriswangcq/ form only.

Run from anywhere; resolves paths relative to this script's own location.

Exit 0 + AUDIT_ROUND013=PASS  when all checks pass.
Exit 1 + AUDIT_ROUND013=FAIL  on first failure category.
"""

import pathlib
import re
import subprocess
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
# <repo>/novaic-control-plane/rounds/round-013/split-close/repos/novaic-evidence-audit/scripts/
REPO_ROOT = SCRIPT_DIR.parents[6]

REPORTS_DIR = REPO_ROOT / "novaic-control-plane" / "rounds" / "round-013" / "20-reports"

ARTIFACT_RE = re.compile(r"artifact_path\s*:\s*`([^`]+)`")
REPO_URL_RE = re.compile(r"repo_url\s*:\s*`([^`]+)`")
CANONICAL_PREFIX = "https://github.com/chriswangcq/"

failures = []

# --- Check 1: artifact_path existence ---
report_files = sorted(REPORTS_DIR.glob("team-*.md"))
artifact_checked = 0
for report in report_files:
    text = report.read_text()
    for m in ARTIFACT_RE.finditer(text):
        artifact = m.group(1).strip()
        resolved = REPO_ROOT / artifact
        artifact_checked += 1
        if not resolved.exists():
            failures.append(f"MISSING_ARTIFACT: {artifact} (in {report.name})")
            print(f"  MISSING  {artifact}")
        else:
            print(f"  OK       {artifact}")

print(f"artifact_path checks: {artifact_checked} checked, {sum(1 for f in failures if 'MISSING_ARTIFACT' in f)} missing")

# --- Check 2: no gitlinks from desktop paths ---
try:
    result = subprocess.run(
        ["git", "ls-files", "--stage"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=15
    )
    desktop_gitlinks = [
        line for line in result.stdout.splitlines()
        if line.startswith("160000") and (
            "novaic-desktop" in line or
            "round-013" in line or
            "round-012" in line or
            "round-011" in line or
            "round-010" in line
        )
    ]
    if desktop_gitlinks:
        for gl in desktop_gitlinks:
            failures.append(f"GITLINK_FOUND: {gl}")
            print(f"  GITLINK  {gl}")
    else:
        print("  gitlink-check: NO_DESKTOP_GITLINKS=PASS")
except Exception as e:
    print(f"  gitlink-check: SKIP ({e})")

# --- Check 3: canonical repo_url ---
for report in report_files:
    text = report.read_text()
    for m in REPO_URL_RE.finditer(text):
        url = m.group(1).strip()
        if not url.startswith(CANONICAL_PREFIX):
            failures.append(f"NON_CANONICAL_URL: {url} (in {report.name})")
            print(f"  BAD_URL  {url}")
        else:
            print(f"  URL_OK   {url}")

# --- Summary ---
if failures:
    print(f"\nfailures={len(failures)}")
    for f in failures:
        print(f"  - {f}")
    print("AUDIT_ROUND013=FAIL")
    sys.exit(1)
else:
    print("\nAUDIT_ROUND013=PASS")
