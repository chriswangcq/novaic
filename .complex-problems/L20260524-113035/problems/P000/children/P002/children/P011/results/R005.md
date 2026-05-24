# P011 Result

## Summary

Verified the release-controller core unit test suite against the P011 acceptance criteria.

## Coverage Observed

- Branch mapping:
  - `test_main_maps_to_staging_deploy_plan`
  - `test_preview_namespace_uses_template_slug`
  - `test_release_branch_is_candidate_only_without_deploy`
- Immutable image refs:
  - `test_immutable_image_ref_validation`
  - `test_prod_promotion_requires_immutable_refs`
- State persistence:
  - `test_branch_heads_survive_store_reload`
  - `test_failed_run_survives_reload`
- Current/previous pointer rollover:
  - `test_current_previous_pointer_rollover`
  - `test_rollback_uses_previous_pointer`
- Dry-run planning and runner behavior:
  - `test_dry_run_runner_does_not_execute_commands`
  - dry-run trigger API test
- API behavior:
  - `test_health_and_rules`
  - `test_trigger_dry_run_persists_run_without_release_pointer`
  - `test_run_lookup_404`
  - `test_prod_promotion_rejects_mutable_ref`
  - `test_rollback_missing_previous_returns_400`
  - `test_status_reports_release_pointers_and_candidates`

## Verification

- `rg -n "^def test_" novaic-release-controller/tests`
  - Listed 25 release-controller tests.
- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: 25 tests.

## Notes

- CI wiring for these tests is intentionally deferred to P004.
