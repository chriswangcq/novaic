# T086 Result: MCP Scripts and CI Test Residue Scan

## Summary

Split MCP/scripts/CI residue review into MCP tests, scripts/CI helpers, and a final sweep. All children completed successfully; stale wording was cleaned, generated MCP resource artifacts were removed, and representative checks passed.

## Children Closed

- P094 / R081 / C095: MCP test residue scan.
- P095 / R084 / C098: Scripts and CI helper residue scan.
- P096 / R085 / C099: Final residue sweep.

## Changes Rolled Up

- `scripts/start.sh`: cleaned stale fallback wording.
- `.github/workflows/lint.yml`: renamed message-column guard step.
- `scripts/ci/lint_legacy_message_columns.sh` -> `scripts/ci/lint_retired_message_columns.sh`.
- `scripts/ci/lint_chat_messages_read.sh`: removed stale survivor/sunset/fallback wording.
- `scripts/ci/lint_subagent_status.sh`: changed back-compat shim language to retired endpoint guard language.
- `scripts/ci/lint_lifecycle.sh`, `scripts/ci/check_start_config_contract.py`, and `scripts/ci/test_no_legacy_file_hot_paths.py`: cleaned stale visible residue while preserving guard behavior.
- Removed Python `__pycache__/.pyc` artifacts from bundled MCP resources under both Tauri resource copies.

## Verification

- MCP package tests passed.
- Non-CI script shell syntax checks passed.
- CI guard scripts passed.
- App resource hygiene passed after artifact cleanup.

## Result

The MCP/scripts/CI residue slice is closed with stale residue removed and remaining guard strings classified as intentional.
