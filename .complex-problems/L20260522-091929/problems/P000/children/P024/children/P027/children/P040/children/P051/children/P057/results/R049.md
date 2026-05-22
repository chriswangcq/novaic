# Entangled REST Staging Target Setup Result

## Summary

`T053` prepared a safe Postgres REST staging target on the API machine. A dedicated database/role/DSN secret was created for `novaic_entangled_rest_staging`, fixture REST-smoke data was imported through the `novaic-postgres` container, and a redacted setup report was written. Production `novaic_entangled` traffic/data was not touched.

## Done

- Confirmed `novaic-postgres` container is healthy on `api.gradievo.com`.
- Created or updated dedicated database/role `novaic_entangled_rest_staging`.
- Created root-owned `0600` staging password and DSN secret files under `/opt/novaic/postgres/secrets/`.
- Imported fixture tables/data for:
  - `entangled_sync_versions`
  - `rest_smoke_events`
  - `subagent_state_transitions`
- Reset identity expectations above migrated fixture maxima.
- Wrote redacted setup report `.complex-problems/L20260522-091929/artifacts/entangled-rest-staging-target-setup-report.json`.

## Verification

- Remote setup query returned non-secret JSON with:
  - `entangled_sync_versions`: 1 row.
  - `rest_smoke_events`: 1 row.
  - `subagent_state_transitions`: 1 row.
  - transition max ID: 1.
  - `rowid_check`: true.
  - sequence restart expectations at 2.
- Secret files were reported as `600 root:root`.
- No DSN/password/token values were printed or stored in the report.

## Known Gaps

- The staging target currently contains REST-smoke fixture data, not a full production SQLite import.
- Runtime startup and REST endpoint smokes remain assigned to later `P051` children.

## Artifacts

- `.complex-problems/L20260522-091929/artifacts/entangled-rest-staging-target-setup-report.json`
