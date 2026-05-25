# Commit and push release source

## Problem

The Entangled fix and active ledger changes must be committed in the correct repositories and pushed so Release Controller can build from immutable source.

## Success Criteria

- Entangled submodule has a focused commit with the SQL fix and tests.
- Parent repo has a commit updating the Entangled pointer and ledger.
- Both commits are pushed to their remotes.
- Local git status after commit/push contains no unintentional source edits.
