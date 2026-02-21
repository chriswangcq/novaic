# Round 008 Report - Runtime Team

---

## Task 1 — code/behavior: contract-version marker in lifecycle guard

- problem_fixed: Guard script had no contract-version identifier in output; auditors could not confirm which contract version was exercised.
- solution_applied: Added `RUNTIME_CONTRACT_VERSION=v1` shell emission and `PASS: RUNTIME_CONTRACT_VERSION=v1` Python marker; added inline `assert contract_version == "v1"` so version drift hard-fails the script.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh`
  - expected_marker: `PASS: RUNTIME_CONTRACT_VERSION=v1`
  - actual_output: `RUNTIME_CONTRACT_VERSION=v1 / PASS: runtime lifecycle contract guard replay / PASS: contract runtime_id rt-2f161e1aacd9 / PASS: RUNTIME_CONTRACT_VERSION=v1`

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh`
- expected_marker: `PASS: RUNTIME_CONTRACT_VERSION=v1`
- repo_url: `file:///Users/wangchaoqun/split-remotes/novaic-runtime-orchestrator.git`
- branch: `split/round-003-runtime`
- commit_sha: `5ca53294b805808b49a88dceff4b75bdd33ef9a4`
- migrated_paths: `scripts/runtime_lifecycle_contract_guard_replay.sh`
- artifact_path: `novaic-control-plane/rounds/round-008/split-fix/runtime-round008-replay-bundle.md`
- status: `DONE`

---

## Task 2 — failure-path: invalid lifecycle transition negative replay

- problem_fixed: No failure-path replay existed; Gate C requires at least one negative case with a deterministic FAIL marker.
- solution_applied: Created `scripts/runtime_lifecycle_failure_path_replay.sh`; bootstraps active runtime then calls `set-status` with mismatched `expected_status=["completed"]` / `new_status="failed"` — CAS rejects because current is `active`; script asserts `success is False` and prints `FAIL-MARKER: invalid-transition-cas-rejected`.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_failure_path_replay.sh`
  - expected_marker: `FAIL-MARKER: invalid-transition-cas-rejected`
  - actual_output: `FAIL-MARKER: invalid-transition-cas-rejected (current_status=active) / PASS: failure-path replay confirmed CAS correctly rejects invalid lifecycle transition`

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_failure_path_replay.sh`
- expected_marker: `FAIL-MARKER: invalid-transition-cas-rejected`
- repo_url: `file:///Users/wangchaoqun/split-remotes/novaic-runtime-orchestrator.git`
- branch: `split/round-003-runtime`
- commit_sha: `5ca53294b805808b49a88dceff4b75bdd33ef9a4`
- migrated_paths: `scripts/runtime_lifecycle_failure_path_replay.sh`
- artifact_path: `novaic-control-plane/rounds/round-008/split-fix/runtime-round008-replay-bundle.md`
- status: `DONE`

---

## Task 3 — operability artifact: replay bundle with self-audit script

- problem_fixed: Task 3 `command` field previously contained `(see Target state proof above)` — a non-executable placeholder that fails machine-readable contract requirement.
- solution_applied: Created executable script `novaic-control-plane/rounds/round-008/split-fix/runtime-round008-self-audit.sh`; Task 3 command is now a single-line directly runnable `bash` invocation.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic && bash novaic-control-plane/rounds/round-008/split-fix/runtime-round008-self-audit.sh`
  - expected_marker: `runtime-round008-audit: PASS`
  - actual_output: `runtime-round008-audit: PASS`

- command: `cd /Users/wangchaoqun/novaic && bash novaic-control-plane/rounds/round-008/split-fix/runtime-round008-self-audit.sh`
- expected_marker: `runtime-round008-audit: PASS`
- repo_url: `file:///Users/wangchaoqun/split-remotes/novaic-runtime-orchestrator.git`
- branch: `split/round-003-runtime`
- commit_sha: `5ca53294b805808b49a88dceff4b75bdd33ef9a4`
- migrated_paths: `novaic-control-plane/rounds/round-008/split-fix/runtime-round008-self-audit.sh`
- artifact_path: `novaic-control-plane/rounds/round-008/split-fix/runtime-round008-replay-bundle.md`
- status: `DONE`

---

## questions_for_program_owner

- question: Should `RUNTIME_CONTRACT_VERSION` be bumped to `v2` when the lifecycle contract API changes, or is versioning handled at the OpenAPI spec level?
- why_blocking: Not blocking Round 008. Relevant for future rounds when contract fields evolve.
- options: (A) Bump shell variable per breaking change. (B) Read version from tracked `contract-version.json` and assert against it.
- recommended_option: Option B — avoids manual guard script edits and makes version drift detection automatic.
- impact_if_unanswered: Guard script remains pinned to `v1` and will not catch future contract drift without a manual update.
- requested_by_round: `round-008`

---

## Team status

- status: `DONE`
- blocker: none
- operability_artifact: `novaic-control-plane/rounds/round-008/split-fix/runtime-round008-replay-bundle.md`
