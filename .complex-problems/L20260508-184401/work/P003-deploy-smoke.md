# Deploy and production smoke

## Problem

Deploy the repair to production and run a controlled smoke check proving a new user IM reaches queue/session runtime state and no longer fails silently before agent monitor activity.

## Success Criteria

- Code is deployed to `root@api.gradievo.com`.
- Relevant services are restarted and healthy.
- Smoke input is observed in Entangled.
- Matching notification does not end in dispatch failure.
- Queue/session runtime records input/session activity for the smoke input.
- Logs no longer show the same dispatch timeout and saga claim 500 loop for the smoke window.

