# CLI inventory success check

## Summary

Success. The shell CLI surfaces are inventoried and the live blob-contract risks are identified with code evidence.

## Evidence

- `shell_capabilities.py` defines the generated shell entrypoints: `agentctl`, `cortex`, and `devicectl`.
- `devicectl hd screenshot` maps to `desktop/screenshot` and upstream `hd_tools.rs` returns base64 under `screenshot`.
- `devicectl hd file-pull` maps to `file/pull` and upstream `hd_tools.rs` returns base64 under `data`.
- `agentctl media audio-qa` requires `blob://` input and returns text answer, not an artifact payload.
- `cortex payload` commands are bounded read/search/summarize/qa utilities.

## Criteria Map

- Command surfaces inventoried: satisfied for `agentctl`, `cortex`, and `devicectl`.
- Output classes identified: satisfied by text/control, bounded payload inspection, and artifact-producing/risky classifications.
- Confirmed risks listed with pointers: satisfied for `devicectl hd screenshot` and `file-pull`.
- Repair targets clear: satisfied by P002/P003/P004 child problems.

## Execution Map

- `T001` executed a bounded read-only code inspection and recorded `R000`.

## Stress Test

- Considered both image-producing and file-producing HD commands, not just the visible screenshot failure.
- Checked whether `agentctl media` creates a hidden violation; it only sends base64 internally to Factory after reading a blob input and returns text.

## Residual Risk

- Non-blocking: remote service behavior can still differ at runtime, but the active code path clearly identifies the artifact-producing contracts that need repair.

## Result IDs

- R000
