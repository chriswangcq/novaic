# Attach generation contract inventory check

## Summary

Success for P496 only. The read-only inventory inspected the required attach paths, saved raw and classified artifacts, and explicitly routed the remaining builder-boundary hardening to P497 instead of treating it as solved.

## Evidence

- Result R483 records a completed read-only attach generation inventory.
- Raw search output is saved at `.complex-problems/L20260516-222011/tmp/p496/attach-generation-raw-guards.txt`.
- File inventory is saved at `.complex-problems/L20260516-222011/tmp/p496/attach-generation-files.txt`.
- Classification is saved at `.complex-problems/L20260516-222011/tmp/p496/attach-generation-classification.md`.
- The classification covers `runtime_handlers.py`, `session_outbox.py`, `session_repo.py`, `session_effects.py`, and focused attach tests.

## Criteria Map

- Runtime attach handler, session outbox publisher, attach effect builder, and session repo attach-race handling are inspected: satisfied by the classification sections for strict runtime validation, durable outbox boundary, repository race guard, and cleanup candidate for `build_attach_input_effect()`.
- Raw and classified artifacts are saved: satisfied by the raw guard, file list, and classification artifacts.
- Missing or ambiguous attach-generation contract becomes follow-up instead of being waved away: satisfied because R483 names `build_attach_input_effect()` as a known gap and routes it to P497.

## Execution Map

- T488 was a read-only inventory ticket.
- R483 records no source changes, matching the ticket acceptance criteria.
- The unresolved builder hardening is intentionally left for the already-split child P497, which is the next implementation ticket under P490.

## Stress Test

- Plausible failure mode: a one-go inventory could falsely claim the attach contract is fully strict while hiding that `build_attach_input_effect()` still accepts `None`.
- The result did not hide that issue; it named it as a cleanup candidate and kept it in the P490 work tree through P497.

## Residual Risk

- P496 does not harden code. The remaining risk is deliberately scoped to P497 and must be closed before P490 can be considered complete.
- No active no-generation attach delivery path was found in this inventory, but P497/P498 still need implementation and verification evidence.

## Result IDs

- R483
