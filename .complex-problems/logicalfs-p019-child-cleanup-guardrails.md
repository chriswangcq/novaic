# Delete Old Authority Paths And Strengthen Guardrails

## Problem

After cutover, old authority code, compatibility constructors, stale docs, or broad allowlists can keep the system ambiguous and make future agents accidentally revive dead paths. This belongs under T019 because the user explicitly wants no half-migration and no legacy branch kept for compatibility.

## Success Criteria

- Old Cortex-owned live file authority code is physically deleted or moved to clearly test-only support with no production imports.
- Guardrail tests fail direct live Workspace usage of `CortexStore`, `BlobCortexStore`, `/v1/objects`, or old backing sandbox paths outside approved LogicalFS internals.
- Docs describe the final module relationship: Cortex semantic layer, LogicalFS realtime `RO` / `RW`, sandboxd process execution, Blob cheap bytes.
- Stale wording that implies Blob/Cortex owns live workspace files is removed.
- Canonical backend tests and targeted residue scans pass.
