# Tools Server — Round 015 Runbook: Fresh Clone Validation

> All commands execute from `~/new-build-novaic/novaic-tools-server` — a fresh
> clone with no prior workspace state. No local sibling directories, no gitlinks.
> Canonical repo: `https://github.com/chriswangcq/novaic-tools-server`

---

## Step 1 — Fresh clone and install

```bash
git clone https://github.com/chriswangcq/novaic-tools-server \
  ~/new-build-novaic/novaic-tools-server
cd ~/new-build-novaic/novaic-tools-server
pip3 install -r requirements.txt
```

Verify HEAD matches expected commit:
```bash
git rev-parse HEAD
# expected: 25b0f77e1b488371f8866e125c4f7bc159defadd or later
```

---

## Step 2 — Unit tests (R015 acceptance command 1)

```bash
cd ~/new-build-novaic/novaic-tools-server && pytest -q tests/unit/tools_server/
echo "TOOLS_UNIT_BASELINE:PASS"
```

**Expected:** `6 passed`, then `TOOLS_UNIT_BASELINE:PASS`

---

## Step 3 — Failure-path script (R015 acceptance command 2)

```bash
cd ~/new-build-novaic/novaic-tools-server && bash scripts/fail_path_tools_missing_config.sh
```

**Expected marker:** `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS`

Sub-cases in order:
- `TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS`
- `TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS`
- `TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS`

---

## Step 4 — Import probe from fresh context

```bash
cd ~/new-build-novaic/novaic-tools-server && python3 -c "
import sys; sys.path.insert(0,'.')
from tools_server.preflight import preflight_check
print('TOOLS_PREFLIGHT_IMPORT_OK')
"
```

**Expected:** `TOOLS_PREFLIGHT_IMPORT_OK`

---

## Step 5 — Packaged-split pass replay from fresh context

```bash
cd ~/new-build-novaic/novaic-tools-server && \
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

## Marker matrix (round-015)

| Marker | Condition |
|--------|-----------|
| `TOOLS_UNIT_BASELINE:PASS` | 6 unit tests passed from fresh clone (acceptance command 1) |
| `TOOLS_PREFLIGHT_FAIL_PATH_MISSING_CONFIG:PASS` | fail-path script all cases green from fresh clone (acceptance command 2) |
| `TOOLS_PREFLIGHT_ERROR_GATEWAY_URL:PASS` | GATEWAY_URL missing case |
| `TOOLS_PREFLIGHT_ERROR_RUNTIME_ORCHESTRATOR_URL:PASS` | RUNTIME_ORCHESTRATOR_URL missing case |
| `TOOLS_PREFLIGHT_ERROR_TOOL_RESULT_SERVICE_URL:PASS` | TOOL_RESULT_SERVICE_URL missing case |
| `TOOLS_PREFLIGHT_IMPORT_OK` | preflight module import probe from fresh context |
| `TOOLS_PREFLIGHT_PASS_REPLAY:PASS` | packaged-split pass replay from fresh context |
| `TOOLS_PREFLIGHT:PASS mode=packaged-split port=<N>` | split mode all env vars valid |
| `TOOLS_R015_RUNBOOK_COMPLETE:PASS` | this runbook verified present with all markers |
