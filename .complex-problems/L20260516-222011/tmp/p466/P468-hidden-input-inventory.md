# Session hidden input inventory

## Problem

Run a focused inventory for implicit inputs in session/worker paths: direct `os.environ`/`getenv` reads, module-level mutable globals, singleton/default config access, and duplicated configuration branching. This child should produce evidence and classify hit buckets, not edit source.

## Success Criteria

- Save guard artifacts under `.complex-problems/L20260516-222011/tmp/p468/`.
- Cover `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, `novaic-business/business/subscribers`, and relevant tests.
- Classify retained hits as safe boundary reads, test-only fixtures, or risky production hidden inputs.
- Name any exact files/functions that require remediation by later children.
