# Cross-network WebRTC release attempt result

## Summary

The WebRTC fix was built, pushed, and partially released through Release Controller, but the final parent commit release did not pass staging deployment. The failure is operationally specific: Docker Compose entered an inconsistent staging project state during container recreation, leaving stale `novaic-staging-*` containers and renamed half-created containers. This means P003 is not complete yet, because the release needs a recovery-safe Compose image deployment path before the final commit can be promoted.

## Done

- Release Controller built immutable API backend image `127.0.0.1:5000/novaic/api-backend:sha-082b3b1de24d`.
- Release Controller built immutable LLM Factory image `127.0.0.1:5000/novaic/llm-factory:sha-082b3b1de24d`.
- Both images were pushed to the host registry and recorded in run `20260524-153107-main-082b3b1de24d`.
- The frontend OTA deploy was re-run after changing the deploy relay host to the DNS-backed API host, and `https://relay.gradievo.com/resource/frontend/v0.3.0/index.html` references bundle `assets/index-D2ZcBCbV.js`.
- The deployed frontend bundle contains the expected no-fallback WebRTC markers: `request_keyframe`, `no video frame arrived`, and `relay-capable TURN credentials`.

## Verification

- Gateway/common/app local tests and builds passed before deployment.
- Earlier Release Controller staging/prod release for backend commit `163a782cb385` succeeded and exposed `/api/turn/credentials` on both prod and staging.
- Final Release Controller run `20260524-153107-main-082b3b1de24d` passed CI, lint, image build, and image push steps.
- Final run failed at `deploy-api-staging` with Docker Compose error: `No such container: fbd1afd0b71a_novaic-staging-entangled-1`.
- Direct `docker compose ps -a` for the staging project currently also fails with `No such container`, confirming the Compose project state is corrupt rather than the application image failing to start.

## Known Gaps

- The final parent commit `082b3b1de24d672b42cb129d45101d8e40d0872f` is not yet fully deployed through Release Controller.
- Staging must be cleaned and redeployed from the immutable image path.
- The deploy script should make image deployment recovery-safe for this exact Compose recreate failure so future Release Controller runs do not require manual surgery.
- Prod must only be promoted after the final staging release succeeds.

## Artifacts

- Release Controller run: `20260524-153107-main-082b3b1de24d`.
- API image: `127.0.0.1:5000/novaic/api-backend:sha-082b3b1de24d`.
- Factory image: `127.0.0.1:5000/novaic/llm-factory:sha-082b3b1de24d`.
- Frontend bundle marker: `assets/index-D2ZcBCbV.js`.
