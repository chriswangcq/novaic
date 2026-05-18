# Step result projection stale branch cleanup ticket

## Problem Definition

Projection code now has newer shell/display/artifact contracts, but stale compatibility branches can still confuse future agents, preserve obsolete behavior, or make tests look broader than the live system. We need an explicit inventory and safe cleanup pass over production and test projection branches.

## Proposed Solution

Audit projection-related production paths and tests, especially Cortex step result projection and runtime multimodal/message preparation. Classify suspicious branches as active, test-only, compatibility, or stale. Remove stale production branches and stale tests when safe; if a branch is still active or intentionally defensive, document that classification in the result. Run focused projection tests after cleanup.

## Acceptance Criteria

- Inventory covers production projection code, runtime image/tool message conversion code, and projection-specific tests.
- Each suspicious branch is classified as active, test-only, compatibility, or stale.
- Stale code/tests are removed when safe, rather than left as misleading residue.
- If no code is removed, the result explains why every suspicious branch is still needed.
- Focused projection and multimodal tests pass after cleanup/classification.

## Verification Plan

Run targeted `rg` audits over projection keywords and run the focused Cortex/runtime/factory projection test suites that protect shell text, current display perception, historical manifest-only projection, and provider multimodal formatting.

## Risks

- Removing a compatibility branch too aggressively could break persisted historical step results.
- Keeping a stale branch because it looks harmless could reintroduce the exact "new code not connected, old path still live" failure mode.
- Tests may encode legacy behavior as if it were a supported contract; these need careful classification rather than blind deletion.

## Assumptions

- Backward compatibility with truly obsolete inline/base64 tool result shapes is not required unless current persisted Cortex data or active runtime paths still depend on it.
- Historical persisted data can be represented as manifest/text-only and should not need raw media in future LLM context.
