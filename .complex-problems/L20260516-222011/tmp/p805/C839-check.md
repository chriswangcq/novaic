# App Backend Startup Graph Remediation Check

## Summary

Success. R791 satisfies P805 by removing the concrete backend startup graph inconsistencies found in P804 and proving script/config/generated copies are synchronized.

## Evidence

- R791 aggregates successful child results P806-P809.
- Packaged blob startup now uses `novaic-storage-a` and no longer carries a packaged `novaic-blob-service` fallback.
- `19996` is now consistently exposed as `cortex` in app config, while the dev script treats Cortex as an external URL rather than a local port variable.
- Stale `runtime.vmuse_mcp_url` was removed.
- Resource/generated startup scripts, config files, and storage binary were compared and verified.

## Criteria Map

- Startup script variants and generated copies are synchronized or clearly marked dev-only: satisfied by script/config `cmp` and dev script boundary text.
- Port naming conflict is removed or clarified: satisfied by removing `PORT_CORTEX` and replacing `services.vmcontrol` with `services.cortex`.
- Script expectations match committed resources: satisfied by `novaic-storage-a` in resources and generated assets plus startup script preference.
- `bash -n` and targeted config scans pass: satisfied by R791 verification.

## Execution Map

- P806 fixed packaged blob/storage startup contract.
- P810 follow-up synchronized the missing storage binary into source resources.
- P807 clarified Cortex/VMControl URL naming.
- P808 removed stale VMuse MCP config.
- P809 performed final synchronization and residue scan.

## Stress Test

- The first P806 check failed deliberately when only script behavior improved but binary source drift remained. That follow-up was resolved before P805 was accepted.
- Final residue scan included old terms from all remediated issues rather than only testing new names.

## Residual Risk

- Historical git tracking of backend binaries remains uneven, but the storage binary needed by the startup contract is now present and visible for commit.

## Result IDs

- R791
