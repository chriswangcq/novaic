# P045 Check

## Judgment

Success.

## Evidence Reviewed

- Result `R031`.
- Focused test run.
- Focused grep over `activity_projection.py`.

## Stress Check

The production backend projection file no longer contains raw old direct-tool tokens. Legacy archived labels are centralized behind `LEGACY_ARCHIVED_TOOL_LABELS`, and current shell `desc` handling remains the first path.

## Residual Risk

Frontend legacy detection remains in `P046`.
