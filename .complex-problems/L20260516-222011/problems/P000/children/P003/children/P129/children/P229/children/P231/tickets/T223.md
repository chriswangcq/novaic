# Map and verify durable payload refs in tool step write path

## Problem Definition

The active tool execution/write path must not store heavy raw tool output directly in normal step records. It should carry a compact observation/projection for history while durable payload content is written under a `payload_ref` and associated with a `step_ref`.

## Proposed Solution

Trace representative shell/display-like tool handler output through runtime/Cortex bridge code and Cortex workspace step writing. Inspect the exact functions that create durable payload records, record steps, and attach refs. Run focused tests that exercise step write and shell/display projection behavior.

## Acceptance Criteria

- Tool handler output path into Cortex step writing is mapped with file/function pointers.
- Workspace step write code evidence shows durable payload storage and `payload_ref`/`step_ref` metadata.
- Focused tests or probes confirm refs are emitted and raw payload does not replace compact step output for representative heavy outputs.

## Verification Plan

Use `rg` and line-numbered inspection over runtime tool handlers/Cortex bridge plus `novaic-cortex/novaic_cortex/workspace.py`. Run focused tests for context event API step writes, step indexing, shell projection, and display/media projection if present.

## Risks

- Shell and display paths may be separated between runtime and Cortex packages; missing one path would create false confidence.
- Historical compatibility data can contain inline content; this ticket should distinguish historical records from active write behavior.

## Assumptions

- Explicit payload read APIs are already audited in `P228` and do not need re-verification here.
