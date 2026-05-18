# Business/subscriber active documentation remediation ticket

## Problem Definition

P717 classified several active documentation lines as stale or ambiguous around Entangled, Gateway, Business, and product CRUD ownership. These lines can mislead future work into reintroducing Gateway product CRUD or confusing Business/subscriber boundaries.

## Proposed Solution

Patch only the safe active stale documentation identified by P717. Update `docs/entangled-architecture.md` to align Entangled/Gateway/Business ownership with current topology, and update `docs/gateway/rest-auth-and-deps.md` so Gateway REST docs do not claim generic product CRUD or device/vm ownership. Preserve historical notes only when clearly labeled as old behavior.

## Acceptance Criteria

- `docs/entangled-architecture.md` no longer says Gateway currently inherits Entangled SQL storage or that all entity CRUD writes flow through Gateway auth.
- `docs/gateway/rest-auth-and-deps.md` no longer implies Gateway owns generic product CRUD, devices, or VM orchestration.
- New wording matches current boundary docs: App uses Entangled sync/action, Business owns product action/entity writes, Gateway is auth/App WS/signaling/Blob edge, Device owns hardware execution.
- Changes are small and localized; no unrelated docs are rewritten.

## Verification Plan

Run focused `rg` scans for stale Gateway/CRUD/Business wording in the patched docs. Run existing docs/status lint if available and cheap. Review the diff for accidental broad rewrites.

## Risks

- Over-editing could erase useful historical context from `docs/entangled-architecture.md`.
- Some Gateway REST docs may still be true for auth/edge endpoints; avoid replacing them with a false blanket statement.

## Assumptions

- P717's disposition is current enough to guide this patch.
- Code behavior is not changed by this ticket.
