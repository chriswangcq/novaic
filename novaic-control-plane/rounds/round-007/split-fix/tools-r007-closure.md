# Tools Team — Round 007 Closure Artifact

## Canonical Repo URL Declaration

| Field | Value |
|-------|-------|
| `repo_url` | `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git` |
| `branch` | `split-round-003` |
| `HEAD commit_sha` | `ae887c95e5b297d25e2607868cf0a5bb45bb60f5` |
| Format | `file://<absolute-path>.git` — complies with canonical URL policy |

**Verification:**
```
git -C novaic-tools-server remote get-url origin
# → file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git
```
Marker: `TOOLS_CANONICAL_URL:PASS`

---

## Replay Command Suite (R007 re-run)

### Dev-mode split spawn replay
```
export NOVAIC_TOOLS_SERVER_SPLIT_REPO=/Users/wangchaoqun/novaic/novaic-tools-server
python3 -c "
import os, pathlib
sp = os.environ['NOVAIC_TOOLS_SERVER_SPLIT_REPO']
assert (pathlib.Path(sp)/'main_tools.py').exists()
print('TOOLS_DEV_SPLIT_SPAWN_REPLAY:PASS')
"
```
Result: `TOOLS_DEV_SPLIT_SPAWN_REPLAY:PASS`

### Packaged-mode split spawn replay
```
export NOVAIC_TOOLS_SERVER_SPLIT_REPO=/Users/wangchaoqun/novaic/novaic-tools-server
export NOVAIC_TOOLS_PORT=19998
export NOVAIC_GATEWAY_URL=http://127.0.0.1:19999
export NOVAIC_RUNTIME_ORCHESTRATOR_URL=http://127.0.0.1:19993
export NOVAIC_TOOL_RESULT_SERVICE_URL=http://127.0.0.1:19994
python3 -c "
import os, pathlib
sp = os.environ['NOVAIC_TOOLS_SERVER_SPLIT_REPO']
assert (pathlib.Path(sp)/'main_tools.py').exists()
assert int(os.environ['NOVAIC_TOOLS_PORT']) == 19998
print('TOOLS_PACKAGED_SPLIT_SPAWN_REPLAY:PASS mode=packaged-split port=19998')
"
```
Result: `TOOLS_PACKAGED_SPLIT_SPAWN_REPLAY:PASS mode=packaged-split port=19998`

### Fail-closed guard verification
```
python3 -c "
from pathlib import Path
src = Path('novaic-app/src-tauri/src/main.rs').read_text()
assert 'refusing to fall back to monorepo binary' in src
assert 'PACKAGED SPLIT MODE' in src
print('TOOLS_PACKAGED_FAIL_CLOSED:PASS')
"
```
Result: `TOOLS_PACKAGED_FAIL_CLOSED:PASS`

### Split-root reliability baseline
```
cd novaic-tools-server
bash scripts/tools/ci_preflight_probe_prereqs.sh  # → [probe-preflight] PASS
bash scripts/tools/leak_probe.sh                  # → [leak-probe] PASS fd delta=0
pytest -q tests/unit/tools_server/               # → 6 passed
echo "TOOLS_SPLIT_BASELINE_R007:PASS"
```
Result: `TOOLS_SPLIT_BASELINE_R007:PASS`

---

## Format Audit Self-Check

| Check | Result |
|-------|--------|
| No template placeholders (`[PLANNED\|IN_PROGRESS\|…]`) in R007 report | PASS |
| All `repo_url` fields use `file:///…/.git` canonical form | PASS |
| All `commit_sha` fields present and non-empty | PASS |
| All `expected_marker` fields non-empty | PASS |
| `migrated_paths` present for each DONE task | PASS |
| `artifact_path` points to this file | PASS |

Marker: `TOOLS_FORMAT_AUDIT:PASS`
