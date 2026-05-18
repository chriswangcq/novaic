# Business/subscriber boundary discovery and map

## Problem
Discover Business service and Subscriber entrypoints, launch surfaces, product/action-hook responsibilities, event drain/aggregation roles, and dependencies. Produce an evidence-backed boundary map.

## Success Criteria
- Business and Subscriber entrypoints/launch references are listed.
- Business domain/action-hook roles are separated from Queue, Runtime, Cortex, Gateway, Device, and Entangled ownership.
- Subscriber drain/aggregation role is separated from wake/session ownership.
- Hidden env/config dependency candidates and cleanup candidates are listed.
