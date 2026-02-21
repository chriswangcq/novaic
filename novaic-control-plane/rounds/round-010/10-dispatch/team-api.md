# Dispatch - API Team (Round 010 Remote Reachability Closure)

- objective:
  - Make gateway evidence truly remote-operable: clean-clone replay, at least one `REACHABLE` commit pair, and no local sibling path assumptions.

- mandatory_tasks:
  - task (code/behavior): update gateway replay/config scripts to accept remote clone workflow (`https://github.com/chriswangcq/novaic-gateway`) and remove hard dependency on pre-existing local sibling repos.
  - task (failure-path): keep runtime-unreachable and startup-no-url failure-path replays deterministic with explicit markers and non-zero inner failure exit.
  - task (operability): publish `api-round010-replay-bundle.md` with clean-clone setup section, success-path transcript, failure-path transcript(s), and marker index.

- acceptance_commands:
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `bash rounds/round-003/split-move/repos/novaic-gateway/scripts/smoke_gateway_repo_root.sh`
  - `bash rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_startup_no_url.sh`
  - `bash rounds/round-003/split-move/repos/novaic-gateway/scripts/fail_path_replay_gateway.sh`

- evidence_requirements:
  - report path: `20-reports/team-api-report.md`
  - repo_url must be: `https://github.com/chriswangcq/novaic-gateway`
  - at least one task must show commit reachability as `REACHABLE` for the reported `commit_sha`
  - required fields per task: `command` + `expected_marker` + `repo_url` + `commit_sha` + `migrated_paths` + `artifact_path`

- due: `round-010`
- status: `PLANNED`
