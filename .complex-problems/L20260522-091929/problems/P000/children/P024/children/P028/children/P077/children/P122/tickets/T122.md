# Inventory Production Queue Runtime And Cutover Preconditions

## Problem Definition

Production cutover needs a reliable inventory of Queue Service, workers, outbox workers, scheduler/health processes, runtime configuration, active SQLite holders, production Postgres target identity, and rollback plan before any freeze, backup, migration, or restart can safely happen.

## Proposed Solution

Run read-only inspections on the api host and local repo: process lists, Docker/container status, Queue Service health where available, filesystem metadata for the active SQLite queue file, `lsof` holder checks, sanitized runtime environment/config discovery, and production Postgres target confirmation without printing credentials. Save a redacted preflight report and make a go/no-go recommendation for the next freeze/backup child.

## Acceptance Criteria

- All visible Queue Service/worker/outbox/scheduler processes are listed with commands and PIDs.
- Active `/opt/novaic/data/queue.db` metadata and holders are recorded without modifying the file.
- Runtime configuration sources are summarized with secrets and credential-file paths redacted.
- Production Postgres target identity is confirmed or a blocker is recorded.
- Rollback plan and go/no-go preflight decision are documented.

## Verification Plan

Cross-check `ps`, `docker ps`, `lsof`, runtime directories, service health endpoints, and sanitized config/environment output. Run a sensitive-pattern scan on the generated report before recording success.

## Risks

- Runtime credentials may be stored in files; commands must avoid printing file contents.
- Multiple services may use the same data directory; process filtering must be broad enough to avoid missing writers.
- If production Postgres target cannot be confirmed, the correct outcome is a blocker/no-go report, not proceeding.

## Assumptions

- The api host is the production runtime host for this Queue cutover inventory.
- This ticket is read-only and does not stop services, write to Queue data, or migrate state.
