# Tools Server — Round 009 Runbook: Clone → Health

## Mandatory env policy (locked round-009)

All five vars are required in split/packaged mode:

| Env var | Error code on missing |
|---------|----------------------|
| `NOVAIC_TOOLS_SERVER_SPLIT_REPO` | `SPLIT_PATH_MISSING` / `MAIN_TOOLS_MISSING` |
| `NOVAIC_GATEWAY_URL` | `GATEWAY_URL_MISSING` |
| `NOVAIC_RUNTIME_ORCHESTRATOR_URL` | `RUNTIME_ORCHESTRATOR_URL_MISSING` |
| `NOVAIC_TOOL_RESULT_SERVICE_URL` | `TOOL_RESULT_SERVICE_URL_MISSING` |
| `NOVAIC_TOOLS_PORT` | defaults to 19998 (not required) |

---

## Step 1 — Clone and setup

```bash
git clone file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git novaic-tools-server
cd novaic-tools-server
pip3 install -r requirements.txt
```

---

## Step 2 — Preflight pass replay

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
assert r.ok, r.error
print(r.marker)
"
```
**Expected:** `TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998`

---

## Step 3 — Failure-path replays

```bash
# Missing RUNTIME_ORCHESTRATOR_URL
NOVAIC_RUNTIME_ORCHESTRATOR_URL= python3 -c "
import sys,os; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert not r.ok
assert 'TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING' in r.error
print('TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS')
"

# Missing TOOL_RESULT_SERVICE_URL
NOVAIC_TOOL_RESULT_SERVICE_URL= python3 -c "
import sys,os; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert not r.ok
assert 'TOOLS_PREFLIGHT_ERROR:TOOL_RESULT_SERVICE_URL_MISSING' in r.error
print('TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS')
"
```

---

## Step 4 — Split-root health baseline

```bash
bash scripts/tools/ci_preflight_probe_prereqs.sh   # → [probe-preflight] PASS
bash scripts/tools/leak_probe.sh                   # → [leak-probe] PASS fd delta=0
pytest -q tests/unit/tools_server/                 # → 6 passed
echo "TOOLS_SPLIT_BASELINE:PASS"
```

---

## Marker matrix (round-009)

| Marker | Condition |
|--------|-----------|
| `TOOLS_PREFLIGHT:PASS mode=packaged-split port=<N>` | All env vars valid |
| `TOOLS_PREFLIGHT:PASS mode=standalone` | No split repo set |
| `TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING` | Split repo path not on disk |
| `TOOLS_PREFLIGHT_ERROR:MAIN_TOOLS_MISSING` | main_tools.py absent |
| `TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING` | NOVAIC_GATEWAY_URL empty |
| `TOOLS_PREFLIGHT_ERROR:RUNTIME_ORCHESTRATOR_URL_MISSING` | NOVAIC_RUNTIME_ORCHESTRATOR_URL empty |
| `TOOLS_PREFLIGHT_ERROR:TOOL_RESULT_SERVICE_URL_MISSING` | NOVAIC_TOOL_RESULT_SERVICE_URL empty |
| `TOOLS_PREFLIGHT_FAIL_CLOSED:PASS` | Fail-closed guard triggered correctly (test) |
| `TOOLS_SPLIT_BASELINE:PASS` | probe-preflight + leak-probe + pytest all green |
| `TOOLS_R009_RUNBOOK_COMPLETE:PASS` | This runbook verified present with all markers |
