# Verify And Clean Payload Manifest Cutover

## Problem Definition

After payload manifest write/read semantics are implemented, Phase 4 needs a final gate proving Cortex owns payload semantic state through manifests and Blob remains raw byte storage. This includes full tests, static audits, and current-doc cleanup.

## Proposed Solution

- Run static audits for manifest write/read wiring, raw Blob semantic leakage, and old BlobRef-only assumptions.
- Update current docs so they describe Cortex payload manifests and Blob raw-byte ownership correctly.
- Run targeted payload tests, full Cortex tests, and `py_compile`.
- Record any remaining historical docs as historical, or update them if they are current architecture references.

## Acceptance Criteria

- Static audit proves live payload writes call `put_payload_manifest` and payload read failures use `PayloadReadError`/manifest status.
- Current docs mention Blob as raw byte storage and Cortex/SQLite manifest as semantic authority.
- Targeted payload/manifest tests pass.
- Full Cortex tests pass.
- `py_compile` over Cortex modules passes.
- No unclassified current-code/current-doc residue remains.

## Verification Plan

- Run `rg` audits for `put_payload_manifest`, `PayloadReadError`, failure codes, and Blob semantic wording.
- Run targeted payload tests.
- Run full `novaic-cortex/tests`.
- Run `python3 -m py_compile $(find novaic-cortex/novaic_cortex -name '*.py' | sort)`.

## Risks

- Full-suite failures may expose unrelated test assumptions from earlier phases; do not hide them.
- Docs may contain historical review records that should be classified rather than rewritten as current architecture.

## Assumptions

- P041-P043 are checked successful before this gate.
- Historical dated/roadmap docs can remain if they are clearly not current architecture guidance.
