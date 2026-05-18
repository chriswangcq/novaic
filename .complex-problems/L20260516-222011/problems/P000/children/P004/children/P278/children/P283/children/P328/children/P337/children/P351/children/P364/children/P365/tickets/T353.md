# Ticket: Remove Startup Rebuild Generation Default

## Objective

Make startup session rebuild obey the explicit session identity contract: a running saga context without positive `session_generation` must not be projected as an active session.

## Implementation Scope

- Change `novaic-agent-runtime/queue_service/session_rebuild.py` so it parses `context["session_generation"]` explicitly.
- Reject/skip missing, boolean, non-numeric, zero, and negative generation values.
- Preserve valid positive integer and positive numeric string values.
- Avoid introducing fallback compatibility branches.

## Tests

- Add focused tests in `novaic-agent-runtime/tests/test_pr279_session_rebuild_projector_boundary.py` or a nearby existing rebuild test.
- Cover:
  - Missing `session_generation` is skipped.
  - Invalid values (`0`, `"0"`, `"bad"`, `False`) are skipped.
  - Valid values (`3`, `"4"`) are projected exactly.
- Run the focused rebuild tests and relevant session residue guards.

## Success Criteria

- `session_rebuild.py` no longer contains `session_generation") or 1` or equivalent missing-generation default.
- Startup rebuild cannot fabricate generation `1`.
- Focused tests pass.
- Residue search for rebuild generation defaults is clean.
