# Round 009 Dispatch - Tools Team

## Objective
Finalize runner support policy with CI sync enforcement and replay stability.

## Mandatory Tasks
1. Add CI check to ensure runner policy doc and preflight script remain synchronized.
2. Replay leak probe + reliability suite with timestamped evidence.
3. Publish final support statement for non-Linux runner strategy.

## Acceptance Commands
- `bash scripts/tools/ci_preflight_probe_prereqs.sh`
- `bash scripts/tools/leak_probe.sh`
- `pytest -q tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_reliability_policy.py`

## Due / Status
- due: 2026-02-24 18:00
- status: DONE
