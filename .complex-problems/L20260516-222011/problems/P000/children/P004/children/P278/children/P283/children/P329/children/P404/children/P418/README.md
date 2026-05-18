# Cortex archive and diagnostic residue cleanup

## Problem

Cortex archive, summary, diagnostic, and projection paths may contain generation/active-state residue that is safe as audit metadata but dangerous if used as live authority.

## Success Criteria

- Inspect archive, summary, diagnostic, and projection hits from the Cortex inventory.
- Remove any live compatibility fallback that reintroduces active-state authority.
- Explicitly classify safe diagnostic/projection/counter fields.
- Add or update tests if archive/diagnostic behavior changes.
- Confirm historical docs or archived summaries are not mistaken for live runtime code.
