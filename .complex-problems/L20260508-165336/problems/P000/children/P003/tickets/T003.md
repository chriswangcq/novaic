# Ticket: Scan Legacy Paths, Compat Branches, Residue Vocabulary, and Guards

## Problem Definition

The user is worried about old branches remaining live after new FSM/DSL work. We need to scan for legacy compatibility paths, retired vocabulary, old active-session tables, shadow toggles, bypass branches, and CI guards that should prevent regression.

## Proposed Solution

Run existing residue/guard scripts and targeted text searches across runtime, queue service, task queue, tests, and CI scripts. Classify hits into active production residue, test/guard-only references, and harmless historical comments. Record any hard gap that needs a follow-up ticket.

## Acceptance Criteria

- Run the existing CI/lint guards relevant to retired runtime/FSM vocabulary.
- Search for legacy/compat/fallback/shadow/toggle terms and old session tables.
- Identify whether any old live branch still bypasses the new session/FSM/roster path.
- Distinguish active production hits from test guard/documentation hits.
- Record explicit residual risks and guard coverage.

## Verification Plan

- Run existing lint scripts: retired vocabulary, runtime supervision, deploy smoke, start config contract, generated artifact lint.
- Use `rg` searches for legacy keywords, old table names, compatibility branches, shadow flags, and old active-session APIs.
- Inspect any non-test production hits with line-numbered reads.
- Record a result with hit classification.

## Risks

- Broad keyword scans can produce false positives in tests that intentionally assert absence of old vocabulary.
- Some comments may contain historical terms without active behavior; the result must not overstate them as live branches.

## Assumptions

- “No backward compatibility needed” means active code should not preserve old behavior branches unless guarded as migration-only documentation or tests.
