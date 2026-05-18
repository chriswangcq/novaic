# Finalize ownership final verification

## Problem

After producer audit and strictness changes, P489 needs a skeptical final check that finalize ownership is explicit and no fallback stack synthesis remains. This belongs under P489 because tests can pass while old helper names or implicit fallback branches survive.

## Success Criteria

- Final `rg` guard proves no successful finalize path fabricates `remaining_stack`.
- Focused finalize/session legacy tests pass together.
- Any retained compatibility-looking hit is classified with file references.
