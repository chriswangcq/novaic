# PR-187B — Archive Stale Ticket Checklist Residue

Status: `[closed]` — 2026-05-03

## Goal

Remove misleading unchecked checklist residue from already closed historical tickets.

## Current-State Analysis

PR-90 and PR-91 were marked deployed, but each still contained conditional unchecked checklist items. They read like active work even though the product architecture had moved on:

- PR-90 optional lifecycle events are no longer planned as execution-log expansion; user-facing activity is now projected from Cortex/Activity Timeline.
- PR-91 optional schema invariant has an active docs/cache guardrail and no separate generated schema invariant location.

## Implementation

- [x] Mark PR-90 optional lifecycle event expansion as explicitly not added.
- [x] Mark PR-90 conditional lifecycle-event tests as not applicable because no such event kinds were added.
- [x] Mark PR-91 optional schema invariant as covered by `scripts/ci/lint_entangled_cache_docs.sh`.
- [x] Leave historical evidence intact while removing the appearance of active unfinished work.

## Validation

```bash
rg -n "\[ \]" docs/roadmap/tickets/PR-90-execution-log-status-and-lifecycle-events.md docs/roadmap/tickets/PR-91-entangled-client-cache-docs-and-guardrails.md
```

Result: no unchecked checklist items remain in PR-90 or PR-91.
