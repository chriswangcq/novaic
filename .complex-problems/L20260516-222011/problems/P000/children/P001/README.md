# Repo topology and residue inventory

## Problem

Audit the multi-repo workspace topology, branch/submodule status, dirty state, stale generated files, and obvious code-residue hotspots before touching implementation. This establishes the map and prevents unrelated or accidental edits.

## Success Criteria

- Current branch, submodule pointers, dirty state, and repo layout are recorded.
- Obvious residue patterns are searched with concrete commands.
- Any immediate low-risk cleanup opportunities are identified for child or follow-up work.
- No implementation edits are made without evidence and a narrower ticket.
