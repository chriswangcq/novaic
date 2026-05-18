# Compensation wake_finalize generation preservation

## Problem

Saga compensation-created `wake_finalize` contexts must preserve explicit positive session generation and wake scope identity when the failed saga/task had them. This belongs under P351 because compensation can otherwise bypass the normal wake-finalize identity contract.

## Success Criteria

- Implement preservation of `scope_id`, wake/root scope identity, subagent identity, and positive session generation in compensation-created `wake_finalize` contexts.
- Remove any compatibility fallback that silently defaults missing generation to `0` or omits generation.
- Add focused tests proving a failed saga with generation produces compensation finalize work with the same positive generation.
- Add focused tests proving missing or invalid generation does not create an ambiguous mutating finalize task.
