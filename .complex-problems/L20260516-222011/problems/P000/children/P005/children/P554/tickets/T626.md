# Remove Cortex Materialize and Legacy Scratch Fallback Residue

## Problem Definition

P553 found one high-confidence stale/backdoor candidate under the LogicalFS/Sandbox/Blob layering audit: `Workspace.materialize()` and the legacy root-level `/rw/scratch` layout/tests. Even if there is no production caller, leaving the API and layout in place is residue that can invite future code to bypass the intended `Workspace -> LogicalFS materialized view -> sandboxd` boundary.

## Proposed Solution

Remove or replace the `Workspace.materialize()` API and delete/adjust tests that encode the old root `/rw/scratch` materialization contract. Then run a targeted static scan to ensure no production or test path still depends on direct materialization or old sandbox backing paths. If the change uncovers multiple independent residues, split them into child problems before editing further.

## Acceptance Criteria

- `Workspace.materialize()` is removed or reduced to a non-bypass internal path only if a current caller proves it is necessary.
- Legacy root `/rw/scratch` assumptions are removed or replaced with the intended LogicalFS/subagent-aware RW layout.
- Tests that only protect the stale materialize contract are removed or rewritten to protect the current LogicalFS/sandboxd contract.
- Static scans show no active local fallback/backdoor materialization route remains.
- Any ambiguous residue discovered during implementation is split into follow-up problems instead of guessed.

## Verification Plan

Run focused Cortex workspace/logicalfs tests, sandbox/logicalfs boundary tests, and static guard scans for `materialize`, `novaic-cortex-sandbox`, `/rw/scratch`, direct temp path leakage, and local shell fallback terms.

## Risks

- Some tests may still rely on `Workspace.materialize()` as a convenient fixture helper; they should be rewritten only if they protect current behavior.
- Removing stale helper code can expose hidden assumptions in context/workspace tests.
- The remediation should not reintroduce Blob-as-workspace or runtime-local shell execution as a replacement.

## Assumptions

- P553's classification is accepted: no production caller requires `Workspace.materialize()`.
- LogicalFS/sandboxd is the intended execution file view boundary.
- Physical cleanup is preferred over compatibility preservation.
