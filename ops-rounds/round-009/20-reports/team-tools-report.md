# Round 009 Report - Tools Team

## 11:00 Blocker Sync
- blocker_status: NONE
- note: All three mandatory tasks completed within round window. No external dependencies.

## Task Ledger

---

### Task 1 — Add CI check to ensure runner policy doc and preflight script stay synchronized
- owner: Tools Team
- due: 2026-02-24 18:00
- status: DONE
- evidence:
  - context: `test_policy_doc_sync.py` was created in Round 008 with 8 token-consistency
    tests and wired into CI. This round extends it with 3 additional runbook checks.
  - new_assertions_added:
    - `test_operator_runbook_exists` — fails if `OPERATOR_RUNBOOK.md` is missing
    - `test_operator_runbook_references_leak_probe` — fails if runbook omits `leak_probe`
    - `test_operator_runbook_references_reliability_policy` — fails if runbook omits `RELIABILITY_POLICY`
  - command: `pytest -q tests/unit/tools_server/test_policy_doc_sync.py`
  - result_summary: 11 passed (timestamp `2026-02-19 11:59:16 CST`)
  - artifact_path: `novaic-backend/tests/unit/tools_server/test_policy_doc_sync.py`
  - ci_step: `Policy sync check (Tools runner support)` in `.github/workflows/ci.yml`
    (wired in Round 008; confirmed still present)
- risk_level: low

---

### Task 2 — Replay leak probe + reliability suite with timestamped evidence
- owner: Tools Team
- due: 2026-02-24 18:00
- status: DONE
- evidence:
  - replay_timestamp: `2026-02-19 11:59:16 CST`
  - command: `bash scripts/tools/ci_preflight_probe_prereqs.sh`
  - result_summary: PASS — `lsof: /usr/sbin/lsof`, `pgrep: /usr/bin/pgrep`
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: PASS — `loops=150`, `fd_before=44`, `fd_after=44`, `delta=0`, `leaked=[]`
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - result_summary: 5 passed
  - full_suite_command: `pytest -q tests/unit/tools_server/ tests/unit/common/test_strict_config.py`
  - full_suite_result: 44 passed (all tools_server + strict_config tests green)
  - artifact_paths:
    - `novaic-backend/scripts/tools/leak_probe.sh`
    - `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh`
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
    - `novaic-backend/tests/unit/tools_server/test_reliability_policy.py`
- risk_level: low

---

### Task 3 — Publish final support statement for non-Linux runner strategy
- owner: Tools Team
- due: 2026-02-24 18:00
- status: DONE
- evidence:
  - action: Created `novaic-backend/tools_server/OPERATOR_RUNBOOK.md` — the final
    handoff-ready operations document.  Contains:
    - Service overview
    - Step-by-step reliability checks (§2) with exact commands and expected outputs
    - Configuration reference table (§3)
    - Incident response procedures (§4) for common failure modes
    - Runner OS support summary table (§5) cross-referencing `RUNNER_SUPPORT_POLICY.md`
    - Escalation path (§6)
    - Complete related files index (§7)
  - command: `grep "FINAL_FOR_OPERATIONS\|Version:" novaic-backend/tools_server/OPERATOR_RUNBOOK.md | head -2`
  - result_summary: `Status: FINAL_FOR_OPERATIONS`, `Version: v1.0.0 (2026-02-19)`
  - artifact_path: `novaic-backend/tools_server/OPERATOR_RUNBOOK.md`
  - support_statement_location: §5 "Runner OS Support Policy (Summary)" + cross-ref to
    `scripts/tools/RUNNER_SUPPORT_POLICY.md` (v1.0.0 FINAL, created Round 008)
  - non_linux_strategy: Fail-fast with explicit error; expansion path documented in
    `RUNNER_SUPPORT_POLICY.md` §4 and runbook §5.
- risk_level: low

---

## Gate Mapping
- Gate A: All DONE items have exact commands, pass summaries, and artifact paths.
- Gate B: No mandatory policy depends on round-only files. All canonical docs are in stable
  paths under `novaic-backend/scripts/tools/` and `novaic-backend/tools_server/`.
- Gate D (Tools scope): Relay checks run in stable CI flow; policy-aligned defaults confirmed;
  operator runbook published for long-term operations.

## Decision Needed
- issue: None. All previously open decision items have been resolved and implemented.
  The sync-check test now covers runbook existence as a CI gate, closing the last
  known governance gap.
- owner: Tools Team
- decision_deadline: N/A

## Final Handoff Inventory

All deliverables are in stable, non-round-specific paths and covered by CI gates:

| Artifact | Path | CI Gate | Status |
|----------|------|---------|--------|
| Operator runbook | `novaic-backend/tools_server/OPERATOR_RUNBOOK.md` | `test_policy_doc_sync.py` | FINAL_FOR_OPERATIONS |
| Runner support policy | `novaic-backend/scripts/tools/RUNNER_SUPPORT_POLICY.md` | `test_policy_doc_sync.py` | v1.0.0 FINAL |
| Full reliability policy | `novaic-backend/tools_server/RELIABILITY_POLICY.md` | `test_policy_doc_sync.py` | FINAL |
| Policy sync-check test | `novaic-backend/tests/unit/tools_server/test_policy_doc_sync.py` | CI named step | ACTIVE (11 assertions) |
| Leak probe | `novaic-backend/scripts/tools/leak_probe.sh` | Direct CI run | STABLE |
| CI preflight script | `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh` | Direct CI run | STABLE |
| Reliability controls test | `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py` | pytest | ACTIVE |
| Policy unit test | `novaic-backend/tests/unit/tools_server/test_reliability_policy.py` | pytest | ACTIVE |
| Strict config test | `novaic-backend/tests/unit/common/test_strict_config.py` | CI named step | ACTIVE |
| Config schema | `novaic-backend/config/services.schema.json` | strict_config | STABLE |
| Config values | `novaic-backend/config/services.json` | strict_config | STABLE |

## Self Status
- status: DONE
