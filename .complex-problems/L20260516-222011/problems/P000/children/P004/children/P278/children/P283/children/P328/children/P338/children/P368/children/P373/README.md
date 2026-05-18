# Cortex Archive Diagnostics Persistence

## Problem

Cortex archive/context-event records should persist the explicit finalize diagnostics supplied by the runtime boundary, not generic archive reasons or remaining-stack data inferred from current active-stack projection.

## Success Criteria

- Cortex archive code writes explicit `finalize_reason`, `session_generation`, and remaining-stack diagnostics into the appropriate archive/context-event metadata.
- Archive logic does not synthesize finalize generation from active lookup for the finalize diagnostics path.
- Missing or invalid explicit generation cannot produce a finalize-diagnostics archive event.
- Focused Cortex tests prove valid archive metadata and invalid generation rejection.

## Why Under P368

This child owns Cortex persistence semantics after the request reaches Cortex. It is separate from task handler/bridge propagation.
