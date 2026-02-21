# Round 001 Report - Desktop Team

## Task 1 - Desktop extraction boundary artifact
- task: Create `split-plan/desktop-boundary.md` for app repo extraction paths and backend coupling points.
- evidence:
  - command:
    - `test -f "novaic-control-plane/rounds/round-001/split-plan/desktop-boundary.md"`
  - summary:
    - PASS; artifact exists and documents extraction scope, backend coupling points, and split guardrails.
  - artifact_path:
    - `novaic-control-plane/rounds/round-001/split-plan/desktop-boundary.md`
- status: DONE

## Task 2 - Desktop runtime dependency map artifact
- task: Create `split-plan/desktop-runtime-dependency-map.md` for process orchestration and endpoint dependencies.
- evidence:
  - command:
    - `test -f "novaic-control-plane/rounds/round-001/split-plan/desktop-runtime-dependency-map.md"`
  - summary:
    - PASS; artifact exists and captures service ports, endpoint families, SSE/VNC dependencies, and split-time risks.
  - artifact_path:
    - `novaic-control-plane/rounds/round-001/split-plan/desktop-runtime-dependency-map.md`
- status: DONE

## Task 3 - Package/startup replay operability baseline
- task: Run package/startup replay checks and capture baseline evidence before split.
- evidence:
  - command:
    - `npm run build` (working dir: `novaic-app`)
  - summary:
    - PASS; TypeScript + Vite production build completed successfully.
  - artifact_path:
    - `novaic-app/dist/`
- evidence:
  - command:
    - `test -d "/Users/wangchaoqun/novaic/novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app" && test -f "/Users/wangchaoqun/novaic/novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg" && shasum -a 256 "/Users/wangchaoqun/novaic/novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg"`
  - summary:
    - PASS; desktop package artifacts exist (`.app` + `.dmg`) and checksum generated.
  - artifact_path:
    - `novaic-app/src-tauri/target/release/bundle/macos/NovAIC.app`
    - `novaic-app/src-tauri/target/release/bundle/dmg/NovAIC_0.3.0_aarch64.dmg`
- evidence:
  - command:
    - `ROUND_DIR="/Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-001" RUN_LABEL="round001-baseline" OPERATOR_ID="team-desktop" WAIT_SECONDS=20 bash "/Users/wangchaoqun/novaic/novaic-app/scripts/validate_fresh_profile.sh"`
  - summary:
    - PASS; fresh-profile startup replay completed with `error_timeout_count=0` and all core startup stages recorded.
  - artifact_path:
    - `novaic-control-plane/rounds/round-001/20-reports/desktop-evidence/fresh-profile-round001-baseline-summary.txt`
    - `novaic-control-plane/rounds/round-001/20-reports/desktop-evidence/fresh-profile-round001-baseline-startup-diagnostics.jsonl`
    - `novaic-control-plane/rounds/round-001/20-reports/desktop-evidence/fresh-profile-round001-baseline-startup.log`
    - `novaic-control-plane/rounds/round-001/20-reports/desktop-evidence/fresh-profile-round001-baseline-metadata.txt`
- status: DONE

## Team status
- status: DONE
- blocker: none
