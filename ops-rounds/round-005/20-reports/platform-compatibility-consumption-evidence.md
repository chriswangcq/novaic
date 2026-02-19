# Platform Compatibility Consumption Evidence (Round 005)

## Goal
Provide auditable evidence for `>=5` component compatibility consumption with exact workflow/file references.

## Evidence List

1. component: `novaic-backend`
   - compatibility source: `compatibility.yaml` (`repos.id: novaic-backend`)
   - workflow reference: `.github/workflows/ci.yml` job `compatibility-matrix`
   - check detail: validates presence and minimum repo count in `compatibility.yaml`

2. component: `novaic-app`
   - compatibility source: `compatibility.yaml` (`repos.id: novaic-app`)
   - workflow reference: `.github/workflows/ci.yml` job `compatibility-matrix`
   - check detail: same guardrail consumed before frontend/tauri jobs

3. component: `novaic-mcp-vmuse`
   - compatibility source: `compatibility.yaml` (`repos.id: novaic-mcp-vmuse`)
   - workflow reference: `.github/workflows/ci.yml` job `compatibility-matrix`
   - check detail: matrix gate blocks whole pipeline on invalid compatibility file

4. component: `novaic-gateway`
   - compatibility source: `compatibility.yaml` (`repos.id: novaic-gateway`)
   - workflow reference: `.github/workflows/ci.yml` job `compatibility-matrix`
   - check detail: gate participates in `ci-success` dependency chain

5. component: `openclaw-main`
   - compatibility source: `compatibility.yaml` (`repos.id: openclaw-main`)
   - workflow reference: `.github/workflows/ci.yml` job `compatibility-matrix`
   - check detail: repo entry counted in mandatory `>=5` matrix validation

## Command Evidence
- `rg "compatibility.yaml|compatibility-matrix" .github`
- `rg "repos:|id: \"novaic-backend\"|id: \"novaic-app\"|id: \"novaic-mcp-vmuse\"|id: \"novaic-gateway\"|id: \"openclaw-main\"" compatibility.yaml`

## Result Summary
- `.github/workflows/ci.yml` contains active `compatibility-matrix` gate and is required by `ci-success`.
- `compatibility.yaml` contains explicit entries for the 5 target components above.
