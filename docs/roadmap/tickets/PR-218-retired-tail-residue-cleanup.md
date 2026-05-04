# PR-218 Retired Tail Residue Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Retired path physical cleanup |
| Created | 2026-05-04 |
| Scope | Packaged artifacts, active docs, test fixtures, Android device base64 data-plane endpoints |
| Dependencies | PR-216, PR-217 |

## Goal

Remove the remaining misleading tails from retired implementations so the active
tree reads like the previous branches never existed.

## Large Work Orders

### 1. Retired Packaged Artifact

- Objective: remove the retained retired storage executable artifact.
- Scope: root `dist/`.
- Result: the retained retired storage executable is no longer tracked or present.

### 2. Gateway / Blob Documentation Boundary

- Objective: stop describing Gateway app as a Blob byte carrier.
- Scope: Gateway architecture docs and Gateway topic docs.
- Result: docs say `/blob/` is a Nginx edge to Blob Service; Gateway app keeps
  auth/App WS/signaling/control-plane only.

### 3. Retired Result-store Naming

- Objective: remove retired result-store naming from active code and tests.
- Scope: Agent Monitor redaction code/tests, Cortex step index fixture, active
  architecture docs.
- Result: tests use neutral payload/step references, and UI code no longer
  carries retired prefix redaction.

### 4. Device Base64 Data-plane Endpoints

- Objective: delete JSON-base64 device file/app push endpoints.
- Scope: `vmcontrol` Android routes and Device path bindings.
- Result: the retired JSON-base64 app install and file push routes and action
  mappings are gone. Other protocol-required base64 encodings, such as
  screenshots, WebRTC cursor payloads, QMP, and guest-agent stdout/stderr, remain
  because they are not retired product data-plane branches.

## Acceptance

- No tracked retired storage executable artifact.
- Active Gateway docs no longer say Gateway app proxies Blob bytes.
- Active App/Cortex code has no retired result-store prefix fixture.
- Retired JSON-base64 app install and file push routes no longer appear in active device
  route or binding code.
- Focused tests and compile checks pass.

## Verification

- targeted `rg` for the retired artifact, Blob edge wording, retired result
  store prefix, and `*-from-base64` endpoints.
- `cd novaic-app && npm run test:unit -- src/components/Visual/ActivityTimeline.test.tsx src/components/Visual/ActivityTimeline.guard.test.ts`
- `cd novaic-app/src-tauri && cargo check`
- `cd novaic-cortex && pytest -q tests/test_step_index_outcome.py`
- `cd novaic-device && pytest -q`
