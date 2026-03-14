# Tools Server — Packaged/Dev Mode Diagnostic Runbook

## Quick reference

| Mode | Trigger | Entry point |
|------|---------|-------------|
| `standalone` | `NOVAIC_TOOLS_SERVER_SPLIT_REPO` not set | `main_tools.py` (fallback config) |
| `split/dev` | env var set, Tauri debug build | `main_tools.py` via Python from split repo dir |
| `split/packaged` | env var set, Tauri release build | `main_tools.py` via Python with full env injection |

---

## Step 1 — Preflight check (always run first)

```bash
# From split repo root
export NOVAIC_TOOLS_SERVER_SPLIT_REPO=$(pwd)
export NOVAIC_TOOLS_PORT=19998
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
export NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993
export NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994

python3 -c "
import sys; sys.path.insert(0, '.')
from tools_server.preflight import preflight_check
r = preflight_check()
if r.ok:
    print(r.marker)
else:
    print(r.error, file=sys.stderr)
    print('TOOLS_PREFLIGHT_FAIL_CLOSED:PASS', file=sys.stderr)
    sys.exit(1)
"
```
**Expected:** `TOOLS_PREFLIGHT:PASS mode=packaged-split port=19998`

---

## Step 2 — Failure-path verification

```bash
# Missing split path → typed error + non-zero exit
NOVAIC_TOOLS_SERVER_SPLIT_REPO=/nonexistent/path \
NOVAIC_TOOLS_PORT=19998 \
NOVAIC_GATEWAY_URL=http://127.0.0.1:19999 \
python3 -c "
import os, sys; sys.path.insert(0, '.')
from tools_server.preflight import preflight_check
r = preflight_check()
assert not r.ok
assert 'TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING' in r.error
print(r.error)
print('TOOLS_PREFLIGHT_ERROR_SPLIT_PATH:PASS')
"
```
**Expected:** `TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING` … `TOOLS_PREFLIGHT_ERROR_SPLIT_PATH:PASS`

---

## Step 3 — Split-root baseline

```bash
cd <split-repo-root>
bash scripts/tools/ci_preflight_probe_prereqs.sh   # → [probe-preflight] PASS
bash scripts/tools/leak_probe.sh                   # → [leak-probe] PASS fd delta=0
pytest -q tests/unit/tools_server/                 # → 6 passed
echo "TOOLS_SPLIT_BASELINE:PASS"
```

---

## Marker matrix

| Marker | Meaning |
|--------|---------|
| `TOOLS_PREFLIGHT:PASS mode=packaged-split port=<N>` | All split env vars valid; safe to start uvicorn |
| `TOOLS_PREFLIGHT:PASS mode=standalone` | No split env set; starting with default config |
| `TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING` | `NOVAIC_TOOLS_SERVER_SPLIT_REPO` path not on disk |
| `TOOLS_PREFLIGHT_ERROR:MAIN_TOOLS_MISSING` | `main_tools.py` absent inside split repo dir |
| `TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING` | `NOVAIC_GATEWAY_URL` not injected by Tauri |
| `TOOLS_PREFLIGHT_FAIL_CLOSED:PASS` | Fail-closed guard triggered correctly (test) |
| `TOOLS_PREFLIGHT_HAPPY_PATH:PASS` | Full happy-path preflight passed (test) |
| `TOOLS_SPLIT_BASELINE:PASS` | probe-preflight + leak-probe + pytest all green |
| `TOOLS_CANONICAL_URL:PASS` | Remote URL is canonical `file:///…/.git` |

---

## Common failure → fix table

| Symptom | Error marker | Fix |
|---------|-------------|-----|
| Tauri log: `SPLIT_PATH_MISSING` | `TOOLS_PREFLIGHT_ERROR:SPLIT_PATH_MISSING` | Set `NOVAIC_TOOLS_SERVER_SPLIT_REPO` to correct abs path |
| Tauri log: `GATEWAY_URL_MISSING` | `TOOLS_PREFLIGHT_ERROR:GATEWAY_URL_MISSING` | Ensure Tauri injects `NOVAIC_GATEWAY_URL` at spawn |
| pytest failures | — | Run `bash scripts/tools/ci_preflight_probe_prereqs.sh` first |
| leak-probe fd delta > 0 | `[leak-probe] FAIL` | Check for unclosed file handles in executor.py |
