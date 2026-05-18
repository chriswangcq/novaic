# Scan old session wrappers and compatibility branches

## Problem

Find old repository wrappers, direct publish helpers, compatibility branches, and mutation shortcuts around session dispatch/finalize/outbox that may survive outside the new FSM/outbox ownership boundary.

## Success Criteria

- Search patterns include old wrapper/helper names, legacy active-session concepts, generation compatibility, and attach/wake publish surfaces.
- Matches are classified as production active path, test guard, documentation, or no-match.
- Risky/removable production residue becomes a cleanup follow-up.
