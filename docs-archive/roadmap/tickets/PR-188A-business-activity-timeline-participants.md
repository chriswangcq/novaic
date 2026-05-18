# PR-188A — Business Activity Timeline Participants Projection

> Historical note: superseded by PR-193. Monitor participants are now Entangled `agent-activity-participants`, not `agents.activity_timeline` response data.

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-03 |
| Repos | `novaic-business` |
| Parent | PR-188 |

## Goal

Extend `agents.activity_timeline` so Business returns user-facing monitor participants derived from internal subagent state.

## Current-State Analysis

`business/agent_actions.py` currently returns only `{records, count}`. The App therefore has no product-owned way to render the bottom Main/Subagent selector without reaching for raw `subagents`.

Business already has access to:

- `subagent_utils.get_or_create_main_subagent(...)`
- `store.list("subagents", "", params={"agent_id": agent_id})`
- Cortex timeline records for the selected participant

## Implementation Plan

- Add a public participant projection shape:
  - `id`
  - `view_id`
  - `kind`
  - `label`
  - `status`
  - `activity_count`
- Derive main participant from the resolved main subagent.
- Derive child participants from Business `subagents` rows.
- Return participants from every `activity_timeline_action` response, including Cortex 404 responses.
- Keep raw runtime fields (`hrl`, `summary_lock`, `need_rest`, `wake_triggers`, `timeout_at`) out of the response.

## Tests

- Main-only response includes a main participant.
- Child subagents are projected as participants with safe fields only.
- Explicit `subagent_id` selects that participant.
- Cortex 404 still returns participants with empty records.

## Done Criteria

- App can render participants without subscribing to `subagents`.
- Business tests prove participant projection is public-field only.

## Closure

Closed 2026-05-03.

Implemented in `business/agent_actions.py`:

- `agents.activity_timeline` now returns `participants` and `selected_participant_id`.
- Participants expose only `id`, `view_id`, `kind`, `label`, `status`, and `activity_count`.
- Raw subagent runtime fields are not included.

Validation:

```bash
PYTHONPATH=.:../novaic-common:../Entangled/packages/server-python pytest -q tests/test_pr169_activity_timeline_action.py
python -m py_compile business/agent_actions.py
```
