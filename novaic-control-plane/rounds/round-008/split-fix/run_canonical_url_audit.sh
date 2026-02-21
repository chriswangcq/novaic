#!/usr/bin/env bash
# run_canonical_url_audit.sh
# Scans all team-storage-ab-report.md files for prohibited local: scheme.
# Expected markers:
#   LOCAL_SCHEME_VIOLATIONS=0
#   CANONICAL_URL_AUDIT=PASS
set -uo pipefail
cd "$(dirname "$0")/../../.."   # workspace root (novaic/)
python - <<'PY'
from pathlib import Path
import re
targets = list(Path("novaic-control-plane/rounds").glob("*/20-reports/team-storage-ab-report.md"))
violations = [h for f in sorted(targets) for h in re.findall(r"local:novaic-storage-[ab]", f.read_text())]
count = len(violations)
print(f"LOCAL_SCHEME_VIOLATIONS={count}")
print("CANONICAL_URL_AUDIT=PASS" if count == 0 else "CANONICAL_URL_AUDIT=FAIL")
if count > 0:
    for v in violations:
        print(f"  VIOLATION: {v}")
    raise SystemExit(1)
PY
