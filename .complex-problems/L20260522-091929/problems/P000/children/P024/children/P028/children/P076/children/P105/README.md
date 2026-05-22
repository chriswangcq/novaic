# Prepare Queue Postgres Staging Target

## Problem

P076 needs a non-production Postgres target before any Queue Service smoke can run. The database must be clearly separate from production, initialized with current Queue schema, and optionally seeded or checked with the migration tooling without exposing secrets.

## Success Criteria

- A non-production Queue Postgres DSN or DSN file is identified and redacted in artifacts.
- The target is confirmed non-production and safe to write.
- Current Queue Postgres schema is initialized or verified.
- Initial table counts and config schema version are recorded.
- If migration fixture data is used, the migration report is generated and redacted.
- Missing credentials or environment access are recorded as an explicit blocker with exact next commands.
