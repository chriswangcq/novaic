# T090 Result: CI and Lint Helper Residue Scan

## Summary

Scanned CI and lint helper surfaces, cleaned stale compatibility-era wording, renamed the message-column guard from legacy naming to retired naming, and verified the touched guards.

## Scope

- `.github`
- `scripts/ci`

## Commands Run

```bash
rg -n "skip\(|pytest\.mark\.skip|xfail|TODO|FIXME|compat|fallback|legacy|migration|direct[-_ ]tool|base64|pass\b" .github scripts/ci -g '*'
bash -n scripts/ci/lint_chat_messages_read.sh
bash -n scripts/ci/lint_subagent_status.sh
bash -n scripts/ci/lint_retired_message_columns.sh
bash -n scripts/ci/lint_lifecycle.sh
python3 -m py_compile scripts/ci/check_start_config_contract.py scripts/ci/test_no_legacy_file_hot_paths.py
./scripts/ci/lint_chat_messages_read.sh
./scripts/ci/lint_subagent_status.sh
./scripts/ci/lint_retired_message_columns.sh
./scripts/ci/lint_lifecycle.sh
python3 scripts/ci/check_start_config_contract.py
python3 scripts/ci/test_no_legacy_file_hot_paths.py
```

## Changes

- `.github/workflows/lint.yml`: renamed the workflow step to `retired-message-columns lint` and pointed it at `lint_retired_message_columns.sh`.
- `scripts/ci/lint_legacy_message_columns.sh` -> `scripts/ci/lint_retired_message_columns.sh`: renamed the guard and updated internal allowlist/output text.
- `scripts/ci/lint_chat_messages_read.sh`: removed stale PR/sunset/fallback/compat language and made the allowlist empty/current-owned.
- `scripts/ci/lint_subagent_status.sh`: replaced rolling-restart/back-compat shim wording with final-state retired endpoint language and removed the obsolete entangled-client allowlist entry.
- `scripts/ci/lint_lifecycle.sh`: removed “historical migration” wording from the active-path rationale.
- `scripts/ci/check_start_config_contract.py` and `scripts/ci/test_no_legacy_file_hot_paths.py`: reduced stale visible wording while preserving retired-path guards.

## Findings

- Remaining `legacy` / `migration` scan hits are guard data for retired path detection or active policy regexes, not compatibility branches.
- The active `record_subagent_transition` write shim is gone; only the GET transition-history route remains in `entangled_client.py`.

## Verification

- Shell syntax checks passed for touched shell guards.
- Python compile passed for touched Python guards.
- Focused CI guard scripts passed:
  - `lint_chat_messages_read.sh`
  - `lint_subagent_status.sh`
  - `lint_retired_message_columns.sh`
  - `lint_lifecycle.sh`
  - `check_start_config_contract.py`
  - `test_no_legacy_file_hot_paths.py`

## Result

CI/lint helper stale wording was cleaned where safe. Remaining residue terms are intentional guard inputs.
