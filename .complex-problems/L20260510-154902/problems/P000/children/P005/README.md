# Phase 4: Prepare/read-path cutover from events

## Problem

Cut `prepare_for_llm`, context status, stack reads, and relevant Runtime bridge behavior over to event-source/projection semantics instead of DFS file source semantics.

## Success Criteria

- `prepare_for_llm` uses event replay/projection as the primary path.
- DFS file traversal is removed as source-of-truth or restricted to explicit repair/debug projection checks.
- Runtime prepare flow no longer depends on call-time DFS scan of legacy source files.
- Tests prove prepared messages match event semantics across active wake, closed summaries, nested skills, tools, and notifications.
