# Cut Over LLM Factory Docker Runtime to Postgres

## Problem Definition

LLM Factory now has Postgres backend support and its SQLite data has been copied into `novaic_llm_factory`, but the live `novaic-llm-factory` Docker container still runs against `/data/llm_factory.db`. The runtime must be cut over to Postgres, and the old SQLite file must be clearly retained as rollback rather than current state.

## Proposed Solution

Deploy the Postgres-capable LLM Factory source/config to the `api` host, rebuild or update the Docker image, rerun the SQLite-to-Postgres migration immediately before restart, store the Postgres DSN in a root-readable file, update the Docker config to use `backend=postgres` and the DSN file, restart the `novaic-llm-factory` container, and verify health plus row counts. After successful cutover, keep the old SQLite file in place or archive it with a clear rollback/non-current label and update the production SQLite classification note.

## Acceptance Criteria

- The Docker image/container uses the Postgres-capable LLM Factory code.
- Runtime config uses Postgres via a root-readable DSN file or equivalent secret handling.
- Migration is rerun immediately before restart so Postgres includes the latest SQLite rows at cutover time.
- `novaic-llm-factory` restarts healthy and `/health` returns ok.
- The running container no longer holds `/opt/novaic/llm-factory/data/llm_factory.db` open.
- Postgres row counts remain valid after cutover.
- The old SQLite DB is retained as rollback with an explicit non-current label.
- Rollback instructions are recorded.

## Verification Plan

Inspect current compose/build layout, sync only required source/config files, rebuild the image, rerun migration, restart the container, check Docker health and `/health`, inspect container config/logs, verify no `lsof` holder on the SQLite DB, verify Postgres counts, and update `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`.

## Risks

- A bad image/config can interrupt LLM routing until rollback.
- DSN handling can leak credentials if written into world-readable config or command output.
- Rows written to SQLite between migration and restart must be minimized by rerunning migration directly before restart.

## Assumptions

- A short LLM Factory restart is acceptable with immediate rollback available.
- The current `/opt/novaic/llm-factory/data/llm_factory.db` remains the rollback source.
