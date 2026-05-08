# Targeted regression tests

## Problem

Add and run targeted tests proving the code repair guards the production regression: dispatch uses configured timeout, and saga claim/FSM ledger writes tolerate normal SQLite contention rather than surfacing a 500/database locked failure.

## Success Criteria

- Tests exist in the appropriate repo(s).
- Targeted tests pass locally.
- Any failing unrelated test is documented rather than hidden.
