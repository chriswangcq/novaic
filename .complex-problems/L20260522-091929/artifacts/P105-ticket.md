# Prepare Queue Postgres Staging Target

## Problem Definition

P076 cannot run service/API or worker smokes until a safe non-production Queue Postgres database is identified, initialized, and recorded. P105 should either prepare that target or clearly record the missing credential/environment blocker with exact next commands.

## Proposed Solution

1. Discover available non-production Queue Postgres connection inputs:
   - environment variables;
   - DSN files;
   - deployment/start scripts;
   - local staging config.
2. Verify the target is not production:
   - inspect hostname/database name where safe;
   - require explicit staging/test naming or user-provided confirmation artifact.
3. Initialize or verify current Queue Postgres schema using the existing schema initializer.
4. Record initial table counts/config schema version with a redacted report.
5. If no safe staging DSN exists in the workspace, record a blocker artifact with exact command/environment variables needed for the next run.

## Acceptance Criteria

- Either a staging target is prepared and counted, or a precise blocker is recorded.
- No production Queue data is written.
- DSNs/secrets are redacted in artifacts.
- The next P076 child has enough information to start Queue Service smokes or knows the exact missing prerequisite.

## Verification Plan

- Inspect local environment/config for staging DSN inputs.
- If DSN exists, run schema/count preflight with the migration/report helpers.
- If DSN is absent, create a redacted blocker report and do not attempt service smokes.

## Risks

- Accidentally touching production is unacceptable; abort if target identity is ambiguous.

## Assumptions

- The current local workspace may not have staging credentials; recording that blocker is a valid P105 outcome.
