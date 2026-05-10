# Audit DFS read fallback removal

## Problem Definition

After P055/P056, the API prepare/status usage paths should no longer use DFS `ContextEngine`. This ticket performs the static/runtime audit so no fallback read source remains hidden in active API semantics. It also classifies or removes legacy tests/docs that would mislead future agents about the authoritative read path.

## Proposed Solution

- Scan Cortex source/tests for `ContextEngine`, `prepare_messages_for_llm`, `read_context`, `StepTree`, materialized `summary.md`/step read fallback language, and `_collect_active_stack`.
- Classify each remaining usage into:
  - active API read source (must be removed),
  - operational control/LIFO/debug (allowed only if explicit),
  - legacy DFS engine module/tests (allowed only as quarantined legacy/debug coverage),
  - unrelated materialized projection verification tests.
- Remove or rewrite misleading active API tests/docs that still describe DFS as the current LLM context source.
- Add a static guard test proving prepare/status usage sections have no `ContextEngine` fallback.
- Run full Cortex tests.

## Acceptance Criteria

- API prepare/status sections have no `ContextEngine` or `prepare_messages_for_llm` fallback.
- Any remaining `ContextEngine` usage is outside active API read semantics and documented as legacy/debug coverage.
- Misleading test/module comments that describe DFS as the current prepare path are updated or removed.
- Full Cortex suite passes.

## Verification Plan

- Run targeted static scans.
- Run the new/updated static guard tests.
- Run full Cortex tests.

## Risks

- Deleting the DFS engine entirely may be larger than this ticket if many legacy rendering tests still cover it directly. Prefer quarantine/classification unless active source semantics are affected.
- `_collect_active_stack` still supports operational LIFO gates; do not delete it until skill lifecycle validation has an event-only replacement.

## Assumptions

- Full physical deletion of DFS engine is Phase 5 cleanup unless this audit finds it is already unused by active/runtime/API code.
- The user’s no-compat direction applies to active behavior; temporary legacy engine tests must not influence production path.
