# Storage Schema Changelog

## 2026-02-20

- schema: `contracts/schema/storage-api.v1.schema.json`
- change_type: governance_baseline
- summary:
  - established breaking-change approval policy
  - formalized required reviewers and evidence rules
- update_note:
  - no schema shape change in this entry; this is governance and process baseline

## Changelog Rules

- Any change to `contracts/schema/storage-api.v1.schema.json` must update this file.
- Changelog entry must include:
  - schema path
  - change_type (`non_breaking` | `breaking` | `governance_baseline`)
  - summary
  - update_note (consumer impact and rollout note)
