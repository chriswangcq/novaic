# Tools Server — Operator Runbook

**Status: FINAL_FOR_OPERATIONS**
**Version: v1.0.0 (2026-02-19)**
**Owner: Tools Team**
**Review trigger: any change to timeout policy, runner matrix, or CI pipeline**

---

## 1. Service Overview

The Tools Server (`tools_server/`) handles all tool-call execution for agent runtimes.
It exposes a FastAPI HTTP API and enforces reliability controls (timeouts, concurrency
limits, resource cleanup) defined in `RELIABILITY_POLICY.md`.

Key processes at runtime:
- `main_novaic.py` or `tools_server/api.py` starts the FastAPI app.
- Each connected runtime gets a `RuntimeContext` with a per-runtime concurrency semaphore.
- `ToolExecutor` executes individual tool calls with layered timeout enforcement.

---

## 2. Reliability Checks (Daily / Pre-Deploy)

Run these three commands to verify the tools server reliability controls are intact.
All three must pass before marking a release ready.

### 2a. CI Preflight (Linux only)

```bash
bash scripts/tools/ci_preflight_probe_prereqs.sh
```

Expected output:
```
[probe-preflight] lsof already available
[probe-preflight] pgrep already available
[probe-preflight] PASS
```

On macOS: `lsof` and `pgrep` are native; script still passes. No install occurs.

### 2b. OS-level Leak Probe

```bash
bash scripts/tools/leak_probe.sh
```

Expected output:
```
[leak-probe] loops=150
[leak-probe] fd_before=N fd_after=N delta=0
[leak-probe] children_before=[] children_after=[] leaked=[]
[leak-probe] PASS
```

FAIL conditions:
- `fd delta > 3` → HTTP client connections leaking after timeout/cancel.
- `leaked=[...]` → child processes not cleaned up after tool execution.

### 2c. Unit + Policy Sync Tests

```bash
pytest -q \
  tests/unit/tools_server/test_api_reliability_controls.py \
  tests/unit/tools_server/test_reliability_policy.py \
  tests/unit/tools_server/test_policy_doc_sync.py \
  tests/unit/common/test_strict_config.py
```

Expected: **16 passed**

`test_policy_doc_sync.py` will fail if `RUNNER_SUPPORT_POLICY.md`,
`RELIABILITY_POLICY.md`, and `ci_preflight_probe_prereqs.sh` drift out of sync.

---

## 3. Configuration Reference

All reliability knobs live in `config/services.json` under `tools_reliability`:

| Key | Default | Effect |
|-----|---------|--------|
| `request_timeout_seconds` | `300.0` | API-level timeout per `call_tool` request |
| `execution_timeout_seconds` | `null` | Per-tool internal timeout (null = heartbeat governs) |
| `global_timeout_seconds` | `1800.0` | Hard cap applied to all execution timeouts |
| `max_concurrent_per_runtime` | `4` | Semaphore limit per RuntimeContext |

Override via environment variables (see `RELIABILITY_POLICY.md` §Timeout Layers).

---

## 4. Incident Response

### Symptom: Tool calls hanging indefinitely

1. Check `request_timeout_seconds` in `config/services.json` — should be ≤ 300.
2. Verify `global_timeout_seconds` is set (not null).
3. Confirm the heartbeat mechanism in the Task/Saga worker is active.

### Symptom: FD leak alert from probe (`fd delta > 3`)

1. Run probe manually: `bash scripts/tools/leak_probe.sh`
2. If confirmed: look for `httpx.AsyncClient` instances not closed on timeout path.
3. Reference: `tools_server/executor.py` — `_execute_impl` and `close()` method.

### Symptom: Too many concurrent tool calls saturating a runtime

1. Lower `max_concurrent_per_runtime` in `config/services.json`.
2. Restart the tools server process.
3. Long-term: profile which tool types are slowest and adjust per-tool timeouts.

### Symptom: `test_policy_doc_sync` fails in CI

1. A policy token (`Option A`, `Ubuntu`, `Non-Linux`) was removed from one file but
   not the others.
2. Fix: update all three files to agree, then re-run `pytest -q tests/unit/tools_server/test_policy_doc_sync.py`.

---

## 5. Runner OS Support Policy (Summary)

Full policy: `scripts/tools/RUNNER_SUPPORT_POLICY.md`

| Environment | Supported | Notes |
|-------------|-----------|-------|
| Ubuntu/Debian Linux (CI) | YES | Prereqs auto-installed by preflight script |
| macOS local dev | YES | Native `lsof`/`pgrep`, no install needed |
| Non-Linux CI runner | NO | Probe fails fast; extend preflight script first |

---

## 6. Escalation Path

| Issue type | First responder | Escalation |
|------------|-----------------|------------|
| Leak probe FAIL | Tools Team on-call | Review `executor.py` `close()` path |
| Config schema mismatch | Tools Team | `common/strict_config.py` validation error |
| Policy sync drift | PR author | Fix all three files, re-run sync check |
| Non-Linux runner added | Platform Team | Open issue, extend `ci_preflight_probe_prereqs.sh` |

---

## 7. Related Files

| File | Purpose |
|------|---------|
| `tools_server/RELIABILITY_POLICY.md` | Full reliability policy (timeout layers, isolation, cleanup) |
| `scripts/tools/RUNNER_SUPPORT_POLICY.md` | Runner OS support policy (v1.0.0 FINAL) |
| `scripts/tools/leak_probe.sh` | OS-level FD + process leak probe |
| `scripts/tools/ci_preflight_probe_prereqs.sh` | CI prereq installer (Linux) |
| `tools_server/reliability.py` | `ToolsReliabilityPolicy` dataclass + `from_env()` |
| `tools_server/executor.py` | `ToolExecutor` — timeout and cleanup logic |
| `tools_server/api.py` | FastAPI endpoint — semaphore + request timeout |
| `tools_server/runtime_manager.py` | `RuntimeContext` — per-runtime semaphore init |
| `config/services.json` | Runtime config values |
| `config/services.schema.json` | Config schema with `tools_reliability` section |
| `tests/unit/tools_server/test_api_reliability_controls.py` | API-level reliability tests |
| `tests/unit/tools_server/test_reliability_policy.py` | Policy unit tests |
| `tests/unit/tools_server/test_policy_doc_sync.py` | CI sync-check gate |
| `tests/unit/common/test_strict_config.py` | Config schema validation tests |
| `.github/workflows/ci.yml` | CI pipeline (includes policy sync check step) |
