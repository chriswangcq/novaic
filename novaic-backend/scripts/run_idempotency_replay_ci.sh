#!/usr/bin/env bash
set -euo pipefail

echo "[idempotency-ci] Running unit replay checks..."
pytest -q "novaic-backend/tests/unit/task_queue/test_retry_policy_and_idempotency.py"

echo "[idempotency-ci] Running integration replay checks..."
pytest -q "novaic-backend/tests/integration/task_queue/test_cross_process_idempotency.py"

echo "[idempotency-ci] Verifying normative diagnostics policy markers..."
python "novaic-backend/scripts/check_idempotency_diagnostics_policy.py"

echo "[idempotency-ci] Verifying diagnostics/contention documentation and code markers..."
if command -v rg >/dev/null 2>&1; then
  rg "contention|diagnostics|idempotency ledger" "novaic-backend" -g "*.py" -g "*.md"
else
  python - <<'PY'
from pathlib import Path
import re

root = Path("novaic-backend")
pat = re.compile(r"contention|diagnostics|idempotency ledger", re.IGNORECASE)
count = 0
for path in root.rglob("*"):
    if path.suffix not in {".py", ".md"}:
        continue
    if any(part in {".venv", "venv", "__pycache__"} for part in path.parts):
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if pat.search(text):
        print(path.as_posix())
        count += 1
if count == 0:
    raise SystemExit("No diagnostics/contention/idempotency ledger markers found")
PY
fi

echo "[idempotency-ci] PASS"
