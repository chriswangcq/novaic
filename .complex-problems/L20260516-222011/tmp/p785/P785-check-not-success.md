# P785 Check: App Resource Generated Asset And Backend Startup Remediation

## Verdict

`not_success`

## Summary

The four child problems closed most of the app resource/generated/backend startup remediation, but a fresh skeptical scan found an active app sync script still bound to the deleted VMuse `main.py` entrypoint. That is within the P785 scope because it can re-break or block synchronization of the committed app VMuse resource/generated copies.

## Evidence

- `P800`, `P801`, `P802`, and `P803` are all recorded as `done` with successful checks.
- Backend startup/config checks still pass:
  - resource/generated backend scripts compare equal
  - resource/generated service configs compare equal
  - resource/generated `novaic-storage-a` binaries compare equal
  - `bash -n` passes for app startup scripts
  - `python -m json.tool` passes for app service configs
- HD comment residue scan is clean for stale screenshot-to-LLM wording in `hd_tools.rs`.
- Fresh residue scan found:
  - `novaic-app/scripts/sync-vmuse-resource.sh:11`
  - the script checks `"$VMUSE_REPO/src/novaic_mcp_vmuse/main.py"`, but source VMuse no longer has `main.py` after the HTTP-only cleanup.

## Why This Blocks Success

P785 is specifically about keeping app resource/generated copies synchronized with the cleaned source contract. A sync script that requires a removed source entrypoint is not harmless documentation residue; it is an executable maintenance path that will fail or encode the wrong contract the next time someone tries to refresh the committed VMuse bundle.

## Follow-up Needed

Create and execute a focused follow-up to update `novaic-app/scripts/sync-vmuse-resource.sh` to validate the current VMuse source contract, run the sync/check path, and verify no resource/generated divergence or stale `main.py` assumption remains.
