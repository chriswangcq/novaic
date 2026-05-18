# Cortex Stable Path Compatibility Residue Classification

## Problem

Classify Cortex occurrences of old temp backing paths, `/tmp/novaic-cortex-sandbox-*`, `/cortex/ro` `/cortex/rw` path compatibility, and path adapter residue. This belongs under P562 because path leakage previously caused runtime confusion and shell timeouts.

## Success Criteria

- Records exact Cortex scan commands and outputs for temp/stable path compatibility terms.
- Reads relevant code slices with line references.
- Separates intended guardrails from risky compatibility fallback.
- Identifies any remediation candidate for P554.
