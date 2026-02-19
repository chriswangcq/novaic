# Round 003 Dispatch - Tools Team

## Objective
Maintain reliability baseline and provide replayable evidence for leak and timeout controls.

## Mandatory Tasks
1. Re-run leak probe and reliability tests; refresh evidence.
2. Add one stress variant with higher concurrency and report max_running bound.
3. Ensure reliability config schema checks run in CI path.

## Acceptance Commands
- `bash scripts/tools/leak_probe.sh`
- `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
- `pytest -q tests/unit/common/test_strict_config.py`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE
