# Verify shell payload and output boundary tests

## Problem

After mapping and any wording corrections, focused tests must prove shell output stays bounded and full payload inspection is explicit. This belongs under P240 because the audit is not closed by source reading alone.

## Success Criteria

- Focused runtime shell output contract tests pass.
- Focused Cortex schema/payload inspection tests pass.
- Residue scans show no guidance that encourages raw base64 or full payload injection in normal context.
