# Finalize/session-ended entry-point inventory

## Problem Definition

We need a complete, evidence-backed map of every finalize/session-ended/recovery/watchdog/restart/skill-end path before modifying more finalize behavior. Missing an entry point is the main risk because stale completion may still clear or archive a newer active session through an unexamined path.

## Proposed Solution

Perform a read-only source inventory of `novaic-agent-runtime`:

1. Search for finalize/session-ended/recovery/watchdog/restart/skill-end terms across `queue_service`, `task_queue`, and tests.
2. Map each entry point with file references and classify its role:
   - repository/API mutation
   - outbox effect build/delivery
   - runtime handler/task handler
   - watchdog/recovery producer
   - skill-end/remaining-stack archival
   - test-only or compatibility residue
3. For each live path, record whether saga id, wake scope id, session generation, reason, remaining stack, pending input ids, and restart intent are explicit.
4. Classify paths as safe, unsafe, or delegated to P335-P339.
5. Record existing tests that exercise each path and gaps that need implementation tickets.

## Acceptance Criteria

- Inventory covers all live finalize/session-ended/recovery/watchdog/restart/skill-end paths found by source search.
- Each live path has explicit file references and carried-key classification.
- Each path is labeled safe, unsafe, or delegated to a specific child problem.
- Existing tests and missing coverage are listed.
- No implementation changes are made in this inventory ticket.

## Verification Plan

- Use `rg` with finalize/session/end/recovery/watchdog/restart/remaining stack terms.
- Inspect matching files with `sed`/`nl`.
- Cross-check tests with `rg` for related function/event names.
- Run no mutation or implementation in this ticket; the result is a source map.

## Risks

- Search terms may miss renamed concepts; mitigate by also searching session state events and outbox effect names.
- Some paths may be generated indirectly through FSM decision names; mitigate by reading session repo/outbox modules directly.

## Assumptions

- Inventory can be completed as a bounded one-go task because it is read-only and produces a map, not code changes.
- Unsafe paths discovered here will be handled by P335-P339 or explicit follow-up children.
