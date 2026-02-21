# Round 004 Tools Split Run Evidence

## Split repo migration commit

- repo_url: `file:///Users/wangchaoqun/novaic/.split-remotes/novaic-tools-server.git`
- branch: `split-round-003`
- commit_sha: `c279971e82fdbad66e71394a0b24d036175fd287`

Migrated paths (source -> target):
- `novaic-backend/tools_server/RELIABILITY_POLICY.md` -> `novaic-tools-server/tools_server/RELIABILITY_POLICY.md`
- `novaic-backend/tools_server/OPERATOR_RUNBOOK.md` -> `novaic-tools-server/tools_server/OPERATOR_RUNBOOK.md`
- `novaic-backend/scripts/tools/RUNNER_SUPPORT_POLICY.md` -> `novaic-tools-server/scripts/tools/RUNNER_SUPPORT_POLICY.md`
- `novaic-backend/tests/unit/tools_server/test_policy_doc_sync.py` -> `novaic-tools-server/tests/unit/tools_server/test_policy_doc_sync.py`
- `novaic-backend/main_tools.py` -> `novaic-tools-server/main_tools.py`

## Monorepo caller wiring updates

- `novaic-backend/main_novaic.py`: supports loading split tools entrypoint via `NOVAIC_TOOLS_SERVER_SPLIT_REPO`.
- `novaic-backend/start_all_services.sh`: exports split tools repo env and prefers split entrypoint if present.
- `novaic-backend/start_all_dev.sh`: same split repo wiring for dev startup path.

## Replay commands and markers

1. Split repo timeout/isolation/policy baseline:
   - command: `cd novaic-tools-server && bash scripts/tools/ci_preflight_probe_prereqs.sh && bash scripts/tools/leak_probe.sh && pytest -q tests/unit/tools_server/test_reliability_policy.py tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_policy_doc_sync.py && echo "TOOLS_SPLIT_TIMEOUT_ISOLATION_POLICY:PASS"`
   - expected_marker: `TOOLS_SPLIT_TIMEOUT_ISOLATION_POLICY:PASS`

2. Monorepo caller split wiring check:
   - command: `python - <<'PY' ... assert split wiring tokens in main_novaic.py/start_all_services.sh/start_all_dev.sh ... print("TOOLS_CALLER_SPLIT_WIRING:PASS") PY`
   - expected_marker: `TOOLS_CALLER_SPLIT_WIRING:PASS`
