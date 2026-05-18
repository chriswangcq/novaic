# Ticket: Cortex boundary residue remediation and verification

## Problem Definition
Use P710's boundary map to remediate safe active Cortex-facing residue that implies Cortex owns foundational file/sandbox infrastructure instead of semantic context/scope/workspace semantics and shell orchestration.

## Proposed Solution
Inspect the P710 cleanup candidates plus nearby docs/scripts, patch only active safe misleading wording, and verify no touched active surface still collapses Cortex with Sandboxd or foundational file authority. If cleanup is broader than the listed candidates, split instead of overreaching.

## Acceptance Criteria
- P710 cleanup candidates are reviewed and dispositioned.
- Safe active wording in scripts/docs is patched to distinguish Cortex semantic/context/shell orchestration from Sandboxd execution and LogicalFS/Blob file authority.
- Generated copies are handled consistently where required.
- Verification includes focused retired-phrase scans and relevant docs/script lint or syntax checks.

## Verification Plan
Run `rg` over active startup scripts and architecture docs for Cortex/sandbox/file-authority wording, patch with `apply_patch`, re-run focused scans, and run any relevant existing CI boundary lint.
