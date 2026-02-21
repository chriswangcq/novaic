# Dispatch - Agent Runtime Team (Round 010 Remote Reachability Closure)

- objective:
  - Keep tiered concurrency evidence stable while making replay and commit proof remote-reachable and CI-friendly from canonical repo.

- mandatory_tasks:
  - task (code/behavior): keep tiered threshold policy (`unit`/`integration`) and ensure command paths and docs are valid for clean clone of `https://github.com/chriswangcq/novaic-agent-runtime`.
  - task (failure-path): maintain deterministic dedup-guard failure-path replay with explicit tier label marker.
  - task (operability): publish `agent-runtime-round010-evidence.md` with clean-clone bootstrap, replay commands, CI notes, and marker grep table.

- acceptance_commands:
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py`
  - `PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_dedup_guard_failure_path.py`

- evidence_requirements:
  - report path: `20-reports/team-agent-runtime-report.md`
  - repo_url must be: `https://github.com/chriswangcq/novaic-agent-runtime`
  - at least one task must show commit reachability as `REACHABLE` for the reported `commit_sha`
  - required fields per task: `command` + `expected_marker` + `repo_url` + `commit_sha` + `migrated_paths` + `artifact_path`

- due: `round-010`
- status: `PLANNED`
