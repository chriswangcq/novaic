# Dispatch - Runtime Team (Round 008 Clarity and Closure)

- problem:
  - Runtime evidence must remain clean under stricter freshness and marker rules.
- required_solution:
  - Keep canonical URL fields and status fields compliant.
  - Re-run runtime guard/startup replays and refresh artifacts.
  - Ensure runtime report passes platform self-audit without exceptions.
- target_state:
  - Zero runtime-specific audit findings.
- task (code/behavior): Add explicit contract-version marker to runtime lifecycle guard script output and enforce expected version check.
- task (failure-path): Add a negative replay case for invalid lifecycle transition and verify deterministic FAIL marker.
- task (operability): Publish updated runtime replay artifact bundle (success path + failure path + marker table).
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-runtime-report.md`.
- status: PLANNED
