# Child Problem: Cortex test fixtures

## Problem

Cortex tests still include direct-tool vocabulary in payload, wake child, and tool-schema tests. After policy/API cleanup, these tests need to reflect endpoint and migration naming.

## Success Criteria

- Payload tests use endpoint naming and shell/API vocabulary.
- Wake counter tests use `reply_action` rather than `im_reply`.
- Tool schema limit tests still guard removed direct tools without presenting them as active paths.
- Focused Cortex tests pass.
