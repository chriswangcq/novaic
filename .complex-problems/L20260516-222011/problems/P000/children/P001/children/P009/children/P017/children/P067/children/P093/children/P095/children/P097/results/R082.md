# T089 Result: Repository Scripts Residue Scan

## Summary

Scanned non-CI repository scripts for stale residue markers, cleaned one stale `fallbacks` wording in `scripts/start.sh`, and verified shell syntax.

## Scope

Non-CI script files selected from `scripts/`, package `scripts/` directories, and top-level run/start/build/deploy/setup shell helpers, excluding `scripts/ci`, thirdparty, rustdesk reference, and test directories.

## Commands Run

```bash
rg --files | rg '(^scripts/|/scripts/|(^|/)run_.*\.sh$|(^|/)start\.sh$|(^|/)dev\.sh$|(^|/)deploy.*\.sh$|(^|/)build.*\.sh$|(^|/)setup.*\.sh$)' | rg -v '(^thirdparty/|^rustdesk-ref/|^scripts/ci/|/tests?/|\.github/)'
rg -n "skip\(|pytest\.mark\.skip|xfail|TODO|FIXME|compat|fallback|legacy|migration|direct[-_ ]tool|base64|pass\b" $(cat /tmp/novaic-nonci-script-files.txt)
bash -n scripts/start.sh
bash -n novaic-blob-service/scripts/verify_contract_version_blob.sh
```

## Changes

- `scripts/start.sh`: rewrote the Cortex PYTHONPATH comment from “bundled fallbacks” to “explicit workspace paths”.

## Findings

- Remaining `pass` matches are ordinary CLI prose such as “pass as CLI args” / “pass device ID”.
- `novaic-blob-service/scripts/verify_contract_version_blob.sh` intentionally constructs a retired `legacy_facade` key to assert the blob service does not expose it.
- No other safe stale non-CI script residue was found.

## Verification

- `bash -n scripts/start.sh` passed.
- `bash -n novaic-blob-service/scripts/verify_contract_version_blob.sh` passed.

## Result

Repository script residue was cleaned where safe and remaining matches are intentional or harmless prose.
