# PR-181A — SubAgent spawn uses Environment as the single IM writer

Status: `[closed]`

## Finding

`spawn_subagent` manually appends a `messages` row, then calls `EnvironmentRepository.create_im_message(..., publish_chat_projection=False)` with the same id. That keeps two write branches in one mutation.

## Scope

- Keep Business as owner of SubAgent creation.
- Make `EnvironmentRepository.create_im_message` write the Environment event, IM row, notification, and chat projection.
- Remove direct `store.append("messages", ...)` from `spawn_subagent`.
- Keep the returned `message_id` as the Environment message id.

## Tests

- Business spawn unit test proves one Environment call creates the projection.
- Static guard: `spawn_subagent` must not directly append `messages`.
- Full Business tests.

## Deployment / Git

- Deploy Business.
- Commit/push `novaic-business` and root docs/pointer.

## Closure

- `spawn_subagent` no longer calls `store.append("messages", ...)`.
- `EnvironmentRepository.create_im_message` now writes the Environment event, IM row, notification, and chat projection for the spawn initial task.
- Returned `message_id` is the Environment message id.
- Tests: focused spawn/repository tests → `23 passed`; full Business suite → `150 passed`.
- Deployment: `./deploy business`; production Business health returned healthy.
