# Foundational boundary residue scan and disposition

## Problem

Run high-signal scans for stale claims that collapse Blob, LogicalFS, or Sandbox responsibilities into Cortex or another layer. Produce a disposition list that separates active-cleanup candidates, history/docs, guard/test strings, and follow-up risks.

## Success Criteria

- Scan commands and raw outputs are saved.
- Candidates are classified by disposition with evidence.
- Active cleanup candidates, if any, are clearly handed to the remediation child.
- No production code is changed in this scan-only child.
