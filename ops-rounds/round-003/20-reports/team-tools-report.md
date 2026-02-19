# Round 003 Report - Tools Team

## 11:00 Blocker Sync
- blocker_status: NONE
- note: No dependency blocker on Tools mandatory tasks; execution proceeded on schedule.

## Task Ledger (Mandatory)
- task: Re-run leak probe and reliability tests; refresh evidence
  owner: Tools Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: `PASS`, `fd delta=0`, `leaked child processes=[]`
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - result_summary: `5 passed`
  - artifact_paths:
    - `novaic-backend/scripts/tools/leak_probe.sh`
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
    - `novaic-backend/tests/unit/tools_server/test_reliability_policy.py`
  - doc_paths:
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md`
  dependencies:
  - `ops-rounds/round-003/10-dispatch/team-tools.md`
  - `ops-rounds/round-003/00-control/gate-criteria.md`
  risk_level: medium

- task: Add one stress variant with higher concurrency and report max_running bound
  owner: Tools Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py`
  - result_summary: includes `test_call_tool_enforces_runtime_semaphore_high_concurrency_variant`
  - stress_profile: `80 concurrent calls`, semaphore limit `5`
  - measured_bound: `max_running <= 5`
  - artifact_paths:
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
  - doc_paths:
    - `ops-rounds/round-003/20-reports/team-tools-report.md`
  dependencies:
  - runtime semaphore isolation in `novaic-backend/tools_server/runtime_manager.py`
  risk_level: medium

- task: Ensure reliability config schema checks run in CI path
  owner: Tools Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
  - command: `pytest -q tests/unit/common/test_strict_config.py`
  - result_summary: `3 passed`
  - CI_change_summary: added strict-config pytest step in Python CI job
  - artifact_paths:
    - `.github/workflows/ci.yml`
    - `novaic-backend/config/services.schema.json`
    - `novaic-backend/common/strict_config.py`
    - `novaic-backend/common/config.py`
  - doc_paths:
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md`
  dependencies:
  - CI workflow availability at `.github/workflows/ci.yml`
  risk_level: low

## Gate Mapping
- Gate A: All mandatory tasks include runnable command evidence and pass summaries.
- Gate D (Tools scope): Reliability checks are reproducible with refreshed round-003 evidence.

## Self Status
- status: DONE
