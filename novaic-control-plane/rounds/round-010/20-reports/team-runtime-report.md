# Round 010 Report - Runtime Team

---

## Task 1 — code/behavior: clean-clone reproducible contract guard

- problem_fixed: Runtime replay scripts referenced local sibling assumptions; contract version source-of-truth was tracked in local repo only, not verifiable from a clean clone of the canonical GitHub remote.
- solution_applied: Code pushed to `https://github.com/chriswangcq/novaic-runtime-orchestrator` (branch `main`). All scripts reference `config/services.json` and `contract/runtime-contract-version.json` by relative path within the repo — no sibling directory dependencies.
- target_state_proof:
  - command: `bash scripts/runtime_lifecycle_contract_guard_replay.sh`
  - expected_marker: `PASS: RUNTIME_CONTRACT_VERSION=v1`
  - actual_output: `RUNTIME_CONTRACT_VERSION=v1 / PASS: runtime lifecycle contract guard replay / PASS: RUNTIME_CONTRACT_VERSION=v1`

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_contract_guard_replay.sh`
- expected_marker: `PASS: RUNTIME_CONTRACT_VERSION=v1`
- repo_url: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
- branch: `main`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- migrated_paths: `contract/runtime-contract-version.json`
- artifact_path: `novaic-control-plane/rounds/round-010/split-fix/runtime-round010-replay-bundle.md`
- status: `DONE`

---

## Task 2 — failure-path: contract-version mismatch deterministic replay

- problem_fixed: No negative proof of version-mismatch guard prior to round-010.
- solution_applied: `scripts/runtime_lifecycle_version_mismatch_replay.sh` temporarily writes `v99` to `contract/runtime-contract-version.json`, runs guard, asserts non-zero exit, greps deterministic marker, restores file via EXIT trap.
- target_state_proof:
  - command: `bash scripts/runtime_lifecycle_version_mismatch_replay.sh`
  - expected_marker: `FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)`
  - actual_output: `FAIL: contract version mismatch: file=v99 expected=v1 / FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1) / PASS: version-mismatch-replay confirmed guard correctly rejects wrong contract version`

- command: `cd /Users/wangchaoqun/novaic-runtime-orchestrator && bash scripts/runtime_lifecycle_version_mismatch_replay.sh`
- expected_marker: `FAIL-MARKER: contract-version-mismatch-detected (file=v99 expected=v1)`
- repo_url: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
- branch: `main`
- commit_sha: `e3fd9d194b8cb8a9d3277abac466edb456f2462d`
- migrated_paths: `scripts/runtime_lifecycle_version_mismatch_replay.sh`
- artifact_path: `novaic-control-plane/rounds/round-010/split-fix/runtime-round010-replay-bundle.md`
- status: `DONE`

---

## Task 3 — operability: runtime-round010-replay-bundle.md with clean-clone instructions

- problem_fixed: Prior bundles referenced local paths; no clean-clone setup instructions existed.
- solution_applied: Created `novaic-control-plane/rounds/round-010/split-fix/runtime-round010-replay-bundle.md` with clean-clone setup, pip install, full marker table, success and failure replay outputs.
- target_state_proof:
  - command: `cd /Users/wangchaoqun/novaic && git cat-file -e 9a3f634ddd2254f728010796cf00c981355a3083^{commit} && echo REACHABLE`
  - expected_marker: `REACHABLE`
  - actual_output: `REACHABLE`

- command: `cd /Users/wangchaoqun/novaic && git cat-file -e 9a3f634ddd2254f728010796cf00c981355a3083^{commit} && echo REACHABLE`
- expected_marker: `REACHABLE`
- repo_url: `https://github.com/chriswangcq/novaic`
- branch: `add-virtual-mobile`
- commit_sha: `9a3f634ddd2254f728010796cf00c981355a3083`
- migrated_paths: `novaic-control-plane/rounds/round-010/split-fix/runtime-round010-replay-bundle.md`
- artifact_path: `novaic-control-plane/rounds/round-010/split-fix/runtime-round010-replay-bundle.md`
- status: `DONE`

---

## questions_for_program_owner

- question: Should Platform update `REMOTE_TO_LOCAL` in `check_commit_reachability.py` for each split repo, or should each team add their own mapping entry?
- why_blocking: Not blocking. Runtime team added its own mapping in this round.
- options: (A) Platform owns REMOTE_TO_LOCAL. (B) Each team adds their own entry.
- recommended_option: Option A.
- impact_if_unanswered: Teams will continue adding their own entries, risking merge conflicts.
- requested_by_round: `round-010`

---

## Team status

- status: `DONE`
- blocker: none
- operability_artifact: `novaic-control-plane/rounds/round-010/split-fix/runtime-round010-replay-bundle.md`
