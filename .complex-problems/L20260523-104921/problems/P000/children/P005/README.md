# Update residue guards, tests, and ledger evidence

## Problem

After code deletion, tests and guard scripts must stop encoding SQLite compatibility as a desirable server property. The work also needs durable evidence so future cleanup does not regress.

## Success Criteria

- Tests/guard scripts assert Postgres-only server persistence where relevant.
- A residue inventory categorizes remaining SQLite references into current allowed, historical archive, or follow-up-required.
- The ledger records evidence from diffs, scans, and test runs.
- Touched submodules and root pointers are committed and pushed without reverting unrelated worktree changes.
