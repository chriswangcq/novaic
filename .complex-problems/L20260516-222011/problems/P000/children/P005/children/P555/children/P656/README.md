# Final Post-Remediation Static Residue Scan

## Problem

Re-run the final local static scans after all remediation work to prove stale direct materialization, backing path, root scratch, implicit local fallback, and Blob-as-workspace authority residues are absent or explicitly classified.

## Success Criteria

- Runs post-remediation scans for `Workspace.materialize`, materialization methods, `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, `/rw/scratch`, implicit `localhost:19996` Cortex API defaults, and direct Blob workspace authority terms.
- Stores scan outputs under the ledger tmp directory.
- Classifies meaningful remaining hits as intended, defensive/test-only, historical, or follow-up-worthy.
- Creates no code changes unless a concrete active defect is found.
