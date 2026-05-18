# Cortex generation and active-state compatibility guard

## Problem

Final Cortex verification needs a focused guard for old active-state lookup and missing/stale generation compatibility paths. These paths are dangerous because they can resurrect old session/scope authority semantics.

## Success Criteria

- Save source guard scans for generation, active lookup, stack/scope compatibility, and legacy state words, excluding `.complex-problems`.
- Classify every remaining hit as current explicit contract, test fixture, docs/comment, or unresolved risk.
- Confirm no live Cortex path accepts missing/stale generation where generation is required.
- Confirm no live Cortex path revives old active-state lookup as authoritative state.
