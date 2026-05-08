# Worker Assembly Spec Substrate

## Problem

`worker_assemblies.py` still contains per-worker hand-written lifecycle assembly. Build a component-level assembly spec/interpreter so worker construction is data/spec driven where practical, and displaced manual wiring is deleted or guarded.

## Success Criteria

- A reusable worker assembly spec substrate exists under `task_queue/workers`.
- Existing workers are migrated to the spec interpreter without changing runtime modes.
- `worker_assemblies.py` shrinks to declarations and generic interpretation rather than duplicated lifecycle construction.
- Tests prove registry still wires all worker modes and old direct lifecycle construction cannot creep back.
