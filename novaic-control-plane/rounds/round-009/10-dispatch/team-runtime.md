# Dispatch - Runtime Team (Round 009 Real Remote Cutover)

- problem:
  - Runtime contract checks rely on local assumptions and fixed markers rather than remotely versioned contract source-of-truth.
- required_solution:
  - Externalize contract version source and enforce it in lifecycle guard flows.
  - Prove version mismatch is caught deterministically.
  - Ship an operability bundle runnable from split runtime repository alone.
- target_state:
  - Lifecycle guard reads and validates contract version from tracked contract artifact.
  - Version mismatch replay emits stable FAIL marker and fails correctly.
  - Runtime replay bundle is reproducible from remote split repo checkout.
- task (code/behavior): Replace hardcoded contract version assertion with version read from tracked contract file and assert exact match in lifecycle guard replay.
- task (failure-path): Add negative replay for contract-version mismatch and verify deterministic fail marker and non-zero exit.
- task (operability): Publish `runtime-round009-replay-bundle.md` including success-path, mismatch failure-path, and marker table.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-runtime-report.md`.
- status: PLANNED
