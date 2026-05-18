# Runtime bridge endpoint inventory

## Problem

The runtime-to-Cortex bridge may still call context, payload, and tool-result endpoints through old helper names. Before changing behavior, create a precise inventory of all bridge callers and endpoint owners.

## Success Criteria

- Search artifacts list every runtime/Cortex caller of `/v1/context/read`, `/v1/context/append`, `/v1/context/batch`, `/v1/payload/*`, `/v1/tool-result/*`, `read_context`, `append_context`, `batch_context`, `prepare_for_llm`, and projection helpers.
- Each hit is classified as live agent loop, notification injection, debug/inspection, bounded payload inspection, test-only, or unresolved.
- No implementation change is made in this child except evidence files.
- Unresolved hits are carried into later child problems.
