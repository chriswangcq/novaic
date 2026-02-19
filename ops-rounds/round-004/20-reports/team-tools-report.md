# Round 004 Report - Tools Team

## 11:00 Blocker Sync
- blocker_status: NONE
- note: No blocking dependency found for Tools mandatory tasks.

## Task Ledger
- task: Re-run leak probe and reliability test bundle
  owner: Tools Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
  - replay_timestamp: `2026-02-19 10:50:29 CST`
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: `PASS`, `fd delta=0`, `leaked child processes=[]`
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - result_summary: `5 passed`
  - command: `pytest -q tests/unit/common/test_strict_config.py`
  - result_summary: `3 passed`
  - artifact_paths:
    - `novaic-backend/scripts/tools/leak_probe.sh`
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
    - `novaic-backend/tests/unit/tools_server/test_reliability_policy.py`
    - `novaic-backend/tests/unit/common/test_strict_config.py`
  - doc_paths:
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md`
  dependencies:
  - `ops-rounds/round-004/10-dispatch/team-tools.md`
  risk_level: medium

- task: Provide one replay run output with timestamp
  owner: Tools Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
  - command: `date '+%Y-%m-%d %H:%M:%S %Z'`
  - result_summary: `2026-02-19 10:50:29 CST`
  - replay_commands:
    - `bash scripts/tools/leak_probe.sh`
    - `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - artifact_paths:
    - `ops-rounds/round-004/20-reports/team-tools-report.md`
  - doc_paths:
    - `ops-rounds/round-004/10-dispatch/team-tools.md`
  dependencies:
  - local shell and test runner availability
  risk_level: low

- task: Report environment prerequisites that may cause false negatives
  owner: Tools Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
  - command: `which lsof && which pgrep`
  - result_summary: `/usr/sbin/lsof`, `/usr/bin/pgrep`
  - prerequisites:
    - `lsof` required by `scripts/tools/leak_probe.sh` for fd counting
    - `pgrep` required by `scripts/tools/leak_probe.sh` for child process checks
    - Python runtime with test dependencies (`pytest`) required for replay tests
  - artifact_paths:
    - `novaic-backend/scripts/tools/leak_probe.sh`
    - `.github/workflows/ci.yml`
  - doc_paths:
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md`
  dependencies:
  - host utilities (`lsof`, `pgrep`) on runner image
  risk_level: medium

## Gate Mapping
- Gate A: Mandatory command evidence attached for all DONE items.
- Gate D (Tools scope): Reliability replay remains green and reproducible.

## Decision Needed
- issue: `leak_probe.sh` depends on host tools (`lsof`, `pgrep`); minimal CI images without these may produce false negatives.
- options:
  - Keep current script and document host prerequisites.
  - Add fallback path in script using Python-only process inspection when host tools are unavailable.
  - Pin CI job image and install `lsof` explicitly before probe execution.
- recommendation: Pin CI prerequisites (install/check `lsof` + `pgrep`) and keep current probe logic for deterministic results.
- impact: Without this decision, probe reliability may vary by environment and create intermittent red runs.

## Self Status
- status: DONE
