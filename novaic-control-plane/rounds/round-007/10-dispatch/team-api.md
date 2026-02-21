# Dispatch - API Team (Round 007 Findings Fix)

- problem:
  - API report fields were still flagged as non-canonical or ambiguous by platform audit.
- required_solution:
  - Normalize all API `repo_url` fields to canonical single-repo URL format.
  - Re-publish non-author replay artifact with deterministic marker set.
  - Re-verify gateway split chain after report correction.
- target_state:
  - API has zero canonical URL failures in platform audit.
  - Replay artifact marker coverage is complete and machine-checkable.
  - Gateway split chain remains green.
- task: Correct all `repo_url` values in API report entries to canonical form.
- task: Generate refreshed `split-fix/api-gateway-non-author-replay-round007.md`.
- task: Re-run gateway split replay and capture strict PASS markers.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-api-report.md`.
- status: PLANNED
