# Cortex explicit projection modes check

## Status

success

## Result IDs

- R000

## Evidence

- Cortex has explicit history/current/display/monitor projection functions.
- Runtime sends `projection` through step-ref expansion.
- Runtime projection selection is based on round and explicit display tool identity.
- Focused Cortex and Runtime tests pass.

## Criteria Map

- Cortex exposes explicit projection functions: satisfied.
- Runtime chooses projection mode from message round/tool identity: satisfied.
- Historical and current non-display tool outputs do not inline legacy image data: satisfied by Cortex projection-mode tests.
- Current explicit `display` can still produce provider-visible image content: satisfied by display perception test and Runtime display projection selection test.
- Focused tests pass: satisfied.

## Execution Map

- Added projection functions in Cortex.
- Added API/bridge/client projection propagation.
- Added Runtime selector for history/current/display modes.
- Verified with focused test suites and residue search.

## Stress Test

- A current non-display tool with legacy `display_files` maps to `current_tool_result` and remains text-only.
- A previous-round `display` tool maps to `history` and remains text-only.
- A current `display` tool maps to `display_perception` and may inline visual content.

## Residual Risk

- `format_for_llm(include_display=...)` remains as a compatibility wrapper for legacy tests/callers, but new Runtime path uses explicit projection.
