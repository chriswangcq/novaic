# Deploy and verify TURN credential endpoint

## Problem

The ICE/TURN code path is fixed locally, and the API host has the required `turn_secret`, but prod/staging are still running the old Gateway image where `/api/turn/credentials` is missing. The fixed route must be deployed and verified before ICE/TURN discovery can be considered solved.

## Success Criteria

- Deploy a new API backend image containing the Gateway TURN endpoint and strict TURN config via the Release Controller path.
- Verify prod and staging Gateway instances return authenticated `/api/turn/credentials` responses with at least one `turn:` or `turns:` URL.
- Verify Gateway startup would fail in deployed envs without `turn_secret`, and the current API host secret is present.
- Confirm no WebRTC code path still silently uses STUN-only in deployed cross-network mode.
