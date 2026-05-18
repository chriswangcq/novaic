# Prove stale production projection helper has no live callers

## Problem

Before deleting stale production projection code, verify in-repo callers, exports, tests, and package entry points for `resolve_for_llm` and any helper-only imports. The deletion must be based on current code evidence rather than memory from the inventory.

## Success Criteria

- `resolve_for_llm` caller/export inventory is recorded with exact file references.
- Any remaining external-facing export risk is identified.
- The result clearly states whether deletion can proceed and what must be removed with it.
