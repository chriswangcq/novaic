# Dispatch - Tools Team (Round 010 Remote Reachability Closure)

- objective:
  - Make tools preflight/runbook evidence remote-replayable from canonical repo and produce at least one `REACHABLE` commit proof.

- mandatory_tasks:
  - task (code/behavior): keep mandatory preflight env policy strict, and ensure all runbook commands assume clean clone of `https://github.com/chriswangcq/novaic-tools-server`.
  - task (failure-path): keep typed fail-closed markers for missing required env (`GATEWAY_URL`, `RUNTIME_ORCHESTRATOR_URL`, `TOOL_RESULT_SERVICE_URL`) with deterministic assertions.
  - task (operability): publish `tools-round010-runbook.md` including clone/setup/preflight pass/fail/baseline flow and marker matrix.

- acceptance_commands:
  - `python3 rounds/round-010/split-close/repos/novaic-evidence-audit/scripts/check_commit_reachability.py`
  - `python3 -c "import sys,os; sys.path.insert(0,'novaic-tools-server'); from tools_server.preflight import preflight_check; print('TOOLS_PREFLIGHT_PROBE_OK')"`
  - `pytest -q novaic-tools-server/tests/unit/tools_server/`

- evidence_requirements:
  - report path: `20-reports/team-tools-report.md`
  - repo_url must be: `https://github.com/chriswangcq/novaic-tools-server`
  - at least one task must show commit reachability as `REACHABLE` for the reported `commit_sha`
  - required fields per task: `command` + `expected_marker` + `repo_url` + `commit_sha` + `migrated_paths` + `artifact_path`

- due: `round-010`
- status: `PLANNED`
