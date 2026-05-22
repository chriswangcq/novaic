# Inventory Production Queue Runtime And Cutover Preconditions

## Problem

Before touching production Queue data, all processes, configs, and credential inputs that can read or write `/opt/novaic/data/queue.db` must be identified. The production Postgres target and rollback plan must be confirmed without exposing credentials.

## Success Criteria

- Production Queue Service, workers, outbox workers, schedulers, and other possible queue writers are listed with process IDs, commands, and owners.
- Current Queue runtime configuration is captured with credential values and credential-file paths redacted.
- Production Postgres target identity is confirmed as intended and non-staging.
- Rollback plan is documented, including SQLite restore/config revert steps and conditions.
- A go/no-go preflight decision is recorded before freeze or backup.
