# Dispatch - API Team (Round 009 Real Remote Cutover)

- problem:
  - Gateway split-path behavior is still partially tolerant to local defaults, which weakens true multi-repo reproducibility.
- required_solution:
  - Remove implicit local fallback in split runtime/tool endpoints.
  - Make failure behavior deterministic when downstream services are unreachable.
  - Provide a remote-repo replay bundle that non-authors can run from clean clone.
- target_state:
  - Gateway split mode depends only on explicit external URLs.
  - Runtime-unreachable case fails fast with stable marker and non-zero exit.
  - API replay evidence is reproducible from remote repository state.
- task (code/behavior): Remove remaining implicit endpoint fallback in gateway split scripts/config and enforce explicit runtime/tools URLs.
- task (failure-path): Add replay with intentionally unreachable runtime URL and verify fail-fast marker plus non-zero exit.
- task (operability): Publish `api-round009-replay-bundle.md` with success-path + failure-path transcript and marker index for non-author replay.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-api-report.md`.
- status: PLANNED
