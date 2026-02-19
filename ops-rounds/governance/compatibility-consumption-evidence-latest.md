# Compatibility Consumption Evidence (Latest)

counting_rule_id: compat-count-v1
counting_rule_version: v1
evidence_path_policy: evergreen
unique_component_count: 5
component_count_check: PASS

## Evidence Items

- component: `novaic-backend`
  - compatibility_source: `compatibility.yaml` (`repos.id: novaic-backend`)
  - workflow_reference: `.github/workflows/ci.yml` job `compatibility-matrix`
  - check_detail: CI fails when compatibility file missing or repo count < 5

- component: `novaic-app`
  - compatibility_source: `compatibility.yaml` (`repos.id: novaic-app`)
  - workflow_reference: `.github/workflows/ci.yml` job `compatibility-matrix`
  - check_detail: compatibility gate runs before frontend/tauri jobs

- component: `novaic-mcp-vmuse`
  - compatibility_source: `compatibility.yaml` (`repos.id: novaic-mcp-vmuse`)
  - workflow_reference: `.github/workflows/ci.yml` job `compatibility-matrix`
  - check_detail: gate is required in `ci-success` dependency chain

- component: `novaic-gateway`
  - compatibility_source: `compatibility.yaml` (`repos.id: novaic-gateway`)
  - workflow_reference: `.github/workflows/ci.yml` job `compatibility-matrix`
  - check_detail: broken compatibility matrix blocks merged CI result

- component: `openclaw-main`
  - compatibility_source: `compatibility.yaml` (`repos.id: openclaw-main`)
  - workflow_reference: `.github/workflows/ci.yml` job `compatibility-matrix`
  - check_detail: explicit repo entry audited by matrix guardrail
