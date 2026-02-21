# Dispatch - Agent Runtime Team (Round 009 Real Remote Cutover)

- problem:
  - High-concurrency evidence exists, but threshold policy is not consistently tiered and idempotency breakage replay is not standardized for remote CI reuse.
- required_solution:
  - Split threshold policy by test tier (unit/integration) and enforce assertions.
  - Keep one deterministic idempotency failure-path replay.
  - Provide a reusable replay package for non-author and CI execution.
- target_state:
  - Throughput/retry thresholds are explicit and tier-scoped.
  - Dedup guard breakage replay emits stable marker and is machine-auditable.
  - Replay bundle can run from remote split repo with no local hidden assumptions.
- task (code/behavior): Refactor concurrency threshold config into explicit tiered policy and enforce assertions in test outputs with PASS markers.
- task (failure-path): Keep/add deterministic dedup-guard-broken replay that must emit FAIL-path marker when guard is bypassed.
- task (operability): Publish `agent-runtime-round009-evidence.md` with tier config table, replay commands, output markers, and CI usage notes.
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-agent-runtime-report.md`.
- status: PLANNED
