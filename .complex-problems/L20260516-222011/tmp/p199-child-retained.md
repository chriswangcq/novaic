# Audit retained production projection compatibility branches

## Problem

Not every old-looking projection branch is stale. Nested result unwrapping, generic dict fallback, and historical step parsing may still defend persisted data. Audit retained production branches and either justify or remove them with evidence.

## Success Criteria

- Each retained compatibility/defensive branch has a concrete reason tied to current or persisted data contracts.
- Any branch found stale is removed in the child work, not merely documented.
- Tests cover the retained behavior or confirm the stale branch is gone.
