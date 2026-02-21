# Dispatch - Agent Runtime Team (Round 007 Findings Fix)

- problem:
  - Prior rounds showed inconsistent marker/report formatting across teams.
- required_solution:
  - Keep agent-runtime report strictly canonical and marker-complete.
  - Re-run high-concurrency and full-suite replay for fresh evidence.
  - Publish grep-friendly marker lines for platform audit scripts.
- target_state:
  - Agent-runtime report returns zero audit findings.
  - Evidence artifact contains full marker list and canonical URL.
- task: Normalize `repo_url`, `expected_marker`, and `status` fields to canonical format.
- task: Re-run high-concurrency replay plus full test replay.
- task: Publish updated evidence artifact with explicit marker table.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-agent-runtime-report.md`.
- status: PLANNED
