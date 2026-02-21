# Dispatch - Storage-A/B Team (Round 007 Findings Fix)

- problem:
  - Storage-A/B reports used non-policy URL scheme and triggered canonical audit failures.
- required_solution:
  - Replace non-canonical URLs with policy-approved format across all relevant reports.
  - Re-run non-author replay and publish explicit step-level PASS markers.
  - Reconfirm failure-injection chain remains green after evidence updates.
- target_state:
  - Storage-A/B has zero canonical URL findings.
  - Replay artifact is fully machine-checkable and reproducible.
- task: Normalize Storage-A/B report URL fields to canonical policy format.
- task: Re-run and republish non-author replay artifact with explicit markers.
- task: Re-verify failure-injection retry chain and include pass evidence.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-storage-ab-report.md`.
- status: PLANNED
