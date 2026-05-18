# Attach outbox worker-only implementation

## Problem

Implement worker-only attach delivery by removing repository eager publish and unused attach eager API.

## Success Criteria

- SessionRepository returns outbox pending attach result without publishing.
- Unused eager attach publish API removed if no production caller remains.
- Tests updated accordingly.
