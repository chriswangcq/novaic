# Fresh Static Residue Scan Audit

## Problem

Run the current repository static residue scan with the P531 pattern and store the raw, production, test, and count outputs. This child belongs under P533 because the audit must not rely only on older scan artifacts after P540 changed code.

## Success Criteria

- Fresh raw residue output is stored as a file artifact.
- Fresh production residue output is stored as a file artifact.
- Fresh test residue output is stored as a file artifact.
- Fresh count summary includes raw hit/file counts and production/test hit/file counts.
- The output explicitly notes any expected count delta caused by P540 cleanup.
