# Ticket: ContextEvent lifecycle final verification

## Goal

Run a final, skeptical verification pass over the ContextEvent lifecycle cleanup group and confirm the completed child tickets compose into a clean lifecycle boundary.

## Scope

- Review closed child outcomes for:
  - store and writer contract audit
  - projection and read-model cleanup
  - workspace step and payload normalization cleanup
  - API lifecycle endpoint cleanup
- Re-run focused guards and tests that prove:
  - tool payloads are pointer/projected instead of inlined into history
  - display/image expansion is display-only
  - ContextEvent writers/readers remain explicit and deterministic
  - workspace payload storage remains inspectable without polluting model context

## Out of Scope

- Archive/direct scope-end cleanup owned by sibling tickets outside the ContextEvent lifecycle group.
- Business queue/session FSM cleanup.

## Success Criteria

- The final verification names every closed child result/check it relies on.
- No unclassified ContextEvent lifecycle residue remains.
- Focused tests pass.
- Any discovered gap is split into a follow-up instead of being hand-waved.
