# Round 007 Dispatch - Tools Team

## Objective
Finalize host-dependency policy decision and keep replay deterministic.

## Mandatory Tasks
1. Finalize policy choice for non-Linux runner handling (A/B/C from Round 006).
2. Reflect chosen policy in script/docs/CI comments.
3. Replay leak probe + reliability suite and attach timestamped evidence.

## Acceptance Commands
- `bash scripts/tools/leak_probe.sh`
- `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
- `pytest -q tests/unit/common/test_strict_config.py`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE
