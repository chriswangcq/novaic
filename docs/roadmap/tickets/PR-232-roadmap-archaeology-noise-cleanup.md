# PR-232 — Roadmap Archaeology Noise Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Documentation entropy cleanup |
| Created | 2026-05-05 |
| Scope | historical roadmap tickets/reviews and current roadmap indexes |
| Dependencies | PR-210, PR-225 |

## Goal

Keep historical tickets useful for archaeology while preventing raw grep or
newcomer review from mistaking old unchecked boxes for active backlog.

## Small Tickets

### PR-232A — Current Backlog Index Separation

- Objective: ensure active/current roadmap indexes point only to current tickets
  and current architecture docs.
- Scope: `docs/roadmap/tickets/README.md` and current roadmap docs.
- Expected result: archived historical content is not part of the active work
  queue.
- Verification: docs grep and archaeology lint.

### PR-232B — Historical Checklist Noise Fence

- Objective: reduce historical `[ ]` checklist noise from old tickets/reviews
  without deleting useful archaeology.
- Scope: historical ticket/review files that still look active.
- Expected result: raw grep has a clear archive marker path or no active-looking
  unchecked boxes in current docs.
- Verification: docs lint and targeted grep.

## Acceptance

- `scripts/ci/lint_current_docs_residue.sh` passes.
- `scripts/ci/lint_roadmap_ticket_archaeology.py` passes.
- A raw checklist grep clearly separates active work from archived historical
  records.

## Closure

Closed 2026-05-05. Current roadmap docs were updated to the chat-message /
Environment notification split, and the roadmap archaeology lint now also fences
retired message lifecycle wording.
