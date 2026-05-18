# Finalize Watchdog and Recovery Ownership Audit

## Problem Definition

P280 must audit the ownership boundary between normal wake finalize, watchdog/suspected-dead detection, recovery wake creation, and remaining-stack archival. The risk is that multiple paths might independently mutate session state or archive scopes instead of routing through explicit event/FSM/outbox ownership.

## Proposed Solution

Map the finalize/recovery code paths with file references, classify ownership boundaries, run focused tests around suspected-dead recovery/finalize/session-ended behavior, and add or tighten tests if the audit finds an active gap.

## Acceptance Criteria

- Finalize, suspected-dead/watchdog, recovery archive, recovery wake creation, and remaining-stack archival paths are mapped with file references.
- Ownership is classified as event/FSM/outbox-oriented or as a concrete gap.
- Any active gap is fixed or split into a smaller follow-up problem.
- Focused recovery/finalize tests pass.
- A durable audit artifact is saved under the ledger.

## Verification Plan

Use `rg`/bounded file slices to map code paths, save an ownership matrix, run focused tests (`suspected_dead`, `recovery`, `finalize`, `session_ended`, saga compensation), and record whether source changes were required.

## Risks

- Some watchdog/recovery terms are intentional compensation paths; deleting them blindly would damage recovery.
- Existing prior diffs can make raw git diff noisy; evidence must cite focused artifacts.

## Assumptions

- P279 already cleaned finalize/session compatibility residue, so P280 can focus on ownership and recovery semantics.
