# Cross-repo stale compatibility residue guard

## Problem

After runtime and Cortex targeted tests pass, cross-repo source guards must classify remaining stale compatibility residue: implicit generation defaults, current-active fallback behavior, direct active pointer mutation, and deprecated finalize/session-ended branches.

## Success Criteria

- Run cross-repo `rg` guards for finalize/session-ended generation defaults, `int(...)` coercion, active-session mutation helpers, legacy compatibility names, and remaining-stack/archive synthesis.
- Classify every guard hit as safe test coverage, safe adapter signature, fixed live residue, or follow-up problem.
- No live path remains that silently defaults generation or clears/restarts/archives a newer active session from stale input.
- The result contains a concise guard matrix with file evidence.
