# Round 006 Report - Tools Team

## 11:00 Blocker Sync
- blocker_status: NONE
- note: No execution blocker this cycle; all three mandatory tasks completed same day.

## Task Ledger

- task: Replay leak probe and reliability test bundle with timestamp
  owner: Tools Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
  - replay_timestamp: `2026-02-19 11:32:18 CST`
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: `PASS` — `loops=150`, `fd delta=0`, `leaked=[]`
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - result_summary: `5 passed`
  - high_concurrency_variant: `test_call_tool_enforces_runtime_semaphore_high_concurrency_variant` — `80 calls`, semaphore `5`, observed `max_running <= 5`
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
  - Python 3.13, pytest, asyncio
  risk_level: low

- task: Verify CI prerequisite step behavior on clean runner assumptions
  owner: Tools Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
  - command: `bash scripts/tools/ci_preflight_probe_prereqs.sh`
  - result_summary: `PASS` — `lsof: /usr/sbin/lsof`, `pgrep: /usr/bin/pgrep`
  - command: `DRY_RUN=1 SIMULATE_MISSING_CMDS=lsof,pgrep bash scripts/tools/ci_preflight_probe_prereqs.sh`
  - result_summary: preflight detects both missing, queues `sudo apt-get update` + install, exits PASS under dry-run (install not executed)
  - CI_change_summary: Python CI job now calls `bash scripts/tools/ci_preflight_probe_prereqs.sh`; inline bash block replaced by versioned replayable script
  - artifact_paths:
    - `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh`
    - `.github/workflows/ci.yml`
  - doc_paths:
    - `ops-rounds/round-006/20-reports/team-tools-report.md`
  dependencies:
  - `sudo apt-get` available on runner (standard `ubuntu-latest`)
  risk_level: medium

- task: Document remaining host dependency caveats with explicit mitigation
  owner: Tools Team
  due: 2026-02-24 18:00
  status: DONE
  evidence:
  - caveat_summary:
    - `lsof` — fd counting; mitigated via `ci_preflight_probe_prereqs.sh` auto-install on Linux CI
    - `pgrep` — child process tracking; same mitigation
    - `python3` — probe main body; fail-fast check added in `leak_probe.sh` header
    - macOS local dev — `lsof`/`pgrep` natively present; preflight skips install branch
    - Non-Linux CI runners — not currently used; would require OS-branch extension in preflight script
  - artifact_paths:
    - `novaic-backend/scripts/tools/leak_probe.sh`
    - `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh`
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md`
  dependencies:
  - NONE beyond existing files
  risk_level: medium

## Gate Mapping
- Gate A: All DONE items have exact commands, pass/fail summary, artifact/doc paths.
- Gate D (Tools scope): Reliability replay remains green; prerequisite checks now in versioned script, not inline CI bash.

## Decision Needed
- issue: `ci_preflight_probe_prereqs.sh` handles only Ubuntu/Debian (`apt-get`). If a non-Linux runner is added, install branch becomes no-op and probe may fail silently.
- options:
  - Option A: Keep Ubuntu-only; document macOS/Windows as unsupported for probe CI (zero cost now).
  - Option B: Add OS detection + Homebrew/Chocolatey branches.
  - Option C: Replace OS-level probes with Python-only fallback in `leak_probe.sh`.
- recommendation: Option A now — no non-Linux runners exist; revisit only if runner matrix changes.
- impact: Option A is zero-cost and zero-risk today; avoids unnecessary complexity.
- owner: Tools Team
- decision_deadline: 2026-02-24 18:00 CST

## Self Status
- status: DONE
