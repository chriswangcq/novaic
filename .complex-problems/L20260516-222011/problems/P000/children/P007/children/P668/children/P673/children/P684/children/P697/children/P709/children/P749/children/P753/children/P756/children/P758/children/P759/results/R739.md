# Gateway test residue discovery

## Summary

Scanned Gateway test-like files with bounded commands and spot-read the high-signal hits. No stale remediation candidate was found in Gateway tests.

Evidence:
- Test file discovery found `novaic-gateway/tests/test_pr141_no_db_access_alias.py`, `test_deps_internal_tasks.py`, `test_pr152_gateway_boundary.py`, `test_pr121_gateway_entangled_boundary.py`, `test_pr119_no_legacy_api_schemas.py`, `conftest.py`, and `tests/unit/gateway/test_entangled_endpoint_only.py`.
- Focused residue search output is saved at `.complex-problems/L20260516-222011/tmp/p759-gateway-test-scan.txt`.
- `novaic-gateway/tests/test_pr152_gateway_boundary.py` is an active guard suite proving Gateway stays a thin boundary, rejects direct query token fallback, keeps old file proxy and from-base64 Blob facade deleted, and keeps local DB migration residue out.
- `novaic-gateway/tests/test_pr121_gateway_entangled_boundary.py` is an active guard suite proving Gateway only exposes/discovers the public Entangled sync endpoint while Business/Subscriber retain HTTP consumption.
- `novaic-gateway/tests/test_pr119_no_legacy_api_schemas.py` is an intentional deletion guard for the old schema module.

Classification:
- Hits containing `direct`, `fallback`, `legacy`, `business`, `blob`, and `gateway` are guard assertions, not active stale fixtures.
- `mode: "direct"` in `test_gateway_contracts_build_upload_config_without_route_dict_bags` describes direct Blob upload mode, not a direct LLM/tool or business bypass.
- No screenshot/media/base64 route expectation remains except a negative assertion that `@app.post("/api/blobs/from-base64")` is absent.

No product code was modified.
