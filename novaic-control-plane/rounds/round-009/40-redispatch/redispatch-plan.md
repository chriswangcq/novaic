# Round 009 Redispatch Plan (Hotfix for Gate A Fail)

## Trigger
- Gate runner result: `gate_round009.sh` fails at Gate A (`canonical-url-audit`).
- Blocking finding summary: `split-close/canonical-repo-url-audit.md` reports 18 violations.
- Root cause: 5 team reports still use `file:///` `repo_url` values, violating Round 009 https-only contract.

## Hard closure rule
- Only this issue is in scope for redispatch: convert all non-https `repo_url` values to canonical `https://github.com/<org>/<repo>`.
- No placeholder URL is accepted.
- No `file:///` / `local:` / SSH URL is accepted.
- Every updated `repo_url` must pair with a real reachable `commit_sha` in that remote.

## Team items
- team: `API`
  - finding_reference: `team-api has 3 non-https repo_url findings in canonical audit`
  - mandatory_fix_tasks:
    - replace all `repo_url` fields in `20-reports/team-api-report.md` to canonical GitHub HTTPS URL
    - ensure each `commit_sha` exists in the referenced remote repo
    - re-run API evidence commands if commit changed and refresh artifact paths if needed
  - acceptance_commands:
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - required_commit_or_path: `rounds/round-009/20-reports/team-api-report.md`
  - target_round: `round-009`
  - status: `DONE`

- team: `Runtime`
  - finding_reference: `team-runtime has 3 non-https repo_url findings in canonical audit`
  - mandatory_fix_tasks:
    - replace all `repo_url` fields in `20-reports/team-runtime-report.md` to canonical GitHub HTTPS URL
    - ensure `commit_sha` values are reachable in remote
    - keep existing markers/artifacts unchanged unless replay output changed
  - acceptance_commands:
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - required_commit_or_path: `rounds/round-009/20-reports/team-runtime-report.md`
  - target_round: `round-009`
  - status: `DONE`

- team: `Agent Runtime`
  - finding_reference: `team-agent-runtime has 3 non-https repo_url findings in canonical audit`
  - mandatory_fix_tasks:
    - replace all `repo_url` fields in `20-reports/team-agent-runtime-report.md` to canonical GitHub HTTPS URL
    - ensure `commit_sha` values are reachable in remote
    - keep tier marker semantics unchanged (`tier=unit`)
  - acceptance_commands:
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - required_commit_or_path: `rounds/round-009/20-reports/team-agent-runtime-report.md`
  - target_round: `round-009`
  - status: `DONE`

- team: `Tools`
  - finding_reference: `team-tools has 4 non-https repo_url findings in canonical audit`
  - mandatory_fix_tasks:
    - replace all `repo_url` fields in `20-reports/team-tools-report.md` to canonical GitHub HTTPS URL
    - ensure `commit_sha` values are reachable in remote
    - keep runbook marker set unchanged
  - acceptance_commands:
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - required_commit_or_path: `rounds/round-009/20-reports/team-tools-report.md`
  - target_round: `round-009`
  - status: `DONE`

- team: `Storage-A/B`
  - finding_reference: `team-storage-ab has 5 non-https repo_url findings in canonical audit`
  - mandatory_fix_tasks:
    - replace all `repo_url` fields in `20-reports/team-storage-ab-report.md` to canonical GitHub HTTPS URL
    - ensure both storage repo `commit_sha` values are reachable in remote
    - keep replay bundle markers unchanged (`STEPS_PASSED=7`, `STEPS_FAILED=0`)
  - acceptance_commands:
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/enforce_canonical_repo_url.py`
    - `python3 rounds/round-009/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - required_commit_or_path: `rounds/round-009/20-reports/team-storage-ab-report.md`
  - target_round: `round-009`
  - status: `DONE`

- team: `Platform`
  - finding_reference: `Gate A failed; full round still blocked`
  - mandatory_fix_tasks:
    - after the 5 teams update reports, re-run full gate chain
    - publish fresh audit artifacts with new `generated_at` and `report_snapshot_sha`
    - publish final gate evidence showing `ROUND009_GATE_RUNNER_PASS`
  - acceptance_commands:
    - `bash rounds/round-009/split-close/gate_round009.sh`
  - required_commit_or_path: `rounds/round-009/split-close/`
  - target_round: `round-009`
  - status: `DONE`

## Status
- status: `CLOSED`
- blocker: `none`
