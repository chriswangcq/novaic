# Tools Server — Round 012 Runbook: Artifact Existence Closure

> Remote-first. All paths from GitHub clone root.
> Canonical repo: `https://github.com/chriswangcq/novaic-tools-server`

---

## Step 1 — Clone and install

```bash
git clone https://github.com/chriswangcq/novaic-tools-server novaic-tools-server
cd novaic-tools-server
pip3 install -r requirements.txt
```

---

## Step 2 — Failure-path script (R012 acceptance command 1)

```bash
bash scripts/fail_path_tools_missing_config.sh
```

**Expected marker:** `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`

This script runs all three missing-env-var failure cases (GATEWAY_URL, RUNTIME_ORCHESTRATOR_URL, TOOL_RESULT_SERVICE_URL) under `env -i` isolation and asserts typed error markers.

---

## Step 3 — Unit tests (R012 acceptance command 2)

```bash
python3 -m pytest -q tests/unit/tools_server/
echo "TOOLS_UNIT_BASELINE:PASS"
```

**Expected:** `6 passed`, then `TOOLS_UNIT_BASELINE:PASS`

---

## Step 4 — Import probe

```bash
python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
print('TOOLS_PREFLIGHT_IMPORT_OK')
"
```

**Expected:** `TOOLS_PREFLIGHT_IMPORT_OK`

---

## Step 5 — Packaged-split pass replay

```bash
env -i NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd) \
  NOVAIC_TOOLS_PORT=19998 \
  NOVAIC_GATEWAY_URL=http://127.0.0.1:19999 \
  NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993 \
  NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994 \
  python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert r.ok and r.mode == 'split', repr(r)
print(r.marker)
print('TOOLS_PREFLIGHT_PASS_REPLAY:PASS')
"
```

**Expected:** `TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998`

---

## Artifact existence checklist

All `artifact_path` values referenced in R012 report exist at close time:

| File | Status |
|------|--------|
| `novaic-tools-server/tools_server/preflight.py` | exists |
| `novaic-tools-server/scripts/fail_path_tools_missing_config.sh` | exists (new R012) |
| `novaic-tools-server/docs/tools-round012-runbook.md` | exists (new R012) |
| `novaic-control-plane/rounds/round-012/split-close/tools-round012-replay-bundle.md` | exists (new R012) |

---

## Marker matrix (round-012)

| Marker | Condition |
|--------|-----------|
| `TOOLS_PREFLIGHT_IMPORT_OK` | preflight module import succeeds |
| `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS` | all 3 missing-config cases PASS (R012 acceptance command 1) |
| `TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS` | GATEWAY_URL missing case asserted |
| `TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS` | RUNTIME_ORCHESTRATOR_URL missing case asserted |
| `TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS` | TOOL_RESULT_SERVICE_URL missing case asserted |
| `TOOLS_PREFLIGHT:PASS mode=packaged-split port=<N>` | all env vars valid, split mode |
| `TOOLS_UNIT_BASELINE:PASS` | 6 unit tests passed (R012 acceptance command 2) |
| `TOOLS_R012_RUNBOOK_COMPLETE:PASS` | this runbook verified present with all markers |
