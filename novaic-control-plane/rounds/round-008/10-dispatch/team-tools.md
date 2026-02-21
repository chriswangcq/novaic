# Dispatch - Tools Team (Round 008 Clarity and Closure)

- problem:
  - Tools evidence must remain deterministic and fully machine-auditable.
- required_solution:
  - Keep canonical `repo_url` format stable.
  - Re-run packaged/dev split markers with explicit PASS tokens.
  - Refresh closure artifact and pass format checks.
- target_state:
  - Zero tools findings in canonical/format audits.
- task (code/behavior): Harden packaged-mode spawn with explicit preflight checks for split path and required env, returning typed errors.
- task (failure-path): Run packaged-mode replay with intentionally missing split path and verify fail-closed marker plus non-zero exit.
- task (operability): Publish tools runbook for packaged/dev mode diagnostics and replay bundle with marker matrix.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-tools-report.md`.
- status: PLANNED
