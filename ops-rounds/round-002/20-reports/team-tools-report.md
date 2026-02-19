# Round 002 Report - Tools Team

## Mission Alignment
- Focused on reliability controls for tool execution: timeout determinism, runtime-level isolation under load, and cleanup behavior on timeout/cancel.

## Task Ledger (File-Driven, Evidence Required)
- task: Timeout behavior tests for request/execution/global timeout layers  
  owner: Tools Team  
  due: 2026-02-26  
  status: DONE  
  evidence:
  - command: `pytest -q tests/unit/tools_server/test_reliability_policy.py tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_executor_qemu_contract.py`
  - pass_summary: `11 passed`
  - code_paths:
    - `novaic-backend/tools_server/reliability.py`
    - `novaic-backend/tools_server/api.py`
    - `novaic-backend/tools_server/executor.py`
    - `novaic-backend/tests/unit/tools_server/test_reliability_policy.py`
  dependencies:
  - `ops-rounds/governance/status-codes.md`
  - `ops-rounds/round-002/00-control/gate-criteria.md`
  risk_level: medium

- task: Runtime-level concurrency stress and queueing behavior capture  
  owner: Tools Team  
  due: 2026-02-26  
  status: DONE  
  evidence:
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py`
  - pass_summary: includes `test_call_tool_enforces_runtime_semaphore_under_load`
  - load_shape: `24 concurrent calls`, runtime semaphore `3`, observed `max_running <= 3`
  - code_paths:
    - `novaic-backend/tools_server/runtime_manager.py`
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
  dependencies:
  - Runtime context lifecycle in `tools_server/runtime_manager.py`
  risk_level: medium

- task: Cleanup verification for timeout/cancel leak prevention  
  owner: Tools Team  
  due: 2026-02-26  
  status: DONE  
  evidence:
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py`
  - checks:
    - timeout path returns deterministic failure
    - executor `close()` called on timeout path
    - executor `close()` called for each concurrent call (`close_count == 24`)
  - code_paths:
    - `novaic-backend/tools_server/api.py`
    - `novaic-backend/tools_server/executor.py`
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
  dependencies:
  - HTTP client lifecycle in `ToolExecutor.close()`
  risk_level: high

- task: Recommended production reliability defaults documentation  
  owner: Tools Team  
  due: 2026-02-26  
  status: DONE  
  evidence:
  - doc_path: `novaic-backend/tools_server/RELIABILITY_POLICY.md`
  - defaults:
    - `NOVAIC_TOOLS_REQUEST_TIMEOUT_SECONDS=300`
    - `NOVAIC_TOOLS_EXECUTION_TIMEOUT_SECONDS` unset by default
    - `NOVAIC_TOOLS_GLOBAL_TIMEOUT_SECONDS=1800`
    - `NOVAIC_TOOLS_MAX_CONCURRENT_PER_RUNTIME=4`
  dependencies:
  - Env-config conventions in backend services
  risk_level: low

- task: Redispatch closure - OS-level leak probe evidence  
  owner: Tools Team  
  due: 2026-02-22 18:00  
  status: DONE  
  evidence:
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: `PASS`, `fd delta=0`, `leaked child processes=[]`
  - artifact_path: `novaic-backend/scripts/tools/leak_probe.sh`
  - run_output_key_lines:
    - `[leak-probe] fd_before=44 fd_after=44 delta=0`
    - `[leak-probe] children_before=[] children_after=[] leaked=[]`
    - `[leak-probe] PASS`
  dependencies:
  - `lsof` and `pgrep` available on runner host
  risk_level: medium

- task: Redispatch closure - reliability config schema/startup integration  
  owner: Tools Team  
  due: 2026-02-22 18:00  
  status: DONE  
  evidence:
  - command: `pytest -q tests/unit/common/test_strict_config.py`
  - result_summary: `3 passed`
  - artifact_paths:
    - `novaic-backend/config/services.schema.json`
    - `novaic-backend/config/services.json`
    - `novaic-backend/common/strict_config.py`
    - `novaic-backend/common/config.py`
    - `novaic-backend/tools_server/reliability.py`
  - doc_path: `novaic-backend/tools_server/RELIABILITY_POLICY.md`
  dependencies:
  - strict config loader validation in `common/strict_config.py`
  risk_level: medium

## Gate Mapping
- Gate A (Build/Test): targeted tests passed (`11 passed` for tools reliability tests, `3 passed` for strict config tests).
- Gate D (Reliability): timeout determinism + concurrency isolation + cleanup + OS-level leak probe evidence are present and reproducible.
- Fail Conditions check: no missing evidence in DONE items under Tools scope.

## Risks / Gaps
- No open P0/P1 in Tools redispatch scope after today updates.
- Remaining round-level PASS dependency is cross-team P0 closure (Runtime, Storage-A/B).

## Next Steps
- Keep daily evidence refresh before 18:00 if code/test output changes.
- Support reviewer replay by preserving command reproducibility and output snippets.

## Self Status
- status: DONE
