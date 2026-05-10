# Phase 3.6.1: Mark legacy context/step/lifecycle file writes as projections

## Problem

Legacy filesystem writes are still named as generic source writes (`append_context`, `write_step`, `complete_child_scope`), which makes it too easy to mistake them for authoritative state after event cutover.

## Success Criteria

- Active event-wired endpoints call projection-named methods or comments that make legacy writes explicitly non-authoritative.
- Context, step, and skill lifecycle projection writes are distinguishable from event append writes.
- Existing transitional readers/tests continue to pass.
- Static scan can classify remaining write sites by name.
