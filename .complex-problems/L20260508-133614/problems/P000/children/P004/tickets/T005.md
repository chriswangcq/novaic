# P004 Ticket - 旧词汇、退休注释、transitional allowlist 清理

## Problem Definition
The repo still contains legacy wording and transitional guard allowlists that imply retired paths are active. This residue is dangerous in AI-assisted maintenance because future edits may preserve or revive old concepts by mistake.

## Proposed Solution
Search for known stale terms and transitional markers, remove or rename active code/docs/tests where the old wording is no longer accurate, and tighten CI guards so transitional allowlists are not silently accepted.

## Acceptance Criteria
- Known old active-session names are renamed or clearly isolated as compatibility-free current state APIs.
- Retired prompt-splice comments are removed or rewritten to current behavior.
- `TRANSITIONAL` allowlist residue is removed from current CI guard scripts.
- Tests/lints verify no targeted stale terms remain in active code paths.

## Verification Plan
- Run `rg` for stale terms and transitional markers.
- Patch current code/tests/docs/lints.
- Run affected tests/lints.
- Add focused residue guard if existing guard does not cover the terms.

## Risks
- Some historical roadmap docs may intentionally mention retired names. Do not churn archival docs unless they affect active guidance.

## Assumptions
- No backward compatibility is required for legacy helper names.
