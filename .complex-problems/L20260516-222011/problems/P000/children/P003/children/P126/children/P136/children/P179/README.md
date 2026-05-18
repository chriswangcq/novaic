# Externalized payload regression coverage and ambiguity cleanup

## Problem

Even if individual layers look correct, regression coverage must prove externalized/blob-like payload refs do not break stable step lookup, do not leak raw payloads into public context, and do not leave compatibility branches that silently treat `step_ref` and `payload_ref` as interchangeable.

## Success Criteria

- Inventory tests covering externalized payload refs, artifact refs, public truncation, and display/media projection.
- Add missing tests that fail if `step_ref` and `payload_ref` are conflated.
- Classify any compatibility or legacy branches as active, dead, or stale; remove/fix stale branches where in scope.
- Run the selected focused runtime and Cortex tests after changes.
