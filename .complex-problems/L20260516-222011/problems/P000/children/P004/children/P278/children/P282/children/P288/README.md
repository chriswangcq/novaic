# Problem: Session rebuild projection and state read inventory

## Problem

Inspect rebuild, projection, and read helpers to understand how active session state is reconstructed/read, and whether any cache/view can drift from authoritative state.

## Success Criteria

- Map read/rebuild/projection methods and their source tables with file references.
- Explain whether active session reads derive from `tq_session_state` or another pointer.
- Identify test coverage for rebuild/projection/state ownership.
