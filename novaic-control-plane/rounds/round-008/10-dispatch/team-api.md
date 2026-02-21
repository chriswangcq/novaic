# Dispatch - API Team (Round 008 Clarity and Closure)

- problem:
  - API evidence must remain canonical and replay-verifiable under final audit rules.
- required_solution:
  - Keep canonical `repo_url` fields stable.
  - Regenerate non-author replay artifact with clear marker table.
  - Validate replay remains green after final audit script changes.
- target_state:
  - Zero API findings in canonical and cross-team audits.
- task (code/behavior): Remove one remaining optional fallback in gateway replay path and enforce split-runtime endpoint config as default.
- task (failure-path): Add replay that intentionally points runtime URL to invalid host and verify deterministic fail marker + non-zero exit.
- task (operability): Publish refreshed non-author replay bundle with success/failure transcripts and marker index.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-api-report.md`.
- status: PLANNED
