# Phase 5: Legacy cleanup, reset behavior, and full verification

## Problem

Remove misleading legacy DFS-source residue, implement old-data reset/no-compat behavior, and run comprehensive checks. The codebase should leave one clear current path for Cortex context source semantics.

## Success Criteria

- Legacy source-of-truth paths and stale docs/comments are deleted or rewritten as projection/debug only.
- Old data reset behavior is explicit and tested.
- Full relevant test suites pass.
- Diff review confirms no permanent double-write/double-read ambiguity.
- Residual risks are documented and non-blocking.
