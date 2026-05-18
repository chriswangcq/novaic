# App Backend Startup Graph Audit Check

## Summary

Success. The audit result satisfies P804 because it maps the startup scripts, service config copies, port naming, and backend binary expectations without editing source files. The remaining issues are remediation work for P805, not blockers for the audit itself.

## Evidence

- R785 lists all relevant start scripts: source/dev plus resource and generated packaged copies.
- R785 lists both service config copies.
- R785 maps app config ports and source/dev script ports, including the `19996` Cortex/vmcontrol naming conflict.
- R785 compares resource and generated backend binary sets and identifies the `novaic-blob-service` versus `novaic-storage-a` mismatch.
- R785 states the ticket was audit-only with no code files edited.

## Criteria Map

- Current start-backends scripts and generated packaged variants are listed: satisfied by the scripts list in R785.
- Current service ports and vmcontrol/Cortex naming are mapped from source evidence: satisfied by the port map and conflict note in R785.
- Backend binary/resource expectations are compared against committed resources: satisfied by the resource/generated binary comparison and packaged script expectation mismatch.
- No code is edited in this audit step: satisfied; only ledger artifact files were added for the audit result/check.

## Execution Map

- The audit used `find`, targeted `rg`, `sed`, and `ls -l`.
- It read the source/dev script, both packaged scripts, and `resources/config/services.json`.
- It did not run remediation commands.

## Stress Test

- Checked both canonical resource copy and generated packaged asset copy so the audit was not fooled by one copy being clean while the other remained stale.
- Checked scripts and configs together, exposing the port-name mismatch that would not appear from script-only inspection.

## Residual Risk

- The audit did not inspect every Rust/Tauri consumer of `services.json`; this is acceptable for P804 because P805 is scoped to remediation and can inspect usage before patching.
- The generated build output directory under `gen/apple/build` was intentionally not treated as an editable source of truth.

## Result IDs

- R785
