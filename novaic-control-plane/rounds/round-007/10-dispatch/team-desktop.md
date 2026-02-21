# Dispatch - Desktop Team (Round 007 Findings Fix)

- problem:
  - Desktop report fields were parsed as non-canonical and marker set was not consistently audit-friendly.
- required_solution:
  - Normalize desktop `repo_url` to canonical policy format across active reports.
  - Ensure expected markers always include explicit `DESKTOP_*` and `PASS` tokens.
  - Re-run split chain and republish evidence artifact with corrected marker lines.
- target_state:
  - Desktop has zero canonical URL and format findings.
  - Desktop split replay evidence is fully non-author reproducible.
- task: Canonicalize desktop `repo_url` values in current and referenced round reports.
- task: Update marker fields to include explicit DESKTOP/PASS tokens.
- task: Re-run desktop split chain and publish corrected evidence artifact.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-desktop-report.md`.
- status: PLANNED
