# Dispatch - Runtime Team (Round 011 Full Remote Verification)

- objective:
  - Validate runtime contract and failure-path flows from remote repository only.

- mandatory_tasks:
  - run lifecycle guard and version-mismatch replays from clean clone of `https://github.com/chriswangcq/novaic-runtime-orchestrator`
  - ensure contract version artifact and scripts are in sync with remote commit proof
  - publish round-011 runtime replay bundle with command/marker table and no local absolute paths

- acceptance_commands:
  - `bash scripts/runtime_lifecycle_contract_guard_replay.sh`
  - `bash scripts/runtime_lifecycle_version_mismatch_replay.sh`

- due: `round-011`
- status: `PLANNED`
