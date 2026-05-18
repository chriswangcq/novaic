# P785 Check: App Resource Generated Asset And Backend Startup Remediation

## Verdict

`success`

## Summary

After the `P811` follow-up, the original P785 app remediation is complete. App VMuse resource/generated copies are synchronized to the HTTP-only VMuse contract, backend packaged resource scripts/configs match, the packaged Blob Service binary expectation is consistent, stale VMuse MCP config is removed, and HD screenshot comments now describe Blob/display artifact flow rather than direct LLM injection.

## Criteria Map

- VMuse source cleanup synchronized into app resource and generated Apple asset copies: satisfied by `P800`, `P801`, and the `P811` sync-script follow-up.
- App startup scripts and packaged/generated backend scripts reflect current topology: satisfied by `P802`; packaged backend scripts/config copies compare equal.
- `PORT_CORTEX=19996` versus `vmcontrol` naming conflict resolved: satisfied by `P802`; app service configs now use `cortex` for port `19996`.
- Backend binary/resource expectations match committed resources: satisfied by `P802`; `resources/backends/novaic-storage-a` matches generated asset binary.
- Stale HD screenshot-to-LLM comment cleaned up: satisfied by `P803`.
- Focused script/config checks run: satisfied by `bash -n`, JSON validation, resource/generated comparisons, sync-script dry-run checks, and focused residue scans.

## Evidence

- `P800` / `R783` / `C830`: app VMuse resource copy sync completed.
- `P801` / `R784` / `C831`: generated Apple VMuse asset copy sync completed.
- `P802` / `R792` / `C840`: backend startup graph cleanup completed.
- `P803` / `R793` / `C841`: HD screenshot comment cleanup completed.
- `P811` / `R795` / `C843`: stale VMuse `main.py` validation removed from `sync-vmuse-resource.sh`.
- Fresh parent-level checks:
  - backend scripts compare equal between resource and generated copies
  - service configs compare equal between resource and generated copies
  - `novaic-storage-a` binary compares equal between resource and generated copies
  - `bash -n` passes for app startup and VMuse sync scripts
  - `python -m json.tool` passes for app service configs
  - `rsync --dry-run --itemize-changes` from source VMuse to both app VMuse bundles returns no output
  - `diff -qr` between app VMuse resource and generated copies returns no output
  - focused scans find no stale `main.py`, FastMCP/SSE/stdio/MCP URL residue in active app VMuse paths

## Stress Test

The first P785 check intentionally failed after finding the stale `sync-vmuse-resource.sh` `main.py` validation. The follow-up fixed that executable maintenance path, then the parent was rechecked across script syntax, generated/resource parity, source-to-bundle dry-run parity, config parity, binary parity, and stale marker scans. Apparent `novaic-blob-service` hits in the dev startup script were reviewed and classified as current source-repo naming for Blob Service, while `novaic-storage-a` is the packaged binary name.

## Residual Risk

No P785-scoped residual risk remains. Broader app repository changes outside startup/resource/VMuse/HD-comment scope are not judged by this problem.
