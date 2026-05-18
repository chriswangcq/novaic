# Ticket: Verify ContextEvent projection guards

## Goal

Re-run focused ContextEvent projection tests and source guards to ensure tool payloads remain pointer/projected and display/image expansion cannot leak into history/current tool-result context.

## Acceptance Criteria

- Focused projection/workspace/API tests pass.
- Guard confirms no `stable_json(observation)` fallback remains in `context_event_projection.py`.
- Guard confirms `include_display=True` is display-perception-only.
- Any regression candidate is fixed or split into a follow-up.
