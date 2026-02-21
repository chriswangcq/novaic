# Runtime Round 008 Replay Bundle

- repo: `file:///Users/wangchaoqun/split-remotes/novaic-runtime-orchestrator.git`
- branch: `split/round-003-runtime`
- commit_sha: `5ca53294b805808b49a88dceff4b75bdd33ef9a4`
- generated_at: 2026-02-20 (Round 008)

---

## Marker Table

| Script | Expected Marker | Status |
|---|---|---|
| `runtime_lifecycle_contract_guard_replay.sh` | `RUNTIME_CONTRACT_VERSION=v1` | PASS |
| `runtime_lifecycle_contract_guard_replay.sh` | `PASS: runtime lifecycle contract guard replay` | PASS |
| `runtime_lifecycle_contract_guard_replay.sh` | `PASS: RUNTIME_CONTRACT_VERSION=v1` | PASS |
| `runtime_lifecycle_failure_path_replay.sh` | `FAIL-MARKER: invalid-transition-cas-rejected` | PASS |
| `runtime_lifecycle_failure_path_replay.sh` | `PASS: failure-path replay confirmed CAS correctly rejects invalid lifecycle transition` | PASS |
| `runtime_startup_health_replay.sh` | `PASS: runtime-orchestrator startup from split repo root` | PASS |
| `runtime_startup_health_replay.sh` | `PASS: runtime health endpoint http://127.0.0.1:62993/api/health` | PASS |
| `pytest` contract + lifecycle suite | `6 passed, 2 skipped` | PASS |

---

## Success Path Replay

```
command: cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh
```

Actual output:
```
RUNTIME_CONTRACT_VERSION=v1
PASS: runtime lifecycle contract guard replay
PASS: contract runtime_id rt-2f161e1aacd9
PASS: RUNTIME_CONTRACT_VERSION=v1
```

```
command: cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_startup_health_replay.sh
```

Actual output:
```
PASS: runtime-orchestrator startup from split repo root
PASS: runtime health endpoint http://127.0.0.1:62993/api/health
```

```
command: cd /Users/wangchaoqun/novaic-runtime-orchestrator && pytest -q tests/contract/test_runtime_orchestrator_process_startup.py tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py
```

Actual output:
```
.ss.....
6 passed, 2 skipped in 0.90s
```

---

## Failure Path Replay

```
command: cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_failure_path_replay.sh
```

Actual output:
```
FAIL-MARKER: invalid-transition-cas-rejected (current_status=active)
PASS: failure-path replay confirmed CAS correctly rejects invalid lifecycle transition
```

### What is tested
- Runtime created at `active` status via `get-or-create`
- `POST /internal/runtimes/{id}/set-status` called with `expected_status=["completed"]`, `new_status="failed"`
- CAS check: current status is `active`, which is not in `["completed"]`, so update is rejected
- Idempotency short-circuit does not fire because `active` != `failed`
- Endpoint returns `{"success": false, "current_status": "active"}`
- Script asserts `success is False` and prints deterministic `FAIL-MARKER: invalid-transition-cas-rejected`

---

## Platform Self-Audit

```
command: cd /Users/wangchaoqun/novaic && python - <<'PY'
import re
from pathlib import Path
CANONICAL="file:///Users/wangchaoqun/split-remotes/"
issues=[]
for rpath in [
    "novaic-control-plane/rounds/round-005/20-reports/team-runtime-report.md",
    "novaic-control-plane/rounds/round-006/20-reports/team-runtime-report.md",
    "novaic-control-plane/rounds/round-007/20-reports/team-runtime-report.md",
]:
    t=Path(rpath).read_text(encoding="utf-8")
    for l in t.splitlines():
        if re.match(r"^\s*-\s+repo_url:\s*", l):
            v=re.sub(r"^\s*-\s+repo_url:\s*","",l).strip().strip("`")
            if v and not v.startswith(CANONICAL): issues.append(f"non-canonical: {rpath}: {v}")
        if re.match(r"^\s*-\s+status:\s*(PLANNED|PENDING)\s*$", l):
            issues.append(f"placeholder status: {rpath}: {l.strip()}")
    if "- status: DONE" not in t: issues.append(f"no DONE: {rpath}")
if issues:
    for i in issues: print("ISSUE:",i)
    raise SystemExit("runtime-round008-audit: FAIL")
print("runtime-round008-audit: PASS")
PY
```

Expected marker: `runtime-round008-audit: PASS`
Actual output: `runtime-round008-audit: PASS`

Note: The audit regex restricts `repo_url:` matching to YAML field lines only (`- repo_url:`), avoiding false positives from inline code blocks in prior-round reports.

---

## Operability Reference

| Asset | Path |
|---|---|
| Startup health replay | `scripts/runtime_startup_health_replay.sh` |
| Lifecycle contract guard (success) | `scripts/runtime_lifecycle_contract_guard_replay.sh` |
| Lifecycle contract guard (failure path) | `scripts/runtime_lifecycle_failure_path_replay.sh` |
| Config | `config/services.json` |
| Contract tests | `tests/contract/test_runtime_orchestrator_process_startup.py` |
| Lifecycle unit tests | `tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py` |
