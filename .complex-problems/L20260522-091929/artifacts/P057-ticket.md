# Prepare Safe Entangled Postgres REST Staging Target

## Problem Definition

REST smokes need a concrete Postgres target that is safe to mutate and not production traffic-facing. Prepare or select a staging database, import fixture or migrated data, and write a redacted setup report with counts and semantic checks.

## Proposed Solution

1. Prefer a dedicated staging database such as `novaic_entangled_rest_staging` on the existing API Postgres service, with a dedicated user/DSN secret.
2. If remote staging cannot be safely created in this pass, use a clearly labeled fixture-backed target and record the blocker for remote setup.
3. Use the migration command/module to prepare schema, clean the staging target, copy data, reset identities, and produce a redacted report.
4. Validate counts, sync versions, transition count/max ID, `entangled_rowid`, and sequence evidence from the report.
5. Store only redacted target labels and report summaries in the ledger; never record DSN/password/token values.

## Acceptance Criteria

- A safe REST staging target is selected or created without touching production traffic.
- DSN/secret handling is documented by path/label only, with values redacted.
- Migration/import runs against the selected target or a documented fixture target.
- Setup report records migrated tables/counts, semantic checks, prepared/cleaned tables, and sequence resets.
- Report contains no DSNs, passwords, tokens, cookies, or env-file contents.
- Any blocker is recorded as a specific result suitable for follow-up.

## Verification Plan

Run target setup/import, inspect the redacted report, verify no raw secret strings are present, and record exact non-secret evidence. If remote commands are used, verify the target database name/label before any destructive action.

## Risks

- Accidentally targeting production `novaic_entangled` would be destructive; require a staging database name/label and confirmation.
- Remote DSN files can leak through shell history/output; avoid printing them.
- Fixture-backed fallback does not prove real Postgres permissions or type behavior.

## Assumptions

- The existing `novaic-postgres` service is the likely place for a staging target, but production cutover is not part of this ticket.
