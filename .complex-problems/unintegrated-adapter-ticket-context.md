# Audit Context Event Source Cutover

## Problem Definition

Audit whether Cortex LLM context assembly has fully cut over to the context event source model, and identify any remaining live DFS/projection fallback or misleading old context-stack code.

## Proposed Solution

Inspect the Cortex context preparation APIs, event store/read model code, context-stack modules, and guard tests. Separate active LLM assembly paths from historical/debug projection reads.

## Acceptance Criteria

- Confirm whether `prepare_for_llm` and active context assembly require context events rather than old DFS projections.
- Identify any remaining active fallback from `/ro/scopes`, `context.jsonl`, `summary.md`, or old stack types.
- Identify dead or misleading compatibility residue that should be cleaned later.
- Record concrete file evidence.

## Verification Plan

- Use `rg` to find context event store/read-model/prepare paths and legacy DFS references.
- Inspect targeted code slices rather than loading large files.
- Inspect tests that guard no-compat/no-DFS behavior.

## Risks

- History/debug endpoints may legitimately read archived projections; incorrectly classifying them as active assembly bugs would create false positives.

## Assumptions

- Active LLM assembly path means the code path that builds messages for current model calls, not read-only history inspection endpoints.
