# PR-181 — SubAgent spawn write normalization

Status: `[closed]`

## Goal

Normalize SubAgent spawn side effects so Environment IM/message/notification writes have one owner and one code path. Business may own the mutation, but it should avoid parallel manual writes that duplicate Environment repository behavior.

## Required Process

1. Analyze current `spawn_subagent` writes and downstream subscribers.
2. Create small implementation tickets from the findings.
3. Implement the single-writer path and delete old duplicate writes.
4. Confirm closure with tests, smoke, deploy, and git commit.

## Tests

- Business SubAgent spawn unit tests.
- Environment notification lifecycle tests.
- Runtime `subagent_spawn` tool smoke.
- Static scan for duplicate message write branches.

## Deployment / Git

- Deploy affected Business/Runtime services.
- Commit/push each independently mergeable change.

## Small Tickets

- PR-181A — SubAgent spawn uses Environment as the single IM writer.

## Closure

PR-181 found one duplicate write path in `spawn_subagent`: a direct `messages` append plus an Environment write. PR-181A removed the direct append, left Environment as the single writer for event/message/notification/projection, deployed Business, and verified tests/smoke.
