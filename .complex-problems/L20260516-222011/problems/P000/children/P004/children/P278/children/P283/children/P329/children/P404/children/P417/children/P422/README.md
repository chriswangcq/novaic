# ContextEvent projection and read-model cleanup

## Problem

ContextEvent projection/read-model code may contain legitimate projection state, but it must not silently revive old compatibility channels or inline payload behavior.

## Success Criteria

- Inspect `context_event_projection.py`, `context_event_read_model.py`, and related projection tests.
- Classify generation/archive/context hits as read-model state, diagnostics, or dangerous compatibility residue.
- Patch dangerous compatibility behavior if found.
- Add or update focused projection/read-model tests for changed behavior.
- Run projection/read-model tests.
