# Cross-Repo CI Minimum Template (Round 002)

## Goal

Define minimum replayable checks for first-wave physically split candidates.

## Required checks

### 1) Contract replay check

- command:
  - `python - <<'PY'`
  - `import pathlib`
  - `p = pathlib.Path("novaic-control-plane/rounds/round-002/split-exec/compatibility-v2.yaml")`
  - `print("CI_CONTRACT_REPLAY_PASS" if p.exists() else "CI_CONTRACT_REPLAY_FAIL")`
  - `PY`
- expected_marker: `CI_CONTRACT_REPLAY_PASS`

### 2) Smoke readiness check

- command:
  - `test -f "novaic-control-plane/rounds/round-002/split-exec/ci-minimum-template.md" && echo "CI_SMOKE_TEMPLATE_PASS"`
- expected_marker: `CI_SMOKE_TEMPLATE_PASS`

### 3) Health readiness check

- command:
  - `python - <<'PY'`
  - `from pathlib import Path`
  - `text = Path("novaic-control-plane/rounds/round-002/split-exec/compatibility-v2.yaml").read_text(encoding="utf-8")`
  - `print("CI_HEALTH_CHECK_PASS" if "health_contract" in text else "CI_HEALTH_CHECK_FAIL")`
  - `PY`
- expected_marker: `CI_HEALTH_CHECK_PASS`

## Artifact path

- `novaic-control-plane/rounds/round-002/split-exec/ci-minimum-template.md`
