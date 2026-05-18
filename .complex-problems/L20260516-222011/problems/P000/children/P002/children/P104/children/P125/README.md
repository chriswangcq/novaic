# Blob Artifact and Display Base64 Regression Sweep

## Problem

After artifact CLI and display projection checks, run a final regression sweep for base64/data URL leakage in shell/display history contracts.

## Success Criteria

- Run focused runtime/Cortex tests for tool-output manifests, display history, and no historical tool image injection.
- Search active code/tests for raw media/base64 transport paths and classify allowed protocol-local uses.
- Add or adjust the smallest regression guard if an uncovered leak path remains.
