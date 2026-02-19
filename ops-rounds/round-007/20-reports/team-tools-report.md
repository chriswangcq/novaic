# Round 007 Report - Tools Team

## 11:00 Blocker Sync
- blocker_status: NONE
- note: No external dependency blocker; all three mandatory tasks executed and verified same day.

## Task Ledger

---

- task: Finalize policy choice for non-Linux runner handling (A/B/C from Round 006)
  owner: Tools Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
  - policy_decision: Option A finalized — Ubuntu/Debian Linux CI + macOS local dev.
  - implementation_artifacts:
    - `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh` — policy block added to file header (lines 4–24)
    - `novaic-backend/scripts/tools/leak_probe.sh` — policy block added to file header (lines 4–22)
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md` — new section "Environment Dependency Policy" added with decision table, rules, rationale, and review trigger
  - command: `grep -n "Policy Choice" novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh novaic-backend/scripts/tools/leak_probe.sh novaic-backend/tools_server/RELIABILITY_POLICY.md`
  - result_summary: Policy block present in all three files; decision text and review trigger confirmed.
  dependencies:
  - Round 006 Decision Needed record in `ops-rounds/round-006/20-reports/team-tools-report.md`
  risk_level: low

---

- task: Reflect chosen policy in script/docs/CI comments
  owner: Tools Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
  - command: `DRY_RUN=1 SIMULATE_MISSING_CMDS=lsof,pgrep bash scripts/tools/ci_preflight_probe_prereqs.sh`
  - result_summary: `PASS` — detected both missing, queued `sudo apt-get update`, queued installs, exited cleanly without executing
  - command: `bash scripts/tools/ci_preflight_probe_prereqs.sh`
  - result_summary: `PASS` — `lsof: /usr/sbin/lsof`, `pgrep: /usr/bin/pgrep`
  - artifact_paths:
    - `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh`
    - `novaic-backend/scripts/tools/leak_probe.sh`
    - `novaic-backend/tools_server/RELIABILITY_POLICY.md`
    - `.github/workflows/ci.yml`
  dependencies:
  - bash, macOS native lsof/pgrep
  risk_level: low

---

- task: Replay leak probe + reliability suite with timestamped evidence
  owner: Tools Team
  due: 2026-02-23 18:00
  status: DONE
  evidence:
  - replay_timestamp: `2026-02-19 11:38:38 CST`
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: `PASS` — `loops=150`, `fd delta=0`, `leaked=[]`
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - result_summary: `5 passed`
  - high_concurrency_bound: `test_call_tool_enforces_runtime_semaphore_high_concurrency_variant` — 80 calls, semaphore 5, `max_running <= 5`
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
  - Python 3.13, pytest, asyncio, lsof, pgrep
  risk_level: low

---

## Gate Mapping
- Gate A: All DONE items have exact command + pass summary + artifact path.
- Gate D (Tools scope): Environment dependency policy finalized in code/docs/CI; replay remains green.

## Decision Needed
- issue: Policy Option A is now documented and enforced. Only residual risk is an undocumented path where a new non-Linux CI runner is added without updating the preflight script first.
- options:
  - Option A: Add a CI-level lint/check that verifies `ci_preflight_probe_prereqs.sh` mentions any runner type listed in `ci.yml`.
  - Option B: Accept current state; rely on PR review to catch runner additions.
- recommendation: Option B for now — runner matrix changes are rare, high-visibility, and reviewed. Option A adds tooling overhead with minimal practical gain.
- impact: Low risk; policy comment in script + RELIABILITY_POLICY.md serves as the human-readable gate.
- owner: Tools Team
- decision_deadline: 2026-02-23 18:00 CST

## Self Status
- status: DONE
