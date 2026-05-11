# agentctl Blob contract audit completed

## Summary

Audited generated `agentctl` CLI output paths. No active raw artifact stdout violation was found. The media path consumes Blob input and returns text; IM and subagent paths print JSON metadata/text only.

## Done

- Inspected `novaic-cortex/novaic_cortex/shell_capabilities.py` `agentctl im` implementation.
- Inspected `agentctl subagent spawn` implementation.
- Inspected `agentctl media audio-qa` implementation.
- Verified `audio-qa` requires `blob://` input via `_get_blob`, reads bytes from Blob Service, sends audio bytes only to Factory, and prints the text answer plus metadata.
- Verified IM reply currently sends `attachments: []`; IM read/history/search/context delegate bounded API responses and do not fetch attachment bytes.

## Verification

- Ran `PYTHONPATH=../novaic-common:../novaic-cortex:../novaic-logicalfs:../novaic-sandbox-sdk:. pytest -q tests/unit/task_queue/test_user_content.py tests/unit/task_queue/test_shell_output_contract.py tests/unit/task_queue/test_tool_output_contract.py` in `novaic-agent-runtime`.
- Result: `16 passed in 0.10s`.
- Ran `PYTHONPATH=../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk:. pytest -q tests/test_shell_capabilities_internal_auth.py tests/test_tool_schemas_limits.py tests/test_blob_payload_client.py` in `novaic-cortex`.
- Result: `16 passed in 0.68s`.

## Known Gaps

- No P005-blocking gaps found.
- This audit does not cover `devicectl` or `cortex payload`; those are tracked separately.

## Artifacts

- Audit evidence: `novaic-cortex/novaic_cortex/shell_capabilities.py` lines covering `_agentctl_im`, `_agentctl_subagent`, `_agentctl_media`, and `_get_blob`.
