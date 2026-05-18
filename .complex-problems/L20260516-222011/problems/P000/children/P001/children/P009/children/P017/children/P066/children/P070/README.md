# Cortex common fallback compatibility residue scan

## Problem

Cortex and common code may retain old compatibility branches around workspace paths, context projection, tool schemas, payload handling, or sandbox exposure.

## Success Criteria

- Focused scans cover `novaic-cortex` and `novaic-common` active code for fallback, compat, legacy, migration, TODO/FIXME, pass, skip, base64, and ephemeral path patterns.
- Hits are classified by active path status and risk.
- Safe tiny cleanup is applied directly if discovered.
- Touched Cortex/common areas receive focused tests or explicit no-code-change verification.
