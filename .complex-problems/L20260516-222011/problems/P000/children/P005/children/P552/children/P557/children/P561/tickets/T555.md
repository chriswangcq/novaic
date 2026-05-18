# Map Artifact And Display Blob Usage

## Problem Definition

P561 must separate intended blob usage for artifacts/display/payload storage from inappropriate blob usage as a real-time RO/RW filesystem authority.

## Proposed Solution

Scan blob references across Cortex, runtime, sandbox/logicalfs, blob service, and docs. Read high-signal files for display/artifact/tool-output contracts. Produce a usage map and flag suspicious live-file semantics for P553.

## Acceptance Criteria

- Blob reference scan artifacts exist.
- Intended artifact/display/payload usage is listed with file references.
- Any blob usage that appears to proxy live RO/RW workspace state is flagged.
- Result avoids removing or changing code.

## Verification Plan

Use `rg` scans for `blob://`, `runtime-artifact`, `cortex-payload`, `display`, `artifact`, `tool-output`, `/ro`, `/rw`, and object-store paths. Read high-signal files only.

## Risks

- Docs may mention desired architecture rather than current code.
- Some object-store adapters are intended but dangerous if called from the wrong layer.

## Assumptions

- P553 will decide cleanup/remediation for suspicious hits.
