# Round 008 Report - Tools Team

## 11:00 Blocker Sync
- blocker_status: NONE
- note: All three mandatory tasks executed and verified within the round window.

## Task Ledger

---

### Task 1 — Publish final policy statement for runner OS support and fallback strategy
- owner: Tools Team
- due: 2026-02-23 18:00
- status: DONE
- evidence:
  - action: Created `novaic-backend/scripts/tools/RUNNER_SUPPORT_POLICY.md` as the
    single, stable, non-round-specific policy document.
  - command: `ls -la novaic-backend/scripts/tools/RUNNER_SUPPORT_POLICY.md`
  - result_summary: File present; contains policy version `v1.0.0`, owner, review trigger,
    supported-environment table, Option A rationale, non-Linux expansion path, long-term
    maintenance rules, and cross-references to all related files.
  - artifact_path: `novaic-backend/scripts/tools/RUNNER_SUPPORT_POLICY.md`
  - policy_version: v1.0.0 (finalized 2026-02-19)
  - cross_references_in_policy_doc:
    - `tools_server/RELIABILITY_POLICY.md`
    - `scripts/tools/ci_preflight_probe_prereqs.sh`
    - `tests/unit/tools_server/test_policy_doc_sync.py`
    - `.github/workflows/ci.yml`
  - also_updated:
    - `scripts/tools/ci_preflight_probe_prereqs.sh` — replaced round-report reference
      with stable doc references (`RUNNER_SUPPORT_POLICY.md`, `RELIABILITY_POLICY.md`)
- risk_level: low

---

### Task 2 — Keep reliability replay green and attach timestamped evidence
- owner: Tools Team
- due: 2026-02-23 18:00
- status: DONE
- evidence:
  - replay_timestamp: `2026-02-19 11:50:11 CST`
  - command: `bash scripts/tools/ci_preflight_probe_prereqs.sh`
  - result_summary: PASS — `lsof: /usr/sbin/lsof`, `pgrep: /usr/bin/pgrep`
  - command: `bash scripts/tools/leak_probe.sh`
  - result_summary: PASS — `loops=150`, `fd_before=44`, `fd_after=44`, `delta=0`, `leaked=[]`
  - command: `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
  - result_summary: 5 passed
  - artifact_paths:
    - `novaic-backend/scripts/tools/leak_probe.sh`
    - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
    - `novaic-backend/tests/unit/tools_server/test_reliability_policy.py`
- risk_level: low

---

### Task 3 — Add one verification that CI preflight script and policy doc stay in sync
- owner: Tools Team
- due: 2026-02-23 18:00
- status: DONE
- evidence:
  - action: Created `tests/unit/tools_server/test_policy_doc_sync.py` with 8 assertions
    covering key policy tokens across all three canonical files:
    - `scripts/tools/RUNNER_SUPPORT_POLICY.md`
    - `tools_server/RELIABILITY_POLICY.md`
    - `scripts/tools/ci_preflight_probe_prereqs.sh`
  - verified_tokens: `Option A`, `Ubuntu`, `Non-Linux`, cross-reference presence
  - command: `pytest -q tests/unit/tools_server/test_policy_doc_sync.py`
  - result_summary: 8 passed (timestamp `2026-02-19 11:50:11 CST`)
  - artifact_path: `novaic-backend/tests/unit/tools_server/test_policy_doc_sync.py`
  - note: This test is a CI gate — if any file drifts from the others, the test fails
    and forces the author to re-align all three files.
- risk_level: low

---

## Gate Mapping
- Gate A: All three DONE items have exact commands, pass summaries, and artifact paths.
- Gate D (Tools scope): Repeatable replay checks green; policy-aligned defaults
  confirmed; sync-check test added as CI gate.

## Decision Needed
- issue: Sync-check test was not yet wired into `.github/workflows/ci.yml` as a named step.
- resolution: RESOLVED — Option A implemented in same round.
- command: `grep -A2 "Policy sync check" .github/workflows/ci.yml`
- result_summary: Step `Policy sync check (Tools runner support)` added to `python` job,
  running `pytest -q tests/unit/tools_server/test_policy_doc_sync.py`
- artifact_path: `.github/workflows/ci.yml`
- owner: Tools Team
- decision_deadline: 2026-02-23 18:00 CST (resolved 2026-02-19)

## Final Handoff Inventory

All deliverables are in stable, non-round-specific paths:

| Artifact | Path | Status |
|----------|------|--------|
| Runner support policy (v1.0.0) | `novaic-backend/scripts/tools/RUNNER_SUPPORT_POLICY.md` | FINAL |
| Full reliability policy | `novaic-backend/tools_server/RELIABILITY_POLICY.md` | FINAL |
| Policy sync-check test | `novaic-backend/tests/unit/tools_server/test_policy_doc_sync.py` | ACTIVE CI GATE |
| Leak probe script | `novaic-backend/scripts/tools/leak_probe.sh` | STABLE |
| CI preflight script | `novaic-backend/scripts/tools/ci_preflight_probe_prereqs.sh` | STABLE |
| Reliability controls test | `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py` | ACTIVE CI GATE |
| Policy unit test | `novaic-backend/tests/unit/tools_server/test_reliability_policy.py` | ACTIVE CI GATE |
| Strict config test | `novaic-backend/tests/unit/common/test_strict_config.py` | ACTIVE CI GATE |
| Config schema | `novaic-backend/config/services.schema.json` | STABLE |
| Config values | `novaic-backend/config/services.json` | STABLE |

## Self Status
- status: DONE
