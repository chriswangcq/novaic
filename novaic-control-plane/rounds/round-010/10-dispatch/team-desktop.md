# Dispatch - Desktop Team (Round 010 Remote Reachability Closure)

- objective:
  - Keep strict split startup behavior and convert desktop operability evidence to remote-clean-clone runnable flow.

- mandatory_tasks:
  - task (code/behavior): keep strict split-config abort path (`no implicit localhost fallback`) and ensure docs/scripts reference canonical main repo `https://github.com/chriswangcq/novaic`.
  - task (failure-path): keep tools-hop unavailable replay deterministic with diagnostics artifact persisted to declared path.
  - task (operability): publish `desktop-closure-bundle-round010.md` with clean-clone setup, 3-hop checks, strict-abort replay, failure-path replay, and troubleshooting matrix.

- acceptance_commands:
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `cd novaic-app/src-tauri && cargo check && echo DESKTOP_BUILD=PASS`
  - `DIAG_OUT=rounds/round-010/split-fix/round010-failure-path-diag.txt bash novaic-app/scripts/failure_path_replay_round009.sh`

- evidence_requirements:
  - report path: `20-reports/team-desktop-report.md`
  - repo_url must be: `https://github.com/chriswangcq/novaic`
  - at least one task must show commit reachability as `REACHABLE` for the reported `commit_sha`
  - required fields per task: `command` + `expected_marker` + `repo_url` + `commit_sha` + `migrated_paths` + `artifact_path`

- due: `round-010`
- status: `PLANNED`
