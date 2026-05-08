# Handler Registry Metadata And Boundary Guard

## Problem

Task handlers are Python functions registered by topic, but the registry does not expose enough declarative metadata to separate real business computation from lifecycle/runtime ownership.

## Success Criteria

- Handler registration exposes metadata such as topic, pool, module, and handler name.
- Tests prove handler modules do not import worker lifecycle, queue DB, or concrete process/runtime ownership.
- Existing handler lookup behavior remains compatible.
- Any misleading hidden lifecycle wiring in handler modules is removed or guarded.

