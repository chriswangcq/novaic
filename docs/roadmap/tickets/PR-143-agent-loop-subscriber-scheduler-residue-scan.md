# PR-143 — Agent Loop / Subscriber / Scheduler Residue Scan

| Field | Value |
| --- | --- |
| Status | `[scanned]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | business, runtime, scripts, docs |
| Depends on | PR-142 |

## Goal

Clarify the single active Agent loop path. Any subscriber, scheduler, health-worker, unread/read, or recovery path that looks like a competing message loop must be classified or removed.

## Scan Plan

1. [x] Identify the active message dispatch path from startup scripts and runtime switches.
2. [x] Search active code for subscriber and outbox consumers.
3. [x] Search recovery paths that can still create wakes.
4. [x] Search old unread/read based loop triggers.
5. [x] Decide whether subscriber code is active, parked, or delete candidate.

## Findings

- Current runtime switch says `subscriber_enabled=false`.
- `scripts/start.sh` starts scheduler unconditionally and only starts `main_subscriber.py` when `subscriber_enabled=true`.
- `novaic-business/main_business.py` logs subscriber-disabled state and does not drain outbox directly.
- `novaic-agent-runtime/task_queue/workers/scheduler_worker.py` is the active scheduled-wake scan path.
- Subscriber path still physically exists and looks complete:
  - `novaic-business/main_subscriber.py`
  - `novaic-business/business/subscribers/dispatch_subscriber.py`
  - `scripts/deploy-business.sh` still documents/enables subscriber canary behavior.
  - `docs/runbooks/subscriber-canary.md` still treats subscriber as an operational path.
- Health/recovery code can still redispatch recovered work. That appears to be a safety net, not the primary loop, but the wording can still confuse ownership.
- Read/unread based chat-loop control is not the current primary mechanism; current UI read receipts are product status, not Agent loop ownership.

## Follow-up Decision

The subscriber path is the biggest active ambiguity. Either delete it as a retired competing loop, or explicitly mark it as parked/future and remove canary/deploy instructions. Given the maintenance policy, prefer a cleanup ticket to remove it unless a current owner re-justifies it.

## Unit / Guardrail Tests

- [ ] Cleanup follow-up should add a path ownership test proving only the intended dispatcher is active.

## Smoke / Deploy

- [x] No deploy for scan-only changes.
- [ ] Cleanup follow-up must smoke send-message -> reply lifecycle.

## Git / Merge

- [ ] Commit ticket updates.
- [ ] Push parent docs update.
