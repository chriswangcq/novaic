# Residue hotspot search and triage

## Problem

Search for stale, misleading, or old-path residue across active code/tests/docs: compatibility shims, direct tool names that should be shell CLI, old `/tmp/novaic-cortex-sandbox-*` path dependencies, base64/image leakage, TODO/FIXME, fallback/backdoor wording, and disabled/skipped tests.

## Success Criteria

- Residue searches use bounded `rg` patterns and record evidence pointers.
- Hits are triaged into active issue, benign historical ledger/doc, or candidate for another child problem.
- High-confidence tiny cleanup can be fixed only if directly supported by evidence and tests.
- Result lists concrete follow-up targets for the specialized child problems.
