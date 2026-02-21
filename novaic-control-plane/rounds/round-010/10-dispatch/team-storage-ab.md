# Dispatch - Storage-A/B Team (Round 010 Remote Reachability Closure)

- objective:
  - Preserve A/B contract + retry boundary guarantees while proving remote reachability and clean-clone replay from canonical storage repos.

- mandatory_tasks:
  - task (code/behavior): keep `contract_version` health contract for both services and align report evidence to `https://github.com/chriswangcq/novaic-storage-a` and `https://github.com/chriswangcq/novaic-storage-b`.
  - task (failure-path): keep permanent-outage max-attempt replay deterministic (`no over-retry`, exact attempt boundary markers).
  - task (operability): publish `storage-ab-round010-replay-bundle.sh` with clean-clone setup + full chain (A contract/smoke, B restore/smoke, retry injection, max breach).

- acceptance_commands:
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `bash novaic-storage-a/scripts/verify_contract_version_a.sh`
  - `bash novaic-storage-b/scripts/verify_contract_version_b.sh`
  - `bash novaic-storage-b/scripts/failure_injection_max_attempt_breach.sh`

- evidence_requirements:
  - report path: `20-reports/team-storage-ab-report.md`
  - repo_url must be:
    - `https://github.com/chriswangcq/novaic-storage-a`
    - `https://github.com/chriswangcq/novaic-storage-b`
  - at least one task must show commit reachability as `REACHABLE` for each storage repo
  - required fields per task: `command` + `expected_marker` + `repo_url` + `commit_sha` + `migrated_paths` + `artifact_path`

- due: `round-010`
- status: `PLANNED`
