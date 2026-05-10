# Active Stack And Status Projection Remediation

## Problem

LLM context now reads ContextEvents, but active stack/status still walks materialized projection files such as `steps/_index.jsonl` and scope `meta.json`. This is acceptable as a projection, but not perfect if the target is a unified state model.

## Success Criteria

- Decide whether active stack/status should be an event-derived projection, SQLite projection, or Workspace projection.
- Define migration path from projection walking to the chosen model.
- Include compatibility removal and tests proving skill_begin/skill_end/finalize status derives from the new model.

