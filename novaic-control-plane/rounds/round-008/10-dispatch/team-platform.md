# Dispatch - Platform Team (Round 008 Clarity and Closure)

- problem:
  - Audit/report mismatch and parser ambiguity still reduce trust in gate decisions.
- required_solution:
  - Enforce canonical URL policy strictly.
  - Add timestamp and snapshot metadata to all audit outputs.
  - Re-run all audits after teams finish final report edits.
- target_state:
  - Zero false positives.
  - Zero canonical failures.
  - Audit files prove they ran after final report updates.
- task (code/behavior): Update audit scripts to output machine-readable JSON plus markdown, including `generated_at` and `report_snapshot_sha`.
- task (failure-path): Add a negative test fixture report and prove audit scripts correctly flag it (and only it).
- task (operability): Publish a one-command gate runner (`gate_round008.sh`) that runs all audits in order and exits non-zero on any failure.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-platform-report.md`.
- status: PLANNED
