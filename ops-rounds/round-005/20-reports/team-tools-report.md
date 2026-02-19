# Round 005 Report - Tools Team

## 11:00 Blocker Sync
- blocker_status: NONE
- note: No execution blocker during this cycle.

## Task Ledger
- task: Add fallback behavior or explicit fail-fast message when `lsof/pgrep` missing
  owner: Tools Team
  due: 2026-02-25 18:00
  status: DONE
  evidence:
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: `PASS`; script now fail-fast checks `lsof`, `pgrep`, `python3` before probe run.
  - artifact_paths:
    - `novaic-backend/scripts/tools/leak_probe.sh`
  - doc_paths:
    - `ops-rounds/round-005/20-reports/team-tools-report.md`
  dependencies:
  - host utility availability (`lsof`, `pgrep`, `python3`)
  risk_level: medium

- task: Add CI preflight step for probe prerequisites
  owner: Tools Team
  due: 2026-02-25 18:00
  status: DONE
  evidence:
  - command: `pytest -q tests/unit/common/test_strict_config.py`
  - result_summary: `3 passed`
  - CI_change_summary: added `Preflight probe prerequisites (Round 005)` step in Python CI job to ensure/install `lsof` and `pgrep`.
  - artifact_paths:
    - `.github/workflows/ci.yml`
    - `novaic-backend/tests/unit/common/test_strict_config.py`
  - doc_paths:
    - `ops-rounds/round-005/20-reports/team-tools-report.md`
  dependencies:
  - root CI workflow permissions and Ubuntu package mirror reachability
  risk_level: medium

- task: Run one high-concurrency replay and publish deterministic bound evidence
  owner: Tools Team
  due: 2026-02-25 18:00
  status: DONE
  evidence:
  - replay_timestamp: `2026-02-19 11:10:46 CST`
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - result_summary: `5 passed`
  - deterministic_bound_summary: includes high-concurrency variant (`80 calls`, semaphore limit `5`, observed `max_running <= 5`)
  - command: `which lsof && which pgrep`
  - result_summary: `/usr/sbin/lsof`, `/usr/bin/pgrep`
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: `PASS`, `fd delta=0`, `leaked=[]`
  - artifact_paths:
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
    - `novaic-backend/tests/unit/tools_server/test_reliability_policy.py`
    - `novaic-backend/scripts/tools/leak_probe.sh`
  - doc_paths:
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md`
    - `ops-rounds/round-005/20-reports/team-tools-report.md`
  dependencies:
  - deterministic async scheduler behavior for semaphore-bound tests
  risk_level: medium

## Gate Mapping
- Gate A: All DONE items have runnable command evidence + result summary.
- Gate D (Tools scope): Reliability replay remains green with prerequisite checks standardized.

## Decision Needed
- issue: Should Tools additionally implement a Python-only fallback mode (when `lsof/pgrep` absent) or keep strict fail-fast + CI preflight as the long-term standard?
- options:
  - Option A: keep current strict fail-fast + CI preflight (implemented now).
  - Option B: add Python fallback path for broader host compatibility.
- recommendation: Option A for no-tech-debt determinism; revisit Option B only if we add non-Linux/non-standard runners.
- impact: Option A keeps behavior predictable and maintenance low; Option B improves portability but adds test matrix and maintenance cost.
- owner: Tools Team
- decision_deadline: 2026-02-20 18:00 CST

## Self Status
- status: DONE
