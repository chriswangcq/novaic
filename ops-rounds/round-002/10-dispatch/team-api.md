# Round 002 Dispatch - API Team

## Objective
Close Week 1 gaps and make gateway interface governance explicit and reproducible.

## Hard Tasks
1. Deliver gateway env var spec with required/default/optional fields.
2. Deliver API surface inventory with `stable/compat/deprecated` labels.
3. Add independent gateway startup smoke script and report.
4. Verify no source-level imports from workers/runtime/tools remain.

## Acceptance Criteria
- Env spec and API inventory files exist and are referenced in report.
- Startup smoke runs successfully in isolated mode.
- Import scan shows zero forbidden cross-repo source imports.

## Required Evidence
- docs paths for env spec and API inventory
- smoke test command and pass summary
- forbidden import scan output summary

## Status
- owner: API Team
- due: 2026-02-26
- status: DONE
