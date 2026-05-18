# Session hidden input remediation

## Problem

Remove or explicitly inject any risky production hidden inputs found by the inventory. Decision logic in session/worker paths must be reproducible from explicit constructor/config inputs instead of reading process state or mutable globals at decision time.

## Success Criteria

- Any risky direct environment/global read in a decision path is replaced by explicit configuration or a narrow adapter-boundary read.
- Unit tests or guards prove the fixed behavior is deterministic from explicit inputs.
- No broad compatibility fallback is introduced.
- If no risky hits exist, record a source-backed no-op result with evidence.
