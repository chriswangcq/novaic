# Dispatch - Platform Team (Round 010 Remote Reachability Closure)

- objective:
  - Close the Round 009 residual gap: move commit-reachability from all `SKIP_REMOTE` to team-level verifiable `REACHABLE` while keeping parser-contract strict.

- mandatory_tasks:
  - task (code/behavior): update round-010 audit scripts to enforce team-level reachability rule (`>=1 REACHABLE pair per team`) and keep `https://github.com/<org>/<repo>` canonical check strict.
  - task (failure-path): add one negative fixture where `repo_url` is valid but `commit_sha` is not in remote; audit must emit deterministic unreachable marker and fail.
  - task (operability): publish `gate_round010.sh` that runs canonical-url audit, commit-reachability audit, cross-team evidence audit, regression audit, and negative-fixture test in order.

- acceptance_commands:
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/audit_round010_reports.py`
  - `bash rounds/round-010/split-close/gate_round010.sh`

- evidence_requirements:
  - report path: `20-reports/team-platform-report.md`
  - required fields per task: `command` + `expected_marker` + `repo_url` + `commit_sha` + `migrated_paths` + `artifact_path`
  - canonical repos in this round:
    - `https://github.com/chriswangcq/novaic`
    - `https://github.com/chriswangcq/novaic-gateway`
    - `https://github.com/chriswangcq/novaic-runtime-orchestrator`
    - `https://github.com/chriswangcq/novaic-agent-runtime`
    - `https://github.com/chriswangcq/novaic-tools-server`
    - `https://github.com/chriswangcq/novaic-storage-a`
    - `https://github.com/chriswangcq/novaic-storage-b`

- due: `round-010`
- status: `PLANNED`
