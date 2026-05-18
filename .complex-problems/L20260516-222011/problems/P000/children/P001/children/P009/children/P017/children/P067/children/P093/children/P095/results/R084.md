# T088 Result: Scripts and CI Helper Residue Scan

## Summary

Split the scripts/CI residue scan into repository scripts and CI/lint helpers. Both child problems completed successfully: one non-CI script wording was cleaned, CI guard language was tightened, and representative checks passed.

## Children Closed

- P097 / R082 / C096: Repository scripts scan.
- P098 / R083 / C097: CI and lint helper scan.

## Changes Rolled Up

- `scripts/start.sh`: replaced stale fallback wording with explicit workspace path wording.
- `.github/workflows/lint.yml`: renamed the message-column guard step.
- `scripts/ci/lint_legacy_message_columns.sh` -> `scripts/ci/lint_retired_message_columns.sh`.
- `scripts/ci/lint_chat_messages_read.sh`: removed stale survivor/sunset/fallback wording.
- `scripts/ci/lint_subagent_status.sh`: changed back-compat shim language to retired endpoint guard language.
- `scripts/ci/lint_lifecycle.sh`, `scripts/ci/check_start_config_contract.py`, and `scripts/ci/test_no_legacy_file_hot_paths.py`: cleaned stale visible residue while preserving guard intent.

## Verification

- `bash -n scripts/start.sh`
- `bash -n novaic-blob-service/scripts/verify_contract_version_blob.sh`
- `bash -n` for touched CI shell guards.
- `python3 -m py_compile` for touched Python guards.
- Focused guard scripts passed.

## Result

The scripts/CI helper scope is closed with intentional guard terms preserved and stale wording removed.
