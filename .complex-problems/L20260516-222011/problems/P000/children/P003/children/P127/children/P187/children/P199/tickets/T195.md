# Remove stale production projection branches

## Problem Definition

The projection inventory identified production code that appears stale or actively dangerous because it can inline images/base64 into LLM text paths. The cleanup must remove truly dead production branches while preserving current active projection paths and justified compatibility/defensive branches.

## Proposed Solution

Physically remove the stale `resolve_for_llm` production helper and any exports/imports that exist only for that helper. Then inspect nearby production projection code for branch residue introduced by the old helper and keep only branches that are still needed by current `tool-output.v1`, display, shell, and history projection contracts. If a branch is retained, document why in the result rather than leaving it as unexplained compatibility.

## Acceptance Criteria

- Production stale branches classified by the inventory are removed.
- No code path can inline image/base64 payloads into LLM text through the removed helper.
- Active production projections for shell text, artifact manifests, current display image projection, and historical display manifest remain intact.
- Retained compatibility/defensive branches have explicit rationale in the result.
- No broad local-only or hidden fallback is introduced.

## Verification Plan

Run focused Cortex projection tests after edits, then run any directly impacted runtime/factory projection tests if imports or contracts are touched.

## Risks

- Removing a helper that is only test-referenced may still break undocumented external imports.
- Over-cleaning nested defensive branches could break persisted historical payload formats.
- Under-cleaning would leave misleading old logic that future agents may accidentally revive.

## Assumptions

- The repository tests and `rg` caller inventory are sufficient to identify live in-repo callers.
- Historical persisted data compatibility should be preserved unless the branch is proven stale or unsafe.
