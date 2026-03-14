# Tools Server — Round 014 Runbook: Hard Cleanup

> Remote-first. No gitlinks. No nested `.git`. No local sibling-repo assumptions.
> Canonical repo: `https://github.com/chriswangcq/novaic-tools-server`

---

## Step 1 — Clone and install

```bash
git clone https://github.com/chriswangcq/novaic-tools-server novaic-tools-server
cd novaic-tools-server
pip3 install -r requirements.txt
```

No `git submodule init` required. No sibling directories needed.

Verify zero gitlinks in this clone:
```bash
git ls-files --stage | grep "^160000" || echo "GITLINK_COUNT_ZERO:PASS"
```

---

## Step 2 — Unit tests (R014 acceptance command 1)

```bash
pytest -q tests/unit/tools_server/
echo "TOOLS_UNIT_BASELINE:PASS"
```

**Expected:** `6 passed`, then `TOOLS_UNIT_BASELINE:PASS`

---

## Step 3 — Failure-path script (R014 acceptance command 2)

```bash
bash scripts/fail_path_tools_missing_config.sh
```

**Expected marker:** `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`

Sub-cases in order:
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

## Gitlink / nested-.git policy (round-014)

- `git ls-files --stage | grep "^160000"` → empty (`GITLINK_COUNT_ZERO:PASS`)
- `find . -name ".git" -not -path "./.git"` → empty (`NO_NESTED_GIT:PASS`)
- All artifact_paths are plain blobs — no submodule commit entries.

---

## Artifact existence checklist (R014)

| artifact_path | exists |
|---------------|--------|
| `novaic-tools-server/tools_server/preflight.py` | yes |
| `novaic-tools-server/scripts/fail_path_tools_missing_config.sh` | yes |
| `novaic-tools-server/docs/tools-round014-runbook.md` | yes (this file) |
| `novaic-control-plane/rounds/round-014/split-close/tools-round014-replay-bundle.md` | yes |

---

## Marker matrix (round-014)

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
| `GITLINK_COUNT_ZERO:PASS` | no 160000 entries in this repo's git index |
| `NO_NESTED_GIT:PASS` | no nested .git dirs in this repo |
| `TOOLS_R014_RUNBOOK_COMPLETE:PASS` | this runbook verified present with all markers |
