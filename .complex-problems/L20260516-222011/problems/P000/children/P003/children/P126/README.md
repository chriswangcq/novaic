# Context assembly source map and event boundary

## Problem

The Cortex context assembly path spans event store, workspace projections, step references, payload references, and active stack injection. Before changing behavior, the active path must be mapped with concrete file/function pointers so optimization work does not patch the wrong layer or leave an old branch active.

## Success Criteria

- The active context assembly/write/read path is mapped from incoming step/result writes to LLM context preparation.
- Each mapped file/function is classified as active, test-only, compatibility-only, or dead/stale.
- The role of context event stream, workspace projections, `step_ref`, `payload_ref`, and active skill stack injection is documented.
- Any discovered duplicate or stale assembly path is turned into a follow-up child problem or removed if obviously dead and safe.
- Focused tests or static checks cover any mapping assumption that affects runtime behavior.
