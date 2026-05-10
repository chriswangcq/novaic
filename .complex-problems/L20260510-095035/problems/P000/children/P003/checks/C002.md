# Check: Cutover And Old-Branch Cleanup Complete

## Summary

P003 is successful: the old lazy-RO command-string behavior is no longer encoded in tests or active code symbols, and the focused sandbox tests pass.

## Criteria Map

- Old lazy-RO test replaced: satisfied by R002.
- Provider capability and RW env vars tested: satisfied by R002.
- Old command-gating function names absent: satisfied by residue audit in R002.
- No `include_ro = command` semantic branch: satisfied by residue audit in R002.
- Focused sandbox tests pass: satisfied by R002 verification.

## Execution Map

- Result IDs checked: R002.
- Evidence: pytest pass and rg residue audit.

## Stress Test

The check explicitly preserves only the old ephemeral-path rejection path, because users may still paste leaked historical `/tmp/novaic-cortex-sandbox-*` paths. That is a safety guard, not a current execution branch.

## Residual Risk

- Full package tests and schema doc wording still need P004 verification.
- True mounted `/cortex` remains a provider capability gap, not a local-mirror feature.
