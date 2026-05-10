# P017 Success Check - Active Stack Authority Audit Complete

## Summary

P017 is solved. The audit maps control-stack file-walk authority, active-path routing, semantic context stack projection, operational SQLite substrate, finalize behavior, and relevant test surfaces with concrete file/line evidence.

## Evidence

- R013 catalogs `_collect_active_stack`, `context_status`, `skill_begin`, `skill_end`, `scope_end`, `resolve_active_scope_path`, `set_active_stack/get_active_stack`, context event writer/projection/read-model, and stack tests.
- R013 explicitly separates operational control stack authority from semantic context-event projection stack.
- R013 identifies active-path routing users beyond the original three endpoints: `steps_write`, `scope_write_assistant`, context append/batch, and meta helper endpoints.

## Criteria Map

- All `_collect_active_stack`, `context_status`, `skill_begin`, `skill_end`, finalize, and stack-projection call sites are cataloged: satisfied by R013 call-site map.
- Each call site is classified as runtime authority, semantic context projection, trace/debug, or test-only: satisfied by R013 boundary decisions and test-surface section.
- Next implementation tickets have explicit boundaries and no ambiguous stack source remains unclassified: satisfied by R013 known gaps and boundary decisions; future P018/P019/P020 tickets must include the active-path routing endpoints discovered here.

## Execution Map

- T015 was executed as a read-only audit.
- No production code was changed.
- R013 records the audit output used to guide Phase 3B/C/D.

## Stress Test

- The audit looked beyond `_collect_active_stack` and found indirect `resolve_active_scope_path` dependencies that would otherwise preserve old authority after a superficial cutover.
- The audit distinguishes context event projection LIFO checks from operational runtime LIFO checks to avoid collapsing two different models.

## Residual Risk

- The audit is not itself the migration; P018/P019/P020/P021 must implement and verify the cutover.
- Future tickets must not narrow scope back to only `skill_begin`, `skill_end`, and `context_status`.

## Result IDs

- R013
