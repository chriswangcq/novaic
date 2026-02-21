# Dispatch - Runtime Team (Round 010 Remote Reachability Closure)

- objective:
  - Convert runtime proofs from local split assumptions to remote-checkable evidence with clean-clone replay.

- mandatory_tasks:
  - task (code/behavior): keep contract-version source-of-truth flow, and ensure runtime replay scripts can run from cloned `https://github.com/chriswangcq/novaic-runtime-orchestrator` without local path shortcuts.
  - task (failure-path): keep contract-version mismatch replay deterministic and machine-greppable (`FAIL-MARKER` required).
  - task (operability): publish `runtime-round010-replay-bundle.md` including clean-clone setup, success/failure replay commands, marker table, and artifact list.

- acceptance_commands:
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `bash scripts/runtime_lifecycle_contract_guard_replay.sh`
  - `bash scripts/runtime_lifecycle_version_mismatch_replay.sh`

- evidence_requirements:
  - report path: `20-reports/team-runtime-report.md`
  - repo_url must be: `https://github.com/chriswangcq/novaic-runtime-orchestrator`
  - at least one task must show commit reachability as `REACHABLE` for the reported `commit_sha`
  - required fields per task: `command` + `expected_marker` + `repo_url` + `commit_sha` + `migrated_paths` + `artifact_path`

- due: `round-010`
- status: `PLANNED`
