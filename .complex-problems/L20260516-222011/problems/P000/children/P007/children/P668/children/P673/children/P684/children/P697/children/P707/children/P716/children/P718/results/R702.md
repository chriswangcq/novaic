# Business/subscriber active documentation remediation result

## Summary

Patched the active stale documentation identified by P717. `docs/entangled-architecture.md` now describes Business as the product entity/action write authority and Gateway as edge/endpoint discovery, not a product CRUD proxy. `docs/gateway/rest-auth-and-deps.md` now limits Gateway REST to edge/auth/TURN/Blob/App WS surfaces and points product writes and device/VM behavior to Business/Device.

## Done

- Updated `docs/entangled-architecture.md` storage-layer wording so Gateway no longer appears to currently inherit or host the product entity store.
- Updated `docs/entangled-architecture.md` Business integration wording so service-side product entity writes and action hooks are owned by Business, while Gateway is edge/auth/signaling/blob/endpoint discovery only.
- Updated `docs/entangled-architecture.md` Sync Contract section so product entity writes no longer claim to flow through Gateway CRUD proxy.
- Updated `docs/gateway/rest-auth-and-deps.md` so Gateway no longer claims generic product CRUD, device association, or VM orchestration ownership.

## Verification

- `python3 scripts/ci/lint_docs_status_consistency.py` passed.
- Focused scan for stale Gateway CRUD / Gateway product entity / Gateway SqlEntityStore wording in patched docs and adjacent active architecture docs was rerun.
- Remaining focused scan hits are now current negative statements, explicit old-architecture notes, or retained boundary docs such as `docs/gateway/entangled-hooks.md` and `docs/gateway/internal-and-workers.md`.
- Reviewed `git diff -- docs/entangled-architecture.md docs/gateway/rest-auth-and-deps.md`; changes are localized to the intended sections.

## Known Gaps

- No code was changed in this ticket.
- P719 still needs to audit active Business/subscriber code boundaries.
- P720 still needs the final cross-surface verification sweep after all P716 children close.

## Artifacts

- Changed: `docs/entangled-architecture.md`
- Changed: `docs/gateway/rest-auth-and-deps.md`
- Verification command: `python3 scripts/ci/lint_docs_status_consistency.py`
- Verification scan: `rg -n 'Gateway.*(CRUD|产品实体|entity CRUD|实体 CRUD|设备|VM)|CRUD.*Gateway|Gateway 鉴权.*Business|Gateway 直接继承|GatewayEntityStore|Gateway.*SqlEntityStore' docs/entangled-architecture.md docs/gateway/rest-auth-and-deps.md docs/gateway docs/architecture -g '*.md'`
