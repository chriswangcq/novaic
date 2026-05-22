# Queue Postgres Target Confirmation Ticket

## Problem Definition

P110 must determine whether the current runner has a safe non-production Queue Postgres DSN or DSN file for downstream Queue Service API smokes. Without this target, service startup and API smokes must not proceed.

## Proposed Solution

1. Inspect only presence/status of relevant environment variables:
   - `NOVAIC_QUEUE_DB_BACKEND`
   - `NOVAIC_QUEUE_POSTGRES_DSN_FILE`
   - `NOVAIC_QUEUE_POSTGRES_DSN`
2. Prefer DSN file usage and avoid printing raw DSN values.
3. If a DSN file is present, confirm the file exists and record only redacted public identity.
4. If a target is available, verify it is non-production before any write.
5. If no safe target is available, record an explicit blocker with exact prerequisite variables.

## Acceptance Criteria

- A confirmed non-production target is recorded, or an exact missing-target blocker is recorded.
- No production target is used.
- No secret DSN value is printed into artifacts.
- Downstream P111/P112/P113 know whether they may proceed or must wait for credentials.

## Verification Plan

- Use set/unset env checks for direct DSN variables.
- Use path existence checks for DSN files without dumping contents.
- Record Docker availability only as supporting context.
- Stop before service startup if target identity is missing or ambiguous.

## Risks

- Direct DSN environment variables can leak through logs if handled carelessly.
- A DSN file path alone does not prove non-production; target identity still requires confirmation.

## Assumptions

- The current local shell is the smoke runner context unless the user provides an alternate machine/session context.
- `NOVAIC_QUEUE_POSTGRES_DSN_FILE` is the preferred credential input.
