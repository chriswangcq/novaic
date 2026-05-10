# P025 Factory Check

## Summary

Success for P025. Cortex now has an explicit LogicalFS authority factory and tests proving owner-prefix construction and invalid agent id rejection.

## Evidence

- `novaic-cortex/novaic_cortex/workspace_authority.py` defines `agent_owner_prefix` and `build_workspace_file_authority`.
- `build_workspace_file_authority` returns `StoreBackedLogicalFileAuthority` with `LogicalFileAuthorityLayout(owner_prefix=agents/{agent_id})`.
- `novaic-cortex/tests/test_workspace_authority.py` covers valid prefix creation and invalid ids.
- Test command passed: `7 passed in 0.15s`.
- Scan found no `CortexLogicalFileAuthority` in the helper or tests.

## Criteria Map

- Factory creates `StoreBackedLogicalFileAuthority` with explicit owner prefix: satisfied.
- Agent id validation matches Workspace constraints: satisfied by invalid id tests.
- No old authority import or use: satisfied by scan.
- Tests cover valid and invalid cases: satisfied.

## Execution Map

- Added helper module and targeted tests.
- Ran targeted tests and old-authority scan.

## Stress Test

- Invalid cases include empty, whitespace, slash, double-dot, NUL, and non-string id.
- Verified object-key mapping through `authority.key("/rw/scratch/a.txt")`.

## Residual Risk

- The helper is not yet used by Workspace/runtime; P026/P027 cover cutover.
- Test suite still uses old direct constructor patterns until P028.

## Result IDs

- R022
