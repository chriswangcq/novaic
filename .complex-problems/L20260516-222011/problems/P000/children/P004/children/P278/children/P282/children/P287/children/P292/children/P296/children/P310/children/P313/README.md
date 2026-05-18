# Attach outbox worker-only verification

## Problem

Verify attach delivery is worker/drain-owned and no repository eager publish residue remains.

## Success Criteria

- Source guard rejects repository eager publish.
- Focused attach/session outbox tests pass.
- No unrelated files modified.
