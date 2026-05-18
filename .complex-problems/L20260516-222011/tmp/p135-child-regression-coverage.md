# Runtime prepare-context regression coverage audit

## Problem

Even if the handler chain is currently correct, it needs tests that would fail if stale local continuity or `context.read` projections re-enter the final LLM context path.

## Success Criteria

- Existing runtime tests for prepare-context, context ordering, context read-by-id, no-wake replay, and no historical tool-image injection are mapped.
- The selected test set is run after the source mapping children finish.
- Missing guard coverage is added if the source map reveals an unguarded regression path.
- The final coverage result explicitly states which stale-context regression modes are and are not covered.
