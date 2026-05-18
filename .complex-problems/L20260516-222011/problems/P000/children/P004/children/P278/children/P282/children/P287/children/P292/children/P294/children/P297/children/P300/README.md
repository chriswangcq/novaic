# Problem: Dispatch start-wake helper verification

## Problem

Verify the refactor with focused tests and source guards so duplicate start-wake construction does not silently return.

## Success Criteria

- Run focused dispatch/outbox/input tests.
- Add or update a source guard if needed.
- Verify source scan shows one shared helper-owned start-wake construction path.
