# Round 006 Dispatch - Tools Team

## Objective
Maintain deterministic reliability and prove no environment-specific blind spots.

## Mandatory Tasks
1. Replay leak probe and reliability test bundle with timestamp.
2. Verify CI prerequisite step behavior on clean runner assumptions.
3. Document any remaining host dependency caveat with explicit mitigation.

## Acceptance Commands
- `bash scripts/tools/leak_probe.sh`
- `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
- `pytest -q tests/unit/common/test_strict_config.py`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE
