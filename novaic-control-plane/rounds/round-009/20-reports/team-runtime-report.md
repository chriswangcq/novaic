# Round 009 Report - Runtime Team

---

## Task 1 — code/behavior: externalize contract version to tracked file

- problem_fixed: Contract version was hardcoded as `v1` in guard script; no remote versioned source-of-truth existed. Drift between deployed contract and guard assumption could not be detected automatically.
- solution_applied: Created `contract/runtime-contract-version.json` as the tracked source-of-truth. Updated `scripts/runtime_lifecycle_contract_guard_replay.sh` to read version from this file at runtime; added shell-level mismatch check that exits non-zero before starting the server if file version != expected.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh`
  - expected_marker: `PASS: RUNTIME_CONTRACT_VERSION=v1`
  - actual_output: `RUNTIME_CONTRACT_VERSION=v1 / PASS: runtime lifecycle contract guard replay / PASS: contract runtime_id rt-2f161e1aacd9 / PASS: RUNTIME_CONTRACT_VERSION=v1`

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh`
- expected_marker: `PASS: RUNTIME_CONTRACT_VERSION=v1`
- repo_url: `https://github.com/novaic-org/novaic-runtime-orchestrator`
- branch: `split/round-003-runtime`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- migrated_paths: `contract/runtime-contract-version.json`
- artifact_path: `novaic-control-plane/rounds/round-009/split-fix/runtime-round009-replay-bundle.md`
- status: `DONE`

---

## Task 2 — failure-path: contract-version mismatch negative replay

- problem_fixed: No version-mismatch failure-path existed; only a CAS-rejection failure-path from Round 008. Guard's version-read logic had no negative proof that mismatch causes deterministic non-zero exit.
- solution_applied: Created `scripts/runtime_lifecycle_version_mismatch_replay.sh`; temporarily writes `v99` to `contract/runtime-contract-version.json`, runs guard, asserts non-zero exit, greps output for `FAIL: contract version mismatch: file=v99 expected=v1`, prints deterministic `FAIL-MARKER: contract-version-mismatch-detected`. EXIT trap restores real contract file regardless of outcome.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_version_mismatch_replay.sh`
  - expected_marker: `FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)`
  - actual_output: `FAIL: contract version mismatch: file=v99 expected=v1 / FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1) / PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version`

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_version_mismatch_replay.sh`
- expected_marker: `FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)`
- repo_url: `https://github.com/novaic-org/novaic-runtime-orchestrator`
- branch: `split/round-003-runtime`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- migrated_paths: `scripts/runtime_lifecycle_version_mismatch_replay.sh`
- artifact_path: `novaic-control-plane/rounds/round-009/split-fix/runtime-round009-replay-bundle.md`
- status: `DONE`

---

## Task 3 — operability: runtime-round009-replay-bundle.md

- problem_fixed: Round 008 bundle was round-scoped; no forward-looking operability reference included the version-mismatch failure path or the contract version source-of-truth reference.
- solution_applied: Created `novaic-control-plane/rounds/round-009/split-fix/runtime-round009-replay-bundle.md` containing full marker table, success-path replay output, version-mismatch failure-path output with explanation, contract version source reference, and operability asset table.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh && bash scripts/runtime_lifecycle_version_mismatch_replay.sh`
  - expected_marker: `PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version`
  - actual_output: (all markers from marker table confirmed; see bundle)

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh && bash scripts/runtime_lifecycle_version_mismatch_replay.sh`
- expected_marker: `PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version`
- repo_url: `https://github.com/novaic-org/novaic-runtime-orchestrator`
- branch: `split/round-003-runtime`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- migrated_paths: `novaic-control-plane/rounds/round-009/split-fix/runtime-round009-replay-bundle.md`
- artifact_path: `novaic-control-plane/rounds/round-009/split-fix/runtime-round009-replay-bundle.md`
- status: `DONE`

---

## questions_for_program_owner

- question: When `contract/runtime-contract-version.json` version is bumped (e.g., v1 → v2), should the `EXPECTED_CONTRACT_VERSION` constant in the guard script also be updated manually, or should the expected version be driven by a separate policy file that all teams reference?
- why_blocking: Not blocking Round 009. Becomes relevant when any team makes a breaking contract change and Runtime needs to know what the canonical expected version is.
- options: (A) Each team updates their own guard script's expected constant when they bump. (B) Platform owns a `policy/expected-contract-versions.json` file; guard scripts read expected version from there.
- recommended_option: Option B — removes per-team manual sync and makes contract version expectations auditable from one place.
- impact_if_unanswered: Guard script's expected constant stays at `v1` until manually updated; a breaking change would only be detected if the developer remembers to bump both files.
- requested_by_round: `round-009`

---

## Team status

- status: `DONE`
- blocker: none
- operability_artifact: `novaic-control-plane/rounds/round-009/split-fix/runtime-round009-replay-bundle.md`
