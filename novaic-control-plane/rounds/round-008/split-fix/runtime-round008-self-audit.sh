#!/usr/bin/env bash
# Runtime Round 008 self-audit script.
# Run from monorepo root: bash novaic-control-plane/rounds/round-008/split-fix/runtime-round008-self-audit.sh
# Expected marker: runtime-round008-audit: PASS
set -euo pipefail

python - <<'PY'
import re
from pathlib import Path

CANONICAL = "file:///Users/wangchaoqun/split-remotes/"
issues = []

for rpath in [
    "novaic-control-plane/rounds/round-005/20-reports/team-runtime-report.md",
    "novaic-control-plane/rounds/round-006/20-reports/team-runtime-report.md",
    "novaic-control-plane/rounds/round-007/20-reports/team-runtime-report.md",
]:
    t = Path(rpath).read_text(encoding="utf-8")
    for l in t.splitlines():
        if re.match(r"^\s*-\s+repo_url:\s*", l):
            v = re.sub(r"^\s*-\s+repo_url:\s*", "", l).strip().strip("`")
            if v and not v.startswith(CANONICAL):
                issues.append(f"non-canonical: {rpath}: {v}")
        if re.match(r"^\s*-\s+status:\s*(PLANNED|PENDING)\s*$", l):
            issues.append(f"placeholder status: {rpath}: {l.strip()}")
    if "- status: DONE" not in t:
        issues.append(f"no DONE status in: {rpath}")

if issues:
    for i in issues:
        print("ISSUE:", i)
    raise SystemExit("runtime-round008-audit: FAIL")
print("runtime-round008-audit: PASS")
PY
