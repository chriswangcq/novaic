# Dispatch - Desktop Team (Round 008 Clarity and Closure)

- problem:
  - Desktop evidence needs consistent canonical URLs and explicit marker semantics across rounds.
- required_solution:
  - Keep `repo_url` canonical in all referenced desktop reports.
  - Ensure marker fields include required `DESKTOP_*` and `PASS` tokens.
  - Re-run split chain replay and republish non-author artifact.
- target_state:
  - Zero desktop canonical/format findings.
- task (code/behavior): Remove one remaining implicit local fallback in desktop split chain script and require explicit split-service endpoints.
- task (failure-path): Run replay with tools endpoint intentionally unavailable and verify deterministic desktop-stage FAIL marker and diagnostics output.
- task (operability): Publish refreshed desktop closure bundle with canonical metadata, hop-by-hop markers, and troubleshooting notes.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-desktop-report.md`.
- status: PLANNED
