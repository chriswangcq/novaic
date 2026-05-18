# ContextEvent projection and read-model cleanup ticket

## Problem Definition

ContextEvent projection/read-model code turns append-only events into LLM-visible context. It must not leak large payloads, revive deprecated compatibility channels, or hide malformed event behavior behind permissive defaults.

## Proposed Solution

Inspect projection/read-model code and focused tests. Patch dangerous behavior if projection turns external payload references into inline content, accepts deprecated event shapes, or silently drops malformed state that should fail closed.

## Acceptance Criteria

- `context_event_projection.py` and `context_event_read_model.py` are inspected.
- Remaining generation/archive/context hits are classified as projection state, diagnostics, or cleanup candidates.
- LLM context projection remains pointer-oriented for tool payloads/artifacts.
- Dangerous compatibility behavior is patched if found.
- Focused projection/read-model tests pass.

## Verification Plan

- Read projection/read-model source slices.
- Run guards for inline payload/base64/result compatibility and deprecated summary channels.
- Run:
  - `tests/test_context_event_projection.py`
  - `tests/test_context_event_read_model.py`
  - `tests/test_context_event_read_source_guards.py`
  - `tests/test_tool_output_projection.py`

## Risks

- Projection code can intentionally summarize tool observations; do not delete useful summaries when the real problem is only large inline payload leakage.

## Assumptions

- Tool output payloads should stay as references/manifests in history unless explicitly loaded by display or payload tools.
