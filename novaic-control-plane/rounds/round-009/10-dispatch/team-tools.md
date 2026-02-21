# Dispatch - Tools Team (Round 009 Real Remote Cutover)

- problem:
  - Tools split startup behavior is improved, but required-env policy and packaged/dev operability are not yet fully standardized for remote multi-repo execution.
- required_solution:
  - Lock required preflight env policy and emit typed errors for missing mandatory variables.
  - Prove fail-closed startup path remains deterministic.
  - Deliver a remote-first runbook from clone to health checks.
- target_state:
  - Packaged/dev preflight policy is explicit and machine-checked.
  - Missing required env triggers typed marker + non-zero exit.
  - Non-author can reproduce diagnostics and recovery using one runbook.
- task (code/behavior): Harden preflight policy by codifying mandatory vars for startup path and emitting stable typed error markers for each missing var class.
- task (failure-path): Add replay cases for missing mandatory env(s) and validate fail-closed behavior with deterministic markers.
- task (operability): Publish `tools-round009-runbook.md` covering clone, setup, preflight pass/fail replay, and health verification marker matrix.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-tools-report.md`.
- status: PLANNED
