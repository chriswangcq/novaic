# P568 Reproducible Scan Command Manifest

## Problem

P568 classified stable path compatibility residue but did not durably record the exact scan/read commands used to generate its artifacts. Add a small reproducibility manifest that lists the exact commands, output artifact paths, and the criteria each artifact supports.

## Success Criteria

- Adds a P568-specific manifest artifact containing exact scan/read commands and their output file paths.
- Maps each command/artifact to P568 criteria: temp/stable path scan, relevant code slices, intended guardrails vs risky fallback, and remediation-candidate identification.
- Does not perform implementation changes; this is documentation/evidence closure only.
