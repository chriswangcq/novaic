# Audit and projection generation classification

## Problem

`session_audit.py`, `queue_audit.py`, and related projection helpers still contain raw generation defaults. They are likely read-only diagnostics/projections, but must be explicitly classified or patched.

## Success Criteria

- Audit/projection generation hits are enumerated with file evidence.
- Hits are either patched to explicit validators or classified safe as diagnostic/projection formatting.
- Any changed audit/projection tests pass.
