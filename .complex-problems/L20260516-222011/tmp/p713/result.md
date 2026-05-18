# Result: P713 Gateway/app edge boundary discovery and map

## Summary
Gateway/app edge boundaries were discovered and mapped. Gateway is a thin edge service: Auth, App WS push/signaling, TURN, Entangled endpoint discovery, Blob edge/control-plane, and local auth-only SQLite. It does not own Business logic, Entangled schema/action authority, Queue DB/session FSM, Runtime execution, Device execution, or Cortex scope/context state.

## Artifacts
- `.complex-problems/L20260516-222011/tmp/p713/boundary-map.md`
- `.complex-problems/L20260516-222011/tmp/p713/gateway-file-tree.txt`
- `.complex-problems/L20260516-222011/tmp/p713/app-wrapper-files.txt`
- `.complex-problems/L20260516-222011/tmp/p713/gateway-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p713/launch-doc-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p713/residue-candidate-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p713/scan-commands.md`

## Key Evidence
- `novaic-gateway/main_gateway.py` docstring says thin gateway: auth, App WS bridge, worker SSE, authenticated Blob Service edge, local SQLite auth storage, Entangled sync endpoint discovery, and internal auth endpoints.
- `main_gateway.py` CLI requires Queue Service and Blob Service URLs, showing explicit dependencies rather than ownership.
- `gateway/api/app_client.py` says App WS is signaling-only and no entity data flows through it.
- `docs/gateway-architecture.md` states Gateway no longer owns business logic, device communication, or Entangled schema/action authority.
- `docs/gateway/README.md` documents the Business-Centric split and Gateway retained endpoints.

## Cleanup Candidates for P714
- Check whether `docs/runbooks/local-backends.md` is still current after service topology changes.
- Check active docs for any non-contrast claim that Runtime uses Gateway for business state or Gateway owns entity sync/schema.
- Consider clarifying the old-vs-new comparison table in `docs/architecture/service-topology.md` if its retired-claim rows can be misread.

## Verification and Caveats
This was a read-only discovery/map pass. No source files were changed. The residue-candidate scan is intentionally broad and includes roadmap/historical docs; P714 must classify active vs historical before patching.
