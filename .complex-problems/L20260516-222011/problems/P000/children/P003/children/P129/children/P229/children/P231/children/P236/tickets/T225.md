# Verify runtime durable payload handoff for heavy tool outputs

## Problem Definition

Runtime tool handlers and the Cortex bridge must separate public compact projections from raw heavy outputs. Shell/display-like outputs should be stored or referenced through durable payload/artifact metadata, while normal message history receives bounded text only.

## Proposed Solution

Trace runtime tool handling, shell result projection, display/media result behavior, and Cortex bridge write calls. Run focused runtime tests for shell result projection, display/media handling, and no historical tool image/base64 injection.

## Acceptance Criteria

- Runtime shell/display-like handoff paths are mapped with file/function pointers.
- Evidence shows compact public text is separated from raw durable payload/artifact data.
- Focused runtime tests pass for projection and historical context boundaries.

## Verification Plan

Use `rg` and line-numbered inspection over `novaic-agent-runtime` tool handlers/context client code. Run focused tests under `novaic-agent-runtime/tests` covering shell projection, media boundaries, and historical tool image injection.

## Risks

- Display is now partly outside shell and may have a different result shape; inspect both shell CLI artifact manifests and direct display tool results where present.
- Passing tests may not cover every CLI command; note any remaining surface for `P230` guidance/schema review.

## Assumptions

- Cortex workspace persistence is solved separately by `P235`.
