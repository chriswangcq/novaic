# Define Entangled Postgres Implementation and Cutover Requirements

## Problem

After inventory and semantic mapping, Entangled still needs a concrete implementation and cutover requirements plan: target database, schema/adapter phases, migration tooling, validation matrix, WebSocket/client smoke tests, rollback boundaries, and residue cleanup rules. This plan must avoid production cutover during P009.

This belongs under P009 because it turns Entangled's migration risks into actionable requirements for later implementation tickets without changing production yet.

## Success Criteria

- A phased implementation plan exists for Postgres config, adapter boundary, schema generation, store SQL conversion, migration tooling, tests, and deployment.
- The plan targets the existing `novaic_entangled` Postgres database and states whether any local SQLite unit-test fake remains acceptable.
- Pre-cutover and post-cutover checks are specified for table row counts, schema/index parity, sync-version equality/monotonicity, sample JSON decode, transition history, and health/readiness.
- WebSocket/client smoke tests are specified for schema push, representative list/form/stream full sync, create/update/delete delta, and reconnect behavior.
- Rollback boundaries are documented for before PG writes, after PG writes with no client-visible deltas, and after client-visible deltas.
- Old SQLite cleanup criteria are defined for the stabilization window.
- No production Entangled cutover is attempted by this child problem.
