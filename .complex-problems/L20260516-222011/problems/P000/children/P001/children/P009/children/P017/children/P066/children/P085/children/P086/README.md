# App settings and model config residue classification

## Problem

`novaic-app/src` contains non-monitor settings/model config hits such as provider compatibility names, local config legacy wording, and settings labels. These may be benign product vocabulary, but they need explicit classification and stale wording cleanup.

## Success Criteria

- Inspect settings/model config hits for fallback, compat, legacy, migration, and provider compatibility wording.
- Classify each hit as current product vocabulary, benign compatibility naming, stale comment, or active risk.
- Remove or rewrite stale comments/names when safe.
- Run focused tests or a no-code-change verification for the inspected settings/model files.
