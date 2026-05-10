# Verify projection boundaries and non-cutover

## Problem Definition

Phase 2 added a pure ContextEvent projector. P017 must verify that projection semantics are covered and that current endpoints/read paths have not been silently cut over or double-wired before the explicit read-path phase.

## Proposed Solution

- Run focused projection/substrate tests.
- Run relevant existing ContextEngine tests.
- Run full Cortex tests.
- Static scan projector for Workspace/DFS/IM/payload dependencies.
- Static scan current API/runtime/context stack references to ensure no accidental read-path cutover.
- Record residual integration gaps for P004/P005/P006.

## Acceptance Criteria

- Focused projection tests pass.
- Existing ContextEngine/context tests pass.
- Full Cortex suite passes.
- Projector is pure and has no Workspace, IM body, payload file, `context.jsonl`, `summary.md`, or `steps/_index` reads.
- Current endpoints are not yet cut over to the projector.

## Verification Plan

- Run `pytest` commands with sibling dependency `PYTHONPATH`.
- Run `rg` scans for hidden dependencies and accidental references.
- Review git status/diff names.

## Risks

- Existing dirty worktree includes prior DFS engine changes; the result must distinguish them from new projection substrate work.

## Assumptions

- Actual endpoint cutover is explicitly tracked by later phases and should not occur here.
