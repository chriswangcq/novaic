# Run final focused projection regression chain

## Problem Definition

The projection cleanup and Gemini provider fix need one final focused regression run across Cortex, runtime, and factory before parent closure. The result must also document any remaining intentional compatibility branches so stale fallback paths are not hidden.

## Proposed Solution

Run the focused test chain that covers Cortex step/tool output projection, runtime task-queue multimodal projection, and factory provider/log behavior. Then audit the remaining projection-related compatibility branches and summarize whether each is intentional or requires follow-up.

## Acceptance Criteria

- Cortex projection tests pass.
- Runtime projection/multimodal tests pass.
- Factory chat/log tests pass.
- Remaining intentional compatibility branches are explicitly listed with rationale.
- Any test failure or unclassified stale branch becomes a follow-up problem instead of being ignored.

## Verification Plan

Run the focused pytest commands for Cortex, runtime, and factory. Run targeted `rg` searches for removed stale symbols and remaining projection branch markers.

## Risks

- A broad full-repo test run may include unrelated slow or environment-dependent tests; keep this ticket focused on the projection chain.
- Some compatibility branch names may look legacy but still protect display/tool-result contracts; classify them carefully instead of deleting blindly.

## Assumptions

- Parent tickets already handled implementation and test additions; this ticket is final regression and branch accounting only.
