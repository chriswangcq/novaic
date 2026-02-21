# Dispatch - API Team (Round 011 Full Remote Verification)

- objective:
  - Make gateway replay fully remote-clone reproducible and remove any hidden local layout assumptions.

- mandatory_tasks:
  - update API replay scripts/runbook to clone and run from `https://github.com/chriswangcq/novaic-gateway`
  - keep startup-failure and runtime-unreachable failure-path markers deterministic
  - refresh report evidence using remote-verifiable commit SHA and updated artifact paths

- acceptance_commands:
  - `bash scripts/smoke_gateway_repo_root.sh`
  - `bash scripts/fail_path_startup_no_url.sh`
  - `bash scripts/fail_path_replay_gateway.sh`

- due: `round-011`
- status: `PLANNED`
