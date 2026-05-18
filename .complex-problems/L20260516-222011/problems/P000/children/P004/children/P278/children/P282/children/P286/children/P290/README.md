# Problem: Session table active usage classification

## Problem

For every session-related table found in DDL, scan active code references and classify the table's role in runtime behavior.

## Success Criteria

- List active read/write references per table with file references.
- Classify each table as authority, event log, durable outbox, projection/cache, or legacy residue.
- Identify any table name referenced in code but absent from DDL.
