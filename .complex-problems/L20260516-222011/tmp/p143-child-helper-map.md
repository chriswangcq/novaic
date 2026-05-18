# context.jsonl helper implementation map

## Problem

The workspace helper methods for `context.jsonl` must be mapped and classified at implementation level: whether they append raw messages, projections, or compatibility data, and whether any helper behavior can carry large payloads.

This belongs under `P143` because caller analysis is unsafe without first knowing exactly what each helper does.

## Success Criteria

- `read_context`, `append_context`, `append_context_projection`, `append_context_batch`, and `append_context_batch_projection` are mapped with source pointers.
- Each helper is classified by role and write/read behavior.
- Any helper behavior that can persist full raw payloads is identified or ruled out.
