# Child Problem: scan and classify active docs for output contract drift

## Problem

Before editing docs, active versus historical guidance must be classified. Otherwise edits may miss the docs developers actually read or churn old design notes unnecessarily.

## Success Criteria

- Targeted scans identify active docs mentioning shell, display, blob/artifact, base64, and ephemeral Cortex backing paths.
- Historical/archival material is classified separately from active guidance.
- The scan recommends exact files to update.
