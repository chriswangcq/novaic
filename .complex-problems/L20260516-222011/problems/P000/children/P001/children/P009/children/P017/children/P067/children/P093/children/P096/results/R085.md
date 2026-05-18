# T091 Result: MCP Scripts CI Final Residue Sweep

## Summary

Ran the final MCP/scripts/CI sweep, found generated Python artifacts in bundled MCP resources, removed them from both app resource copies, and reran representative checks successfully.

## Commands Run

```bash
rg -n "skip\(|pytest\.mark\.skip|xfail|TODO|FIXME|compat|fallback|legacy|migration|direct[-_ ]tool|base64|pass\b" novaic-mcp-vmuse/tests docs/mcp-vmuse .github scripts/ci $(cat /tmp/novaic-nonci-script-files.txt) -g '*'
pytest -q scripts/ci/test_app_resource_hygiene.py
./scripts/ci/lint_chat_messages_read.sh
./scripts/ci/lint_subagent_status.sh
./scripts/ci/lint_retired_message_columns.sh
./scripts/ci/lint_lifecycle.sh
python3 scripts/ci/check_start_config_contract.py
python3 scripts/ci/test_no_legacy_file_hot_paths.py
cd novaic-mcp-vmuse && pytest -q
```

## Changes

- Removed generated Python cache artifacts from:
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/__pycache__`
  - `novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/__pycache__`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/__pycache__`
  - `novaic-app/src-tauri/gen/apple/assets/novaic-mcp-vmuse/src/novaic_mcp_vmuse/tools/__pycache__`

## Findings

- The final sweep initially failed `scripts/ci/test_app_resource_hygiene.py` because bundled MCP resources had `.pyc` files.
- After cleanup, resource hygiene passed.
- Remaining residue scan hits are intentional guard strings or ordinary prose (`pass` as a verb).

## Verification

- `scripts/ci/test_app_resource_hygiene.py`: 2 passed.
- CI guard scripts passed:
  - `lint_chat_messages_read.sh`
  - `lint_subagent_status.sh`
  - `lint_retired_message_columns.sh`
  - `lint_lifecycle.sh`
  - `check_start_config_contract.py`
  - `test_no_legacy_file_hot_paths.py`
- `novaic-mcp-vmuse`: 1 test passed.

## Result

Final sweep closed one real generated-artifact residue and verified the bounded MCP/scripts/CI surfaces.
