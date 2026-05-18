# T094 Result: Reference and Runbook Docs Residue Scan

## Summary

Scanned active reference/runbook docs, cleaned stale current-guidance wording in cloud production and blob service docs, and verified remaining hits are intentional.

## Scope

- `docs/reference/*.md`
- `docs/runbooks/*.md`

## Commands Run

```bash
find docs/reference docs/runbooks -type f -name '*.md'
rg -n "TODO|FIXME|compat|fallback|legacy|migration|old[-_ ]path|direct[-_ ]tool|base64|back-compat|shim|temporary|sunset" $(cat /tmp/novaic-reference-runbook-docs.txt)
```

## Changes

- `docs/runbooks/cloud-production.md`: changed `legacy env file` wording to retired env file wording.
- `docs/reference/blob-service.md`: renamed “No Fallback Rule” to “BlobRef Reader Rule”, changed migration-input wording to retired-input wording, and renamed the Cortex adapter section to “Cortex Object Store Bridge”.

## Findings

- Remaining `S3-compatible` is protocol naming, not compatibility branch guidance.
- Remaining `Do not reintroduce base64 upload APIs` is active safety guidance.

## Verification

- Focused reference/runbook rescan completed after cleanup.

## Result

Reference and runbook docs no longer present the cleaned old-path wording as current operational guidance.
