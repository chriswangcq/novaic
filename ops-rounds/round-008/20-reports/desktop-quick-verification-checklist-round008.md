# Desktop Quick Verification Checklist - Round 008

## Operator Checklist (Non-Author)
- [ ] Run:
  - `cargo check --manifest-path "novaic-app/src-tauri/Cargo.toml"`
- [ ] Run replay:
  - `RUN_LABEL="<label>" OPERATOR_ID="<operator>" ROUND_DIR="/Users/wangchaoqun/novaic/ops-rounds/round-008" novaic-app/scripts/validate_fresh_profile.sh`
- [ ] Confirm summary:
  - `event_count>=10`
  - `error_timeout_count=0`
- [ ] Build bundle:
  - `novaic-app/scripts/build_desktop_evidence_bundle.sh "/Users/wangchaoqun/novaic/ops-rounds/round-008"`
- [ ] Verify bundle outputs:
  - `.tar.gz` archive exists
  - manifest exists and includes SHA256 line

## Stable Reference
- `ops-rounds/governance/desktop-operator-quick-checklist.md`
