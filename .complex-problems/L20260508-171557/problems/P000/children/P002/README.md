# Plan-First Effect Runner Contract

## Problem

Action engines still call `execute_effect(...)` directly. Move effect execution ownership into a generic runner/substrate so engines compute explicit actions/plans and effect execution is centralized.

## Success Criteria

- `queue_service/worker/effects.py` exposes a reusable plan runner API.
- Task, saga, scheduler, and health engines no longer import or call `execute_effect(...)` directly.
- `_effect(...)` helper methods are removed from action engines.
- Tests prove action engines stay behind explicit effect adapters and direct effect execution is banned.
