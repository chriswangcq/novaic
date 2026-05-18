# Finalize/session-ended generation ownership audit

## Problem Definition

Finalize, `session_ended`, watchdog, recovery, restart, and nested skill closure paths must not clear, restart, or archive a newer active session because an older saga/session completion arrives late. This ticket audits the full boundary and fixes any stale-generation or missing-generation behavior found.

## Proposed Solution

Audit and close the finalize generation boundary in small slices:

1. Inventory every finalize/session-ended entry point in `novaic-agent-runtime`, including repository APIs, outbox effects, task handlers, watchdog/recovery paths, and skill-end/remaining-stack archival paths.
2. For each entry point, map the explicit keys carried across the boundary:
   - saga id
   - wake scope id
   - session generation
   - end reason
   - remaining stack
   - pending input/restart intent
3. Verify current-generation checks occur inside the same mutation boundary that clears active state, restarts pending input, or records archive/finalize facts.
4. Fix any path that clears active state or restarts/archives based only on stale saga id, stale wake scope id, implicit active lookup, or missing generation.
5. Add focused tests proving stale finalize/session-ended events cannot mutate a newer active generation, and proving missing generation fails closed where applicable.
6. Run focused session/FSM tests and source guards for legacy finalize compatibility residue.

If this ticket becomes too broad, split into child problems for:

- finalize entry-point inventory
- repository mutation atomicity
- outbox/worker delivery enforcement
- runtime handler enforcement
- remaining stack/reason archival
- aggregate stale-generation regression coverage

## Acceptance Criteria

- All finalize/session-ended entry points are mapped with file references and explicit generation/session keys.
- Active clearing, pending restart, and remaining-stack archive paths are protected by current-generation checks at the mutation boundary.
- Missing or stale generation behavior is classified and fixed if unsafe.
- End reason and remaining stack are recorded at the generation boundary where finalize/archive occurs.
- Tests prove stale finalize/session-ended events do not close or mutate a newer active generation.
- No stale compatibility helper remains that silently falls back to generation `1` or current active generation for finalize/session-ended mutations.

## Verification Plan

- Use `rg` to inventory finalize/session-ended/watchdog/recovery/restart/remaining-stack paths.
- Inspect repository and handler code with line references.
- Add or update focused pytest coverage in `novaic-agent-runtime/tests`.
- Run focused test suites around session FSM, outbox, recovery, generation checked attach/finalize, and legacy cleanup.
- Run source guards for fallback generation defaults and direct active-session clearing outside the expected repository/FSM boundary.

## Risks

- Finalize paths may cross several layers, so a one-go implementation could miss a side path.
- Some historical tests may encode old compatibility behavior and need careful deletion or rewrite rather than expansion.
- Restart and pending input handling may interact with active-session state and outbox delivery in subtle ways.

## Assumptions

- P327 already closed attach expected-generation behavior; this ticket focuses on finalize/session-ended surfaces.
- The project does not need backward compatibility for unsafe missing-generation finalize payloads.
- It is acceptable to split this ticket into smaller ledger children before implementation if the inventory shows multiple independent surfaces.
