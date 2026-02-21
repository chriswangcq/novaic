# Dispatch - Agent Runtime Team (Round 008 Clarity and Closure)

- problem:
  - Agent-runtime evidence must stay parser-friendly and marker-complete.
- required_solution:
  - Keep report structure strict and placeholder-free.
  - Refresh replay evidence and keep canonical URL fields.
  - Provide explicit marker table in artifact for automated checks.
- target_state:
  - Zero format/canonical findings for agent-runtime report.
- task (code/behavior): Add explicit threshold assertions to high-concurrency replay (throughput floor, retry count bounds) and print PASS/FAIL markers.
- task (failure-path): Add one replay with forced duplicate delivery beyond threshold and verify handler dedup guard emits FAIL marker when broken.
- task (operability): Publish updated agent-runtime evidence bundle with threshold config, metrics table, and replay commands.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-agent-runtime-report.md`.
- status: PLANNED
