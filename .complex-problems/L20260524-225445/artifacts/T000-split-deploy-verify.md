# Deploy and verify cross-network WebRTC release

## Problem

After code/config fixes, the deployed prod/staging stack must actually run the corrected WebRTC path, with host infrastructure and release records matching the immutable release-controller workflow.

## Success Criteria

- Build, commit, and push all code/config changes in the relevant repo and parent repo pointers.
- Use Release Controller, not manual production scripts, to deploy the corrected backend/app-side service artifacts where applicable.
- Verify deployed TURN/registry/gateway configuration from the API host and confirm no stale host-process or manual paths are needed.
- Run local checks plus at least one deployment smoke check that proves ICE/TURN config is served and relay-capable.
- Record the final result in the complex-problems ledger with remaining known manual client-app update steps, if any.
