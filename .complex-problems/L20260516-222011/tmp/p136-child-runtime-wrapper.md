# Runtime tool result wrapper ref contract

## Problem

Runtime tool handlers wrap raw tool output before writing step results and exposing public context. This wrapper layer must clearly emit stable `step_ref`, correct `payload_ref`, durable payload metadata, public text, and artifact refs without leaking large payloads or conflating lookup identity with storage identity.

## Success Criteria

- Map runtime wrapper code that constructs tool result dictionaries, public content, durable payloads, artifacts, `step_ref`, and `payload_ref`.
- Document which fields are public context fields versus durable/raw payload fields.
- Add or tighten focused tests if wrapper behavior permits ref ambiguity or raw payload leakage.
- State whether this layer needs code changes or is already correct.

