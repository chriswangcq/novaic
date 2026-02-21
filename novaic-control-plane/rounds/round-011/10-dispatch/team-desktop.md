# Dispatch - Desktop Team (Round 011 Full Remote Verification)

- objective:
  - Keep strict split startup checks and validate desktop operability from canonical main repo workflow.

- mandatory_tasks:
  - verify strict split-config abort path remains effective in latest main repo commit
  - replay tools-hop failure path and persist diagnostics artifact for non-author check
  - publish round-011 desktop closure bundle with clean-clone steps, hop checks, and troubleshooting matrix

- acceptance_commands:
  - `cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS`
  - `bash novaic-app/scripts/failure_path_replay_round009.sh`

- due: `round-011`
- status: `PLANNED`
