# Business service and subscriber boundary classification

## Problem
Classify Business service/subscriber code as product/business computation and event consumption. Verify entrypoints, subscriber launch surfaces, dependency boundaries, and separation from Queue/Runtime worker ownership.

## Success Criteria
- Business service/subscriber entrypoints and launch references are listed with evidence.
- Business logic, subscriber behavior, and event handling are separated from Queue session FSM ownership and Runtime worker orchestration.
- Hidden environment/config dependency residue is checked where classification touches subscriber behavior.
- Stale misleading claims are patched or recorded.
