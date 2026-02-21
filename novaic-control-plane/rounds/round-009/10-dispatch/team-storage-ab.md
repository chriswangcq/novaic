# Dispatch - Storage-A/B Team (Round 009 Real Remote Cutover)

- problem:
  - Storage A/B replay chains work, but contract/version discipline and retry-boundary behavior still need stronger remote-first reproducibility guarantees.
- required_solution:
  - Keep canonical remote URLs and align A/B contract version semantics.
  - Prove max-attempt retry-stop boundary remains correct in permanent outage mode.
  - Deliver one replay package covering smoke, restore, retry-injection, and max-breach path.
- target_state:
  - Storage reports/evidence use canonical remote repo URLs.
  - Retry max-attempt boundary is deterministic and audited by marker.
  - Non-author replay package runs complete A/B chain from documented commands.
- task (code/behavior): Version and enforce Storage A/B interface contract expectations in code/tests and align report evidence to remote canonical repo URLs.
- task (failure-path): Maintain/add permanent-outage replay proving retry-stop at max attempts with deterministic markers and no over-retry.
- task (operability): Publish `storage-ab-round009-replay-bundle.sh` with full multi-step chain (A smoke, B restore/smoke, retry injection, max-attempt breach).
- evidence: for each DONE item provide command + expected_marker + commit_sha + migrated_paths + artifact_path in `20-reports/team-storage-ab-report.md`.
- status: PLANNED
