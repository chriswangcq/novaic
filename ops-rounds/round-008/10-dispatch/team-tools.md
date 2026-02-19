# Round 008 Dispatch - Tools Team

## Objective
Finalize environment dependency policy with explicit long-term support statement.

## Mandatory Tasks
1. Publish final policy statement for runner OS support and fallback strategy.
2. Keep reliability replay green and attach timestamped evidence.
3. Add one verification that CI preflight script and policy doc stay in sync.

## Acceptance Commands
- `bash scripts/tools/ci_preflight_probe_prereqs.sh`
- `bash scripts/tools/leak_probe.sh`
- `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE
