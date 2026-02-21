# Dispatch - Agent Runtime Team (Round 005 Gap Closure)

- task: Migrate remaining worker/handler modules to split repo and leave only explicit shim boundaries in monorepo.
- task: Remove monorepo path assumptions in agent runtime scripts and tests.
- task: Run high-concurrency idempotency/retry replay from split repo root and compare with Round 004 baseline.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-agent-runtime-report.md`.
- status: PLANNED
