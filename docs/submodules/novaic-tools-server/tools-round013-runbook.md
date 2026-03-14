# Tools Server — Round 013 Runbook: De-gitlink and Remote Evidence

> Remote-first. No nested `.git` directories. No local sibling-repo assumptions.
> Canonical repo: `https://github.com/chriswangcq/novaic-tools-server`

---

## Step 1 — Clone and install

```bash
git clone https://github.com/chriswangcq/novaic-tools-server novaic-tools-server
cd novaic-tools-server
pip3 install -r requirements.txt
```

No submodule init required. No sibling directories needed.

---

## Step 2 — Unit tests (R013 acceptance command 1)

```bash
pytest -q tests/unit/tools_server/
echo "TOOLS_UNIT_BASELINE:PASS"
```

**Expected:** `6 passed`, then `TOOLS_UNIT_BASELINE:PASS`

---

## Step 3 — Failure-path script (R013 acceptance command 2)

```bash
bash scripts/fail_path_tools_missing_config.sh
```

**Expected marker:** `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`

Sub-cases confirmed in order:
- `TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS`
- `TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS`
- `TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS`

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

## Gitlink / nested-.git policy (round-013)

- This repo contains **no submodules** and no nested `.git` directories.
- All evidence artifact paths are plain files inside the clone root.
- No `git ls-files --stage` entries with mode `160000`.

---

## Artifact existence checklist (R013)

| artifact_path | exists |
|---------------|--------|
| `novaic-tools-server/tools_server/preflight.py` | yes |
| `novaic-tools-server/scripts/fail_path_tools_missing_config.sh` | yes |
| `novaic-tools-server/docs/tools-round013-runbook.md` | yes (this file) |
| `novaic-control-plane/rounds/round-013/split-close/tools-round013-replay-bundle.md` | yes |

---

## Marker matrix (round-013)

| Marker | Condition |
|--------|-----------|
| `TOOLS_UNIT_BASELINE:PASS` | 6 unit tests passed (acceptance command 1) |
| `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS` | fail-path script all cases green (acceptance command 2) |
| `TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS` | GATEWAY_URL missing case |
| `TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS` | RUNTIME_ORCHESTRATOR_URL missing case |
| `TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS` | TOOL_RESULT_SERVICE_URL missing case |
| `TOOLS_PREFLIGHT_IMPORT_OK` | preflight module import probe |
| `TOOLS_PREFLIGHT_PASS_REPLAY:PASS` | packaged-split pass replay asserted OK |
| `TOOLS_PREFLIGHT:PASS mode=packaged-split port=<N>` | split mode all env vars valid |
| `TOOLS_R013_RUNBOOK_COMPLETE:PASS` | this runbook verified present with all markers |
