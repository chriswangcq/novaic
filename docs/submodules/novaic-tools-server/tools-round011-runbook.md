# Tools Server — Round 011 Runbook: Full Remote Verification

> Remote-first. No local sibling directories. All paths from the GitHub clone root.
> Canonical repo: `https://github.com/chriswangcq/novaic-tools-server`

---

## Step 1 — Clone and install

```bash
git clone https://github.com/chriswangcq/novaic-tools-server novaic-tools-server
cd novaic-tools-server
pip3 install -r requirements.txt
```

---

## Step 2 — Import probe (R011 acceptance command 1)

```bash
python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
print('TOOLS_PREFLIGHT_IMPORT_OK')
"
```

**Expected:** `TOOLS_PREFLIGHT_IMPORT_OK`

---

## Step 3 — Packaged-split pass replay

```bash
export NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd)
export NOVAIC_TOOLS_PORT=19998
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
export NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993
export NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994

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

## Step 4 — Standalone pass replay

```bash
env -i python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert r.ok and r.mode == 'standalone', repr(r)
print(r.marker)
print('TOOLS_PREFLIGHT_STANDALONE_REPLAY:PASS')
"
```

**Expected:** `TOOLS_PREFLIGHT:PASS mode=standalone`

---

## Step 5 — Failure-path replays (env -i isolated)

```bash
# Missing GATEWAY_URL
env -i NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd) \
  NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993 \
  NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994 \
  python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert not r.ok and 'TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING' in r.error
print('TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS')
"

# Missing RUNTIME_ORCHESTRATOR_URL
env -i NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd) \
  NOVAIC_GATEWAY_URL=http://127.0.0.1:19999 \
  NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994 \
  python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert not r.ok and 'TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING' in r.error
print('TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS')
"

# Missing TOOL_RESULT_SERVICE_URL
env -i NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd) \
  NOVAIC_GATEWAY_URL=http://127.0.0.1:19999 \
  NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993 \
  python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert not r.ok and 'TOOLS_PREFLIGHT_ERROR:TOOL_RESULT_SERVICE_URL_MISSING' in r.error
print('TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS')
"
```

---

## Step 6 — Unit test baseline (R011 acceptance command 2)

```bash
python3 -m pytest -q tests/unit/tools_server/
echo "TOOLS_UNIT_BASELINE:PASS"
```

**Expected:** `6 passed`, then `TOOLS_UNIT_BASELINE:PASS`

---

## Mandatory env policy (locked)

| Env var | Required in split mode | Error code on missing |
|---------|----------------------|----------------------|
| `NOVAIC_TOOLS_SERVER_SPLIT_REPO` | yes | `SPLIT_PATH_MISSING` / `MAIN_TOOLS_MISSING` |
| `NOVAIC_GATEWAY_URL` | yes | `GATEWAY_URL_MISSING` |
| `NOVAIC_RUNTIME_ORCHESTRATOR_URL` | yes | `RUNTIME_ORCHESTRATOR_URL_MISSING` |
| `NOVAIC_TOOL_RESULT_SERVICE_URL` | yes | `TOOL_RESULT_SERVICE_URL_MISSING` |
| `NOVAIC_TOOLS_PORT` | no — defaults to 19998 | n/a |

---

## Marker matrix (round-011)

| Marker | Condition |
|--------|-----------|
| `TOOLS_PREFLIGHT_IMPORT_OK` | preflight module import succeeds (R011 acceptance command 1) |
| `TOOLS_PREFLIGHT:PASS mode=packaged-split port=<N>` | all env vars valid, split mode |
| `TOOLS_PREFLIGHT:PASS mode=standalone` | no split repo set |
| `TOOLS_PREFLIGHT_PASS_REPLAY:PASS` | packaged-split pass replay asserted OK |
| `TOOLS_PREFLIGHT_STANDALONE_REPLAY:PASS` | standalone pass replay asserted OK |
| `TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING` | NOVAIC_GATEWAY_URL absent |
| `TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING` | NOVAIC_RUNTIME_ORCHESTRATOR_URL absent |
| `TOOLS_PREFLIGHT_ERROR:TOOL_RESULT_SERVICE_URL_MISSING` | NOVAIC_TOOL_RESULT_SERVICE_URL absent |
| `TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING` | split repo path not on disk |
| `TOOLS_PREFLIGHT_ERROR:MAIN_TOOLS_MISSING` | main_tools.py absent |
| `TOOLS_PREFLIGHT_FAIL_CLOSED:PASS` | fail-closed guard triggered in test |
| `TOOLS_UNIT_BASELINE:PASS` | 6 unit tests passed (R011 acceptance command 2) |
| `TOOLS_R011_RUNBOOK_COMPLETE:PASS` | this runbook verified present with all markers |
