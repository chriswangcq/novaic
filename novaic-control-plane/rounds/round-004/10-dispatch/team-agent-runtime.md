# Dispatch - Agent Runtime Team (Round 004 Code Move)

- task: Move additional worker/handler modules from monorepo task queue into split agent-runtime repo and wire imports.
- task: Remove monorepo-only execution assumptions in replay scripts so they run from split repo root.
- task: Run idempotency/retry replay from split repo root and publish PASS markers with commit evidence.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-agent-runtime-report.md`.
- status: PLANNED
