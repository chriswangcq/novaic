# Attach stale and missing generation regression coverage audit

## Problem

Review end-to-end and guard tests for stale/missing attach generation. Ensure repository, outbox, and runtime tests together prove stale attach cannot mutate a newer active wake.

## Success Criteria

- List existing stale/missing attach generation tests and their covered boundary.
- Identify any missing boundary coverage between repository, outbox, and runtime.
- Add or request follow-up for a regression test if stale scope/generation can still slip through.
- Run focused attach-generation tests and report exact results.
