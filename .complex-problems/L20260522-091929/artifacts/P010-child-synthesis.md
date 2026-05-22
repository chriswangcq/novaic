# Synthesize Gateway Cortex SQLite Dispositions and Classification Note

## Problem

After Gateway and Cortex are classified separately, their dispositions must be synthesized into one durable boundary artifact and reflected in the central SQLite classification note if the live classification changes.

This belongs under P010 because the parent problem requires backup expectations, eventual Postgres boundaries, and central note maintenance.

## Success Criteria

- A durable combined artifact summarizes Gateway and Cortex dispositions, backup expectations, and Postgres boundaries.
- The central SQLite classification note is updated if Gateway or Cortex disposition changed, or the result explicitly states no update was needed.
- The update, if made, is small, timestamped, and documentation-only.
- No Gateway or Cortex production cutover is attempted.

