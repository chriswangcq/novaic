# Business dispatch adapter residue scan

## Problem

Business dispatch/subscriber code may still carry fallback compatibility or migration-era paths around IM aggregation, dispatch, ownership, or queue handoff.

## Success Criteria

- Focused scans cover `novaic-business` active code for legacy, fallback, compat, migration, TODO/FIXME, and old direct tool or dispatch wording.
- Hits are classified by active path status and risk.
- Safe tiny cleanup is applied directly if found.
- Focused business tests pass for touched files.
