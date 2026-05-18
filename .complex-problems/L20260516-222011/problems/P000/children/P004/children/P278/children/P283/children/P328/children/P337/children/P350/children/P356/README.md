# Finalize mutation guard aggregate verification

## Problem

After Cortex scope-end, subagent status, and wake-finalize payload propagation are handled, P350 needs an aggregate verification pass to prove there are no remaining stale finalize mutation holes in the inspected runtime paths.

This child belongs under P350 because each individual guard can pass while the composed finalize mutation path still has a residue or untested branch.

## Success Criteria

- Run focused tests covering Cortex scope-end, subagent status mutation, wake finalize payloads, and session finalize ownership.
- Run source/residue searches for unguarded finalize mutation payloads and missing generation compatibility fallbacks.
- Map every P350 success criterion to concrete evidence.
- Record any remaining gap as a follow-up rather than marking P350 solved.
