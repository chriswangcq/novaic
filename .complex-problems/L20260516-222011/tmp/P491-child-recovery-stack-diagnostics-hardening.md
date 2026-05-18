# Recovery stack diagnostics hardening

## Problem

Suspected-dead and recovery archive paths should preserve explicit stack diagnostics or mark them unknown explicitly. They must not silently lose `remaining_stack` and then fabricate an empty stack in a way that hides wake corruption.

## Success Criteria

- Suspected-dead payloads preserve recovery stack diagnostics when available.
- Recovery archive effect construction no longer silently turns missing diagnostics into a known empty stack.
- Any unavoidable unknown-stack case is explicit in payload/result semantics.
- Focused tests cover both preserved stack diagnostics and unknown-stack behavior.

