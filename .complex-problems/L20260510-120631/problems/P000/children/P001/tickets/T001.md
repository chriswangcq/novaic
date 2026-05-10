# Implement business-agnostic LogicalFS package

## Problem Definition

LogicalFS needs a reusable substrate package that owns snapshot/view/patch types and materialization/diff logic without depending on Cortex or sandbox execution services.

## Proposed Solution

Create `novaic-logicalfs/logicalfs` with DTOs and a local view provider. The provider materializes explicit snapshots into temporary view roots, prepares stable `/cortex`-style env values from explicit layout inputs, validates cwd, observes RW changes, and returns a patch object. Add tests and forbidden-import scans.

## Acceptance Criteria

- `novaic-logicalfs` package exists with contracts and local provider code.
- Materialization and patch observation are tested.
- Env/layout generation takes explicit inputs only.
- Package imports no Cortex, sandbox core, sandbox sdk, agent runtime, agentctl, business, or common product modules.

## Verification Plan

- Run `PYTHONPATH=novaic-logicalfs pytest -q novaic-logicalfs/tests`.
- Run forbidden import scan against `novaic-logicalfs`.

## Risks

- DTO shape might need adjustment when Cortex adapter migration starts.

## Assumptions

- Initial implementation is package substrate, not daemon; service-ization can be a later physical deployment choice once the contract is clean.
