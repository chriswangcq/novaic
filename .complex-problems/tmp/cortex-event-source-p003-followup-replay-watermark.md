# Add projection replay watermark and sequence validation

## Problem

Phase 2's projector has basic replay semantics but does not fully satisfy the parent criterion that projection output is generation-checked and rebuildable from the event stream. It needs explicit stream/sequence validation and a snapshot watermark before Phase 2 can be considered complete.

## Success Criteria

- `ContextProjectionSnapshot` includes a deterministic stream watermark, at minimum stream id, root scope id, first seq, and applied seq.
- `project_context_events` rejects mixed stream ids.
- `project_context_events` rejects non-contiguous or out-of-order seq values.
- Empty event projection remains deterministic and documented.
- Tests cover valid watermark, mixed stream rejection, duplicate seq rejection, seq gap rejection, and out-of-order rejection.
- Focused ContextEvent tests pass.
