# Cortex compatibility residue cleanup ticket

## Problem Definition

The compatibility inventory may contain Cortex-side residue around session generation defaults, active-state lookup, archive diagnostics, context event lifecycle, and operational metadata. Live Cortex paths must not silently accept missing/stale generation or revive old active-state behavior.

## Proposed Solution

Audit Cortex hits from the P402 inventory in small responsibility slices:

1. Inspect context stack / context event lifecycle code for generation or archive defaults.
2. Inspect operational/archive paths for active-state lookup or compatibility diagnostics.
3. Inspect API/CLI/bridge surfaces that read or expose Cortex context state.
4. Classify legitimate projection/diagnostic/counter references explicitly.
5. Patch dangerous live compatibility branches with explicit validators or remove them outright.
6. Add focused Cortex tests for changed boundaries.
7. Rerun Cortex guard searches and focused tests until no unclassified live Cortex residue remains.

## Acceptance Criteria

- Every Cortex hit from the inventory is classified as fixed, safe validator/test, safe diagnostic/projection/counter, or non-live historical residue.
- Dangerous live Cortex defaults or active-state compatibility branches are removed.
- Changed live Cortex boundaries have focused tests.
- Cortex guard searches have no unclassified generation/active-state/archive compatibility residue.
- Cortex-focused tests pass.

## Verification Plan

- Reuse P402 guard outputs and run Cortex-specific guards excluding `.venv` and generated caches.
- Run focused `novaic-cortex` tests around context event API, scope summary/archive behavior, context assembly, and any patched code.
- If a slice is too broad or ambiguous, split into child tickets before editing.

## Risks

- Some Cortex references are diagnostic metadata rather than live authority; deleting by regex could remove useful audit context.
- Context event lifecycle code may interact with LogicalFS/Workspace state, so boundary tests need explicit setup.
- Historical archived summaries may contain old terms; these should be classified as non-live artifacts, not patched.

## Assumptions

- No backward compatibility is required for missing/stale generation in live Cortex paths.
- Historical ledger/problem-package text is not live runtime behavior unless loaded into code paths under test.
