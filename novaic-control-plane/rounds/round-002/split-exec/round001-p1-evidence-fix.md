# Round 001 P1 Evidence Command Fix (Platform)

## Issue

Round 001 Platform report used a placeholder command:

- `python - <<'PY' ... check target_repo/Extraction order/Must stay shared ... PY`

This is not replayable as-is by non-authors.

## Replacement replayable command

```bash
python - <<'PY'
from pathlib import Path
checks = [
    (Path("novaic-control-plane/rounds/round-001/split-plan/repo-boundaries.md"), "target_repo"),
    (Path("novaic-control-plane/rounds/round-001/split-plan/migration-order.md"), "Extraction order"),
    (Path("novaic-control-plane/rounds/round-001/split-plan/shared-kernel-cut-list.md"), "Must stay shared"),
]
for path, needle in checks:
    text = path.read_text(encoding="utf-8")
    assert needle in text, f"missing marker {needle} in {path}"
print("R001_P1_EVIDENCE_FIX_PASS")
PY
```

## Expected marker

- `R001_P1_EVIDENCE_FIX_PASS`

## Artifact path

- `novaic-control-plane/rounds/round-002/split-exec/round001-p1-evidence-fix.md`
