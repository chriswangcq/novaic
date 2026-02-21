# Dispatch - Tools Team (Round 011 Full Remote Verification)

- objective:
  - Prove tools preflight and runbook flows are remote-first and independently reproducible.

- mandatory_tasks:
  - execute preflight pass/failure checks from clean clone of `https://github.com/chriswangcq/novaic-tools-server`
  - preserve typed fail-closed markers for all mandatory env vars
  - publish round-011 tools runbook with clone/setup/replay/health verification chain

- acceptance_commands:
  - `python3 -c "import sys; sys.path.insert(0,'novaic-tools-server'); from tools_server.preflight import preflight_check; print('TOOLS_PREFLIGHT_IMPORT_OK')"`
  - `pytest -q novaic-tools-server/tests/unit/tools_server/`

- due: `round-011`
- status: `PLANNED`
