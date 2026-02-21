# Round 009 Report - Storage-A/B Team

---

## Task 1 — code/behavior: Version and enforce Storage A/B interface contract

### problem_fixed
Storage-A and Storage-B health endpoints returned `{"status": "ok", "service": "..."}` with no versioned contract field. Consumers had no machine-checkable way to assert they were talking to the correct service version. Remote-first reproducibility guarantees required an explicit, testable interface contract marker.

### solution_applied
Added `contract_version` field to `/api/health` in both services:
- `novaic-storage-a/file_service/main.py`: health returns `"contract_version": "storage-a/v1"`
- `novaic-storage-b/tool_result_service/main.py`: health returns `"contract_version": "storage-b/v1"`

Created verification scripts that start each service, call `/api/health`, and assert the field is present and correctly valued:
- `novaic-storage-a/scripts/verify_contract_version_a.sh` → `STORAGE_A_CONTRACT_VERSION=PASS`
- `novaic-storage-b/scripts/verify_contract_version_b.sh` → `STORAGE_B_CONTRACT_VERSION=PASS`

Committed and verified.

### target_state_proof

- type: `code/behavior`
- repo_url: `https://github.com/chriswangcq/novaic-storage-a`
- repo_url: `https://github.com/chriswangcq/novaic-storage-b`
- branch: `split/round-003-storage-a`
- branch: `split/round-003-storage-b`
- commit_sha: `059caf68f39e48104b82c7b6b8fa9310337e0660`
- commit_sha: `324666707c1ea7f423aba2c67a0c92f46a9bdc71`
- migrated_paths: `novaic-storage-a/file_service/main.py`
- migrated_paths: `novaic-storage-a/scripts/verify_contract_version_a.sh`
- migrated_paths: `novaic-storage-b/tool_result_service/main.py`
- migrated_paths: `novaic-storage-b/scripts/verify_contract_version_b.sh`
- command: `cd /Users/wangchaoqun/novaic/novaic-storage-a && bash scripts/verify_contract_version_a.sh`
- expected_marker: `STORAGE_A_CONTRACT_VERSION_FIELD=PASS`
- expected_marker: `STORAGE_A_CONTRACT_VERSION=PASS`
- command: `cd /Users/wangchaoqun/novaic/novaic-storage-b && bash scripts/verify_contract_version_b.sh`
- expected_marker: `STORAGE_B_CONTRACT_VERSION_FIELD=PASS`
- expected_marker: `STORAGE_B_CONTRACT_VERSION=PASS`
- artifact_path: `novaic-storage-a/scripts/verify_contract_version_a.sh`
- artifact_path: `novaic-storage-b/scripts/verify_contract_version_b.sh`
- status: `DONE`

---

## Task 2 — failure-path: Permanent-outage retry-stop boundary verification

### problem_fixed
After contract version changes and repo commits, the max-attempt breach evidence needed re-validation to confirm the retry-stop boundary remained deterministic and that no regression was introduced.

### solution_applied
Re-ran `novaic-storage-b/scripts/failure_injection_max_attempt_breach.sh` against the updated Storage-B codebase (commit `324666707c1ea7f423aba2c67a0c92f46a9bdc71`). Script starts Storage-B pointed at a permanently offline port, calls `for-llm`, and asserts: resolver returns `None` gracefully (no `image_url`), exactly 3 retry attempts logged, no over-retry. All markers confirmed.

### target_state_proof

- type: `failure-path`
- repo_url: `https://github.com/chriswangcq/novaic-storage-b`
- branch: `split/round-003-storage-b`
- commit_sha: `324666707c1ea7f423aba2c67a0c92f46a9bdc71`
- migrated_paths: `novaic-storage-b/scripts/failure_injection_max_attempt_breach.sh`
- command: `cd /Users/wangchaoqun/novaic/novaic-storage-b && bash scripts/failure_injection_max_attempt_breach.sh`
- expected_marker: `RETRY_MAX_BREACH_RESOLVER_NULL=PASS`
- expected_marker: `RETRY_MAX_BREACH_ATTEMPTS_SEEN=3`
- expected_marker: `RETRY_MAX_BREACH_STOP=PASS`
- artifact_path: `novaic-storage-b/artifacts/storage-ab-max-attempt-breach-latest.md`
- status: `DONE`

---

## Task 3 — operability: Publish Round 009 full replay bundle

### problem_fixed
The Round 008 replay bundle did not include contract version verification steps. With the addition of `contract_version` to health endpoints, a new bundle was required that covers the complete Round 009 evidence chain including the new contract assertions.

### solution_applied
Created `novaic-control-plane/rounds/round-009/20-reports/storage-ab-round009-replay-bundle.sh` covering 7 sequential steps with temp-file buffering (no SIGPIPE false-FAIL). Embeds canonical URL map and commit anchors in header. Verified at 2026-02-21T03:26:39Z: `STEPS_PASSED=7`, `STEPS_FAILED=0`.

Steps covered:
1. `CONTRACT_VERSION_A` — `STORAGE_A_CONTRACT_VERSION=PASS`
2. `CONTRACT_VERSION_B` — `STORAGE_B_CONTRACT_VERSION=PASS`
3. `STORAGE_A_SMOKE` — `STORAGE_A_SMOKE_OK=true`
4. `STORAGE_B_RESTORE` — `STORAGE_B_RESTORE_VALIDATE=PASS`
5. `STORAGE_B_SMOKE` — `STORAGE_B_SMOKE_OK=true`
6. `RETRY_INJECTION` — `STORAGE_AB_RETRY_INJECTION=PASS`
7. `MAX_BREACH` — `RETRY_MAX_BREACH_STOP=PASS`

### target_state_proof

- type: `operability`
- repo_url: `https://github.com/chriswangcq/novaic-storage-a`
- repo_url: `https://github.com/chriswangcq/novaic-storage-b`
- branch: `split/round-003-storage-a`
- branch: `split/round-003-storage-b`
- commit_sha: `059caf68f39e48104b82c7b6b8fa9310337e0660`
- commit_sha: `324666707c1ea7f423aba2c67a0c92f46a9bdc71`
- migrated_paths: `novaic-control-plane/rounds/round-009/20-reports/storage-ab-round009-replay-bundle.sh`
- command: `cd /Users/wangchaoqun/novaic && bash novaic-control-plane/rounds/round-009/20-reports/storage-ab-round009-replay-bundle.sh`
- expected_marker: `REPLAY_CONTRACT_VERSION_A=PASS`
- expected_marker: `REPLAY_CONTRACT_VERSION_B=PASS`
- expected_marker: `REPLAY_STORAGE_A_SMOKE=PASS`
- expected_marker: `REPLAY_STORAGE_B_RESTORE=PASS`
- expected_marker: `REPLAY_STORAGE_B_SMOKE=PASS`
- expected_marker: `REPLAY_RETRY_INJECTION=PASS`
- expected_marker: `REPLAY_MAX_BREACH=PASS`
- expected_marker: `STEPS_PASSED=7`
- expected_marker: `STEPS_FAILED=0`
- expected_marker: `STORAGE_AB_ROUND009_REPLAY=PASS`
- artifact_path: `novaic-control-plane/rounds/round-009/20-reports/storage-ab-round009-replay-bundle.sh`
- status: `DONE`

---

## questions_for_program_owner

- question: Should `contract_version` values be centrally registered (e.g., in a `contracts/` registry file) so consumers across teams can declare which versions they depend on?
- why_blocking: Currently `storage-a/v1` and `storage-b/v1` are defined only inside the service code. If a downstream consumer (e.g., API gateway, agent runtime) needs to assert compatibility, there is no shared registry to reference.
- options:
  - Keep `contract_version` as a service-internal constant; consumers hard-code expected values in their own tests.
  - Create a `novaic-control-plane/contracts/` directory with a version registry file; teams register versions there.
  - Use semver in `contract_version` (e.g., `storage-a/1.0.0`) and enforce compatibility via a shared checker script.
- recommended_option: Option 2 — lightweight registry in control-plane keeps versions visible to all teams without adding tooling overhead.
- impact_if_unanswered: Contract version bumps will be invisible to consumers until an integration test fails; no shared source of truth for compatibility.
- requested_by_round: `round-009`

---

## Team status
- status: `DONE`
- blocker: `none`
