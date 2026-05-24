# ICE/TURN discovery not fully closed

## Summary

The implementation closes the discovered code/config bug, and the API host secret has been repaired, but the problem asked for deployed prod/staging ICE/TURN discovery to be working. The new Gateway route and fail-fast behavior are not yet running in prod/staging, so the deployed credential endpoint still has not been proven to return relay-capable ICE servers.

## Blocking Gaps

- `R000` explicitly records that the new Gateway/app/common code is not deployed yet.
- The pre-deploy direct Gateway check showed `/api/turn/credentials` returning 404 on prod and staging loopback ports.
- Cross-network peers cannot rely on the fixed ICE/TURN discovery path until a Release Controller deployment puts the new Gateway code behind both namespace ports and verifies the endpoint.

## Result IDs

- R000
