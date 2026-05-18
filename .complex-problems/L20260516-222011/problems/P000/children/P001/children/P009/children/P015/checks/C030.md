# P015 Check

## Judgment

Not success.

## Evidence Reviewed

The completed child work removed many active prompt/documentation residues, but a fresh broad scan still found direct-tool names outside intentionally narrow compatibility boundaries.

Important remaining hits:

- `novaic-common/tests/test_llm_assembly_contract.py` still uses `im_read` as a raw tool schema fixture and asserts it in `tool_names`.
- `novaic-agent-runtime/task_queue/utils/activity_projection.py` still has direct-tool labels for historical records. It is documented as monitor-only, but the naming is still easy to confuse with active tool surface.
- Multiple tests still use `im_reply` as historical direct-tool data. Some are valid regression fixtures, but the current scan does not yet separate valid historical fixtures from misleading current-contract fixtures.
- `novaic-agent-runtime/task_queue/tool_surface_policy.py` intentionally lists migrated tool names. This is probably valid, but it should be the policy exception rather than part of an untriaged residue pool.

## Why The Parent Cannot Close

The parent problem is not merely "fix the already found files"; it is "direct tool and hidden harness residue scan." A skeptical close requires that remaining direct-tool references are either:

1. Removed from current-contract examples and tests.
2. Isolated behind explicit legacy/migration naming.
3. Covered by a focused guard so future scans do not rediscover the same ambiguity.

That level of classification is not done yet.

## Residual Risk

If this closes now, the codebase still contains enough direct-tool vocabulary for future changes to accidentally re-normalize old direct tool paths.
