# Round 004 Dispatch - Tools Team

## Objective
Keep reliability proofs fresh and reproducible.

## Mandatory Tasks
1. Re-run leak probe and reliability test bundle.
2. Provide one replay run output from CI or local with timestamp.
3. Report any environment prerequisites that may cause false negatives.

## Acceptance Commands
- `bash scripts/tools/leak_probe.sh`
- `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`
- `pytest -q tests/unit/common/test_strict_config.py`

## Due / Status
- due: 2026-02-23 18:00
- status: DONE
