# Runtime queue fallback compatibility residue scan

## Problem

Runtime and queue handling code may still contain stale fallback/compatibility branches around session dispatch, tool output projection, shell/display handling, or old queue paths.

## Success Criteria

- Focused scans cover `novaic-agent-runtime` active code for fallback, compat, legacy, migration, TODO/FIXME, pass, skip, and old direct-tool wording.
- Hits are classified as active risk, intentional guard, benign adapter, or stale residue.
- Safe tiny cleanup is applied directly if discovered.
- Touched runtime areas receive focused tests or explicit no-code-change verification.
