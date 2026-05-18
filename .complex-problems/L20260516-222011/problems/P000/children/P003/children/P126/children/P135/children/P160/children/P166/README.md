# Cortex prepare handler response shape map

## Problem

`handle_cortex_prepare_llm_context` shapes the prepared messages/tools returned to the saga. Its inputs, output fields, and any local fallback reads must be mapped so the saga receives only the intended prepared snapshot.

## Success Criteria

- `cortex_handlers.py` prepare handler is mapped with line pointers for payload parsing, bridge prepare call, messages/tools/tool_names output, no-tool warning, and active stack injection.
- Any `read_context` or local continuity use inside the handler is classified as active-safe, dead, or stale.
- Existing handler tests are identified and run, or a focused guard is added if response shape is unguarded.
