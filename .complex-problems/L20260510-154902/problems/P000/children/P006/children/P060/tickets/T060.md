# Source-of-truth language and artifact cleanup

## Problem Definition

After the event-source cutover, comments/docs/tests must not imply `context.jsonl`, `steps`, or `summary.md` are the active LLM source of truth. Materialized files can remain only as projection, debug, inspection, or archive artifacts.

## Proposed Solution

- Scan source/tests/docs for source-of-truth wording around materialized artifacts and DFS.
- Rewrite misleading comments/docstrings to say event stream is authoritative and materialized files are projection/debug artifacts.
- Leave legitimate artifact tests intact when they verify persistence/projection behavior rather than active read source behavior.
- Run focused static scan and full tests.

## Acceptance Criteria

- Active source-of-truth wording points to ContextEvents/event projection.
- Materialized artifact wording is explicitly projection/debug/inspection where applicable.
- No comments imply DFS is the current API LLM prepare source.
- Full Cortex tests pass.

## Verification Plan

- Static scans for `source of truth`, `authoritative`, `ContextEngine`, `context.jsonl`, `summary.md`, and `steps`.
- Run full Cortex tests.

## Risks

- Some user-facing tool descriptions still mention `summary.md` because skill summaries are visible artifacts. Those are valid if not source-of-truth claims.

## Assumptions

- This ticket changes wording/guards only; physical code deletion is handled separately.
