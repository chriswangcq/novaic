# Dispatch - Storage-A/B Team (Round 008 Clarity and Closure)

- problem:
  - Storage-A/B reports still use `local:` repo URL scheme, which violates canonical policy.
- required_solution:
  - Replace all `local:` entries with policy-approved canonical URL format.
  - Re-run non-author replay and failure-injection checks after URL normalization.
  - Publish updated artifact with explicit marker table and canonical URLs.
- target_state:
  - Zero storage canonical URL failures.
- task (code/behavior): Replace all `local:` URL usage with policy-approved canonical URLs in active storage reports and evidence docs.
- task (failure-path): Extend failure-injection replay to assert retry-stop behavior on max-attempt breach with deterministic FAIL marker.
- task (operability): Publish storage non-author replay package including canonical URL map, restore/smoke chain, and failure-injection outcomes.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-storage-ab-report.md`.
- status: PLANNED
