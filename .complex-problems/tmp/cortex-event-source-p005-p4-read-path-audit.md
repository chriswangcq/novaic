# Audit DFS read fallback removal

## Problem

After prepare/status cutover, remaining DFS `ContextEngine` usage must be statically audited so it cannot silently remain the API read source.

## Success Criteria

- Static scan classifies all remaining `ContextEngine` imports/usages.
- API prepare/status paths have no DFS fallback.
- Legacy DFS tests are classified as projection/debug legacy tests or moved out of active API source semantics.
- Full Cortex suite passes.
