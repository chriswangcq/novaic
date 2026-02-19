# Round 005 Dispatch - Tools Team

## Objective
Make reliability replay robust across environments with no hidden prerequisite debt.

## Mandatory Tasks
1. Add fallback behavior or explicit fail-fast message when `lsof/pgrep` missing.
2. Add CI preflight step for probe prerequisites.
3. Run one high-concurrency replay and publish deterministic bound evidence.

## Acceptance Commands
- `bash scripts/tools/leak_probe.sh`
- `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
- `pytest -q tests/unit/common/test_strict_config.py`

## Due / Status
- due: 2026-02-25 18:00
- status: DONE
