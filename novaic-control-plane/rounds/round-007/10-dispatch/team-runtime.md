# Dispatch - Runtime Team (Round 007 Findings Fix)

- problem:
  - Runtime needs to prove evidence format compliance under updated audit scripts.
- required_solution:
  - Normalize runtime report fields to canonical format.
  - Re-run runtime guard and startup replay to produce fresh artifact.
  - Validate runtime report with platform scripts without manual exception.
- target_state:
  - Runtime has zero canonical/format findings.
  - Runtime replay artifacts remain green and reproducible.
- task: Canonicalize runtime `repo_url` and marker fields in current and referenced reports.
- task: Re-run guard + startup replay and refresh artifact.
- task: Execute platform-compatible self-audit and include result marker.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-runtime-report.md`.
- status: PLANNED
