# Cortex LLM DFS context assembly audit

## Problem

Audit novaic-cortex LLM context DFS assembly logic and determine whether it correctly assembles open scopes, folded completed scopes, tool projections, summaries, and ordering without hidden stale paths.

## Success Criteria

- Locate the active code path used to assemble LLM context from Cortex workspace state.
- Verify DFS traversal, fold/expand semantics, child summary behavior, and chronological ordering.
- Verify current tests cover the important invariants and run focused tests.
- Identify concrete bugs or residual design risks with file pointers.
- Avoid speculative changes; only recommend or patch if evidence is clear.

## Constraints

- Use pointer-oriented inspection; do not paste large raw JSON or unrelated files.
- Treat this as a code/design audit unless a clear correctness bug appears.
- Keep results tied to exact files, functions, and tests.
