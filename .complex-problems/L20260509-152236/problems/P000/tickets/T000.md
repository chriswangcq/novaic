# Audit tools for resource-oriented context optimization

## Problem Definition

The previous backend analysis identified screenshot/base64 prompt bloat. The broader question is whether other tools or shared tool infrastructure need optimization under the same file/display/resource-oriented model.

## Proposed Solution

Perform a design-and-code audit of tool execution and result projection paths across Runtime/Cortex/Business. Identify tool families, risk classes, existing good patterns, and concrete follow-up implementation candidates. This ticket is analysis-only.

## Acceptance Criteria

- Cover Runtime executors, device tools, payload tools, display/audio tools, user attachment handling, Cortex step result projection, and context assembly.
- Rank optimization opportunities by priority.
- Distinguish immediate bloat risks from architectural cleanup.
- Preserve evidence pointers to files/lines.
- Record final audit result and success check in the ledger.

## Verification Plan

- Use `rg`, `nl`, and focused file slices to inspect the relevant code paths.
- Cross-check results against prior observed slow execution evidence.
- Validate/render ledger before final response.

## Risks

- The audit may over-index on screenshot symptoms and miss text/log or audio pathways.
- Some dynamic tools are mounted through Business/Device and may not have direct Runtime implementation in this repo.
- This is not a production fix; implementation must be tracked separately.

## Assumptions

- User wants an audit and optimization map, not immediate code changes.
- Existing uncommitted work in the repo should not be reverted or mixed with this audit beyond ledger artifacts.
