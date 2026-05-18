# Finalize restart atomicity design

## Problem

Design the smallest transaction-boundary change that removes the finalize-with-pending no_active race while preserving durable restart outbox, generation, and pending projection semantics.

## Success Criteria

- Define exactly where restart scope, generation, plan, transition, and projection should be created.
- Preserve explicit dependencies and no direct publish path.
- Identify tests/source guards needed for verification.
