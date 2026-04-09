# 待检查文件总表（持疑核对 + 修文档）

> **自动生成**：`python3 docs/_scripts/regen_verification_registry.py`
> **规则**：每批 **8** 个并行 subagent；每人 **只负责一个文件**，对照代码核验，**有矛盾则改文档**（过程稿可加页眉说明「历史」）。
> **完成后**：把该路径写入 `docs/_scripts/verification_state.json`（`verified` 或 `partial` + 日期 + 备注），再重跑本脚本。
> **并行 8 名**：每人只改自己的 `.md`；**登记**一律用 `python3 docs/_scripts/merge_verification_state.py ...`（**flock**，可多进程并行调用）。**禁止**多人手写覆盖整份 `verification_state.json`。
> **partial**：仍出现在下表中，直至改为 `verified` / `skipped`（或删 JSON 项回到 pending）。
> **模板**：[`_scripts/SKEPTICAL_VERIFY_TEMPLATE.md`](_scripts/SKEPTICAL_VERIFY_TEMPLATE.md)
> **派单顺序**：按 **优先级** 排列（先 `HANDOVER` / `README` / `SYNC_CONTRACT` / checklist、`docs/` 根专章，再 `misc/`，**`design/` 最后**）。逻辑见 `regen_verification_registry.py` 中 `classify_work_priority`。

## 统计

- **仍待派出核对/修复**：160
- **批次数**（每批 8）：20

---

## 分批清单（按顺序派单）

### 第 1 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `HANDOVER.md` | 仓库根 · SSOT |
| 2 | `docs/DOCUMENT_AGGRESSIVE_STRATEGY.md` | docs 根 |
| 3 | `docs/entangled-architecture-upgrade-design-complete.md` | docs 根 |
| 4 | `docs/entangled-architecture-upgrade-plan.md` | docs 根 |
| 5 | `docs/entangled-cleanup-design.md` | docs 根 |
| 6 | `docs/entangled-load-test.md` | docs 根 |
| 7 | `docs/entangled-multi-worker-threat-model.md` | docs 根 |
| 8 | `docs/entangled-params-canonical.md` | docs 根 |

### 第 2 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/entangled-pk-conventions.md` | docs 根 |
| 2 | `docs/entangled-push-to-all-audit.md` | docs 根 |
| 3 | `docs/entangled-rust-single-writer-notes.md` | docs 根 |
| 4 | `docs/entangled-serviceization-design.md` | docs 根 |
| 5 | `docs/entangled-sync-protocol-v1.md` | docs 根 |
| 6 | `docs/entangled-tauri-capabilities-audit.md` | docs 根 |
| 7 | `docs/entity-design-audit.md` | docs 根 |
| 8 | `docs/im-tool-design.md` | docs 根 |

### 第 3 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/model-entity-refactor.md` | docs 根 |
| 2 | `docs/NEW_DOCUMENTATION_BLUEPRINT.md` | docs 根 |
| 3 | `docs/scope-driven-agent-lifecycle.md` | docs 根 |
| 4 | `docs/skills-domain-investigation-reports.md` | docs 根 |
| 5 | `docs/icons/README.md` | 其他 |
| 6 | `docs/misc/AGENTS_TAB_API_CONTRACT_VALIDATION.md` | L2/L3 misc |
| 7 | `docs/misc/AGENTS_TAB_CONFIG_GATEWAY_API_REPORT.md` | L2/L3 misc |
| 8 | `docs/misc/CURRENT_STATE_SURVEY_SUMMARY.md` | L2/L3 misc |

### 第 4 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/misc/FRONTEND_HOT_UPDATE_SUMMARY.md` | L2/L3 misc |
| 2 | `docs/misc/IOS_BLACK_SCREEN_ISSUE_REPORT.md` | L2/L3 misc |
| 3 | `docs/misc/MOBILE_DESKTOP_UNIFICATION_PROGRESS.md` | L2/L3 misc |
| 4 | `docs/misc/phase1-device-identity.md` | L2/L3 misc |
| 5 | `docs/misc/phase2-local-discovery.md` | L2/L3 misc |
| 6 | `docs/misc/phase3-p2p-remote.md` | L2/L3 misc |
| 7 | `docs/misc/phase4-multi-user.md` | L2/L3 misc |
| 8 | `docs/misc/README.md` | L2/L3 misc |

### 第 5 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/misc/RELAY_MIGRATION_8_TO_47.md` | L2/L3 misc |
| 2 | `docs/misc/RO_GATEWAY_CALL_RELATIONSHIP.md` | L2/L3 misc |
| 3 | `docs/misc/survey-2026/README.md` | L2/L3 misc |
| 4 | `docs/misc/TEST_RUN_REPORT.md` | L2/L3 misc |
| 5 | `docs/misc/VMCONTROL-TAURI-INTEGRATION-PLAN.md` | L2/L3 misc |
| 6 | `docs/misc/VPN_DEPLOYMENT_GUIDE.md` | L2/L3 misc |
| 7 | `docs/misc/设计文档.md` | L2/L3 misc |
| 8 | `docs/review/README.md` | 其他 |

### 第 6 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md` | L1 runbooks |
| 2 | `docs/runbooks/E2E_READINESS.md` | L1 runbooks |
| 3 | `docs/runbooks/HOT_UPDATE_DEPLOY_STEPS.md` | L1 runbooks |
| 4 | `docs/_archive/README.md` | 其他 |
| 5 | `docs/submodules/novaic-agent-runtime/README.md` | 子模块 README |
| 6 | `docs/submodules/novaic-app/README.md` | 子模块 README |
| 7 | `docs/submodules/novaic-contracts/README.md` | 子模块 README |
| 8 | `docs/submodules/novaic-control-plane/README.md` | 子模块 README |

### 第 7 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/submodules/novaic-gateway/README.md` | 子模块 README |
| 2 | `docs/submodules/novaic-runtime-orchestrator/README.md` | 子模块 README |
| 3 | `docs/submodules/novaic-shared-kernel/README.md` | 子模块 README |
| 4 | `docs/submodules/novaic-storage-b/README.md` | 子模块 README |
| 5 | `docs/submodules/novaic-tools-server/README.md` | 子模块 README |
| 6 | `docs/submodules/README.md` | 子模块 README |
| 7 | `docs/gateway-upgrade/00-design.md` | L3 gateway-upgrade |
| 8 | `docs/gateway-upgrade/01-chat-router.md` | L3 gateway-upgrade |

### 第 8 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/gateway-upgrade/02-monitoring-router.md` | L3 gateway-upgrade |
| 2 | `docs/gateway-upgrade/03-files-proxy-router.md` | L3 gateway-upgrade |
| 3 | `docs/gateway-upgrade/04-tasks-and-system-router.md` | L3 gateway-upgrade |
| 4 | `docs/gateway-upgrade/05-main-gateway-slim.md` | L3 gateway-upgrade |
| 5 | `docs/gateway-upgrade/06-schema-slim.md` | L3 gateway-upgrade |
| 6 | `docs/gateway-upgrade/07-repository-cleanup.md` | L3 gateway-upgrade |
| 7 | `docs/gateway-upgrade/08-docstrings-deadcode.md` | L3 gateway-upgrade |
| 8 | `docs/gateway-upgrade/README.md` | L3 gateway-upgrade |

### 第 9 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/ota/OTA_CHANGES_4_AGENT_REVIEW.md` | L3 ota |
| 2 | `docs/ota/OTA_FLOW_CAPABILITY_SWITCH.md` | L3 ota |
| 3 | `docs/ota/OTA_INVOKE_4_AGENT_REPORT.md` | L3 ota |
| 4 | `docs/ota/OTA_INVOKE_ROOT_CAUSE_ANALYSIS.md` | L3 ota |
| 5 | `docs/ota/OTA_PLAN_REVIEW_SUMMARY.md` | L3 ota |
| 6 | `docs/ota/OTA_RE_ENABLE_FRONTEND_REVIEW.md` | L3 ota |
| 7 | `docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md` | L3 ota |
| 8 | `docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_REVIEW.md` | L3 ota |

### 第 10 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md` | L3 ota |
| 2 | `docs/ota/OTA_V2_FRONTEND_3_AGENT_SUMMARY.md` | L3 ota |
| 3 | `docs/ota/OTA_V2_FRONTEND_REVIEW.md` | L3 ota |
| 4 | `docs/p2p/P2P-FIXES-2026-03-11.md` | L3 p2p |
| 5 | `docs/p2p/P2P-PHASE4-CODE-REVIEW-REPORT.md` | L3 p2p |
| 6 | `docs/p2p/P2P-REVIEW-CONTEXT.md` | L3 p2p |
| 7 | `docs/p2p/P2P-SUBAGENT-FIX-LIST.md` | L3 p2p |
| 8 | `docs/p2p/P2P_ARCHITECTURE_SURVEY_ROUND1.md` | L3 p2p |

### 第 11 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/p2p/P2P_CRITICAL_REVIEW_ROUND2.md` | L3 p2p |
| 2 | `docs/p2p/P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md` | L3 p2p |
| 3 | `docs/p2p/P2P_REFACTOR_PROPOSAL_A.md` | L3 p2p |
| 4 | `docs/p2p/P2P_REFACTOR_SUMMARY_ABC.md` | L3 p2p |
| 5 | `docs/p2p/P2P_RELAY_RACE_ANALYSIS.md` | L3 p2p |
| 6 | `docs/p2p/P2P_SERVER_ISSUE_REPORT.md` | L3 p2p |
| 7 | `docs/device/DEVICE_AGENT_DECOUPLE_DATAFLOW_RESEARCH_ROUND2.md` | L3 device |
| 8 | `docs/device/DEVICE_DATAFLOW_RESEARCH_ROUND1.md` | L3 device |

### 第 12 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/device/DEVICE_FLOATING_PANEL_DEVICEMODE_RESEARCH_ROUND3.md` | L3 device |
| 2 | `docs/device/DEVICE_ITERATION_REVIEW_CONTEXT.md` | L3 device |
| 3 | `docs/device/DEVICE_MANAGEMENT_DATA_STRUCTURE_REPORT.md` | L3 device |
| 4 | `docs/device/DEVICE_MANAGER_FLOATING_PANEL_DATA_SOURCE_RESEARCH.md` | L3 device |
| 5 | `docs/device/DEVICE_PC_CLIENT_ONLINE_PLAN.md` | L3 device |
| 6 | `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R2.md` | L3 device |
| 7 | `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3.md` | L3 device |
| 8 | `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_AGENT_DRAWER.md` | L3 device |

### 第 13 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_SECURITY.md` | L3 device |
| 2 | `docs/device/DEVICE_SETUP_START_PC_CLIENT_ID_REVIEW.md` | L3 device |
| 3 | `docs/device/DEVICE_STATUS_RACE_MULTI_PC_RESEARCH_ROUND3.md` | L3 device |
| 4 | `docs/device/DEVICE_STATUS_STORE_POLLING_RESEARCH_ROUND2.md` | L3 device |
| 5 | `docs/device/DEVICE_SWITCH_FLOW_ANALYSIS.md` | L3 device |
| 6 | `docs/device/PC_CLIENT_HANDLE_DEVICE_MESSAGE_REVIEW.md` | L3 device |
| 7 | `docs/device/README.md` | L3 device |
| 8 | `docs/research/AGENTS_TAB_CONFIG_8_AGENT_ANALYSIS_SUMMARY.md` | L3 research |

### 第 14 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/research/AGENTS_TAB_CONFIG_AGENT_SELECTION_ANALYSIS.md` | L3 research |
| 2 | `docs/research/AGENTS_TAB_CONFIG_ANALYSIS.md` | L3 research |
| 3 | `docs/research/AGENTS_TAB_CONFIG_API_ANALYSIS.md` | L3 research |
| 4 | `docs/research/BACKEND_STARTUP_SLOWNESS_ANALYSIS.md` | L3 research |
| 5 | `docs/research/COMMANDS_ANALYSIS.md` | L3 research |
| 6 | `docs/research/DB-LOG-ANALYSIS-subagent.md` | L3 research |
| 7 | `docs/research/GATEWAY_VS_TAURI_RESPONSIBILITY_BOUNDARY_RESEARCH_ROUND3.md` | L3 research |
| 8 | `docs/research/QUEUE_SERVER_DISCONNECTED_ROOT_CAUSE_ANALYSIS.md` | L3 research |

### 第 15 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/research/README.md` | L3 research |
| 2 | `docs/research/RELAY_IPV6_FIX_ANALYSIS.md` | L3 research |
| 3 | `docs/research/RESEARCH_APP_INSTANCE.md` | L3 research |
| 4 | `docs/research/RESEARCH_APP_INSTANCE_MYDEVICES_LINKAGE.md` | L3 research |
| 5 | `docs/research/RESEARCH_APP_INSTANCE_OVERVIEW.md` | L3 research |
| 6 | `docs/research/RESEARCH_APP_INSTANCE_SYNC_AND_FAILURE_SCENARIOS.md` | L3 research |
| 7 | `docs/research/RESEARCH_CONNECT_RELAY_FLOW.md` | L3 research |
| 8 | `docs/research/RESEARCH_DEVICE_BACKEND.md` | L3 research |

### 第 16 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/research/RESEARCH_DEVICE_FRONTEND.md` | L3 research |
| 2 | `docs/research/RESEARCH_P2P_RELAY_TUNNEL_DETAILS.md` | L3 research |
| 3 | `docs/research/TOOL_ERRORS_ANALYSIS.md` | L3 research |
| 4 | `docs/research/TOOL_ERRORS_TROUBLESHOOTING.md` | L3 research |
| 5 | `docs/research/UNIFIED_CURRENT_STATE_AND_RESEARCH.md` | L3 research |
| 6 | `docs/design/CHATS_AGENTS_TABS_DESIGN.md` | L3 design |
| 7 | `docs/design/COMMANDS_SPLIT_DESIGN.md` | L3 design |
| 8 | `docs/design/DESIGN-ELIMINATE-RUNTIME-ROOT-PLAN.md` | L3 design |

### 第 17 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/design/DESIGN-GATEWAY-FILTERED-TOOLS-TASKS.md` | L3 design |
| 2 | `docs/design/DESIGN-gateway-no-forward.md` | L3 design |
| 3 | `docs/design/DESIGN-GATEWAY-RETURNS-FILTERED-TOOLS.md` | L3 design |
| 4 | `docs/design/DESIGN-LOCAL-RELAY.md` | L3 design |
| 5 | `docs/design/DESIGN-novaic-quic-service-IMPLEMENTATION.md` | L3 design |
| 6 | `docs/design/DESIGN-novaic-quic-service.md` | L3 design |
| 7 | `docs/design/DESIGN-P2P-ORCHESTRATOR-PROPOSAL-C.md` | L3 design |
| 8 | `docs/design/DESIGN-P2P-REGISTRATION-DISCOVERY.md` | L3 design |

### 第 18 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/design/DESIGN-P2P-UNIFIED.md` | L3 design |
| 2 | `docs/design/DESIGN-subagent-agent-routes.md` | L3 design |
| 3 | `docs/design/DESIGN-subagent-centric-gateway-migration.md` | L3 design |
| 4 | `docs/design/DESIGN-subagent-wake-message-gateway-db.md` | L3 design |
| 5 | `docs/design/DESIGN-vm-tools-subagent-centric.md` | L3 design |
| 6 | `docs/design/DEVICE_SUBJECT_DESIGN.md` | L3 design |
| 7 | `docs/design/EXECUTION_LOG_SUBAGENT_CAPSULES_DESIGN.md` | L3 design |
| 8 | `docs/design/HOT_UPDATE_EXECUTION_PLAN.md` | L3 design |

### 第 19 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/design/IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md` | L3 design |
| 2 | `docs/design/IMPLEMENTATION-PLAN-tools-server-remove-runtime-ro.md` | L3 design |
| 3 | `docs/design/LAYOUT_CONTAINER_REFACTORING_DESIGN.md` | L3 design |
| 4 | `docs/design/MOBILE_FILE_LIST_REMOVAL_PLAN.md` | L3 design |
| 5 | `docs/design/MULTI_USER_DESIGN.md` | L3 design |
| 6 | `docs/design/OPTIMIZATION_PLAN.md` | L3 design |
| 7 | `docs/design/PARALLEL_SERVICE_STARTUP_PROPOSAL.md` | L3 design |
| 8 | `docs/design/RESPONSIVE_LAYOUT_DESIGN_V2.md` | L3 design |

### 第 20 批（8 个）

| # | 路径 | 层级 |
|---|------|------|
| 1 | `docs/design/SECURE_STORAGE_DESIGN.md` | L3 design |
| 2 | `docs/design/SSE_USER_LEVEL_MIGRATION.md` | L3 design |
| 3 | `docs/design/SUBUSER_MAINDESK_MOVE_TO_COLUMN3_DESIGN.md` | L3 design |
| 4 | `docs/design/SYSTEM_DESIGN.md` | L3 design |
| 5 | `docs/design/TAURI2_MOBILE_MODULARIZATION_PLAN.md` | L3 design |
| 6 | `docs/design/UNIFIED_DESIGN_TASK_ASSIGNMENT.md` | L3 design |
| 7 | `docs/design/UNIFIED_LAYOUT_AND_EXECUTION_LOG_DESIGN.md` | L3 design |
| 8 | `docs/design/VM_STATUS_REPORT_STOPPED_DEVICES_PLAN.md` | L3 design |

---

## 仅路径列表（复制用）

```text
HANDOVER.md
docs/DOCUMENT_AGGRESSIVE_STRATEGY.md
docs/entangled-architecture-upgrade-design-complete.md
docs/entangled-architecture-upgrade-plan.md
docs/entangled-cleanup-design.md
docs/entangled-load-test.md
docs/entangled-multi-worker-threat-model.md
docs/entangled-params-canonical.md
docs/entangled-pk-conventions.md
docs/entangled-push-to-all-audit.md
docs/entangled-rust-single-writer-notes.md
docs/entangled-serviceization-design.md
docs/entangled-sync-protocol-v1.md
docs/entangled-tauri-capabilities-audit.md
docs/entity-design-audit.md
docs/im-tool-design.md
docs/model-entity-refactor.md
docs/NEW_DOCUMENTATION_BLUEPRINT.md
docs/scope-driven-agent-lifecycle.md
docs/skills-domain-investigation-reports.md
docs/icons/README.md
docs/misc/AGENTS_TAB_API_CONTRACT_VALIDATION.md
docs/misc/AGENTS_TAB_CONFIG_GATEWAY_API_REPORT.md
docs/misc/CURRENT_STATE_SURVEY_SUMMARY.md
docs/misc/FRONTEND_HOT_UPDATE_SUMMARY.md
docs/misc/IOS_BLACK_SCREEN_ISSUE_REPORT.md
docs/misc/MOBILE_DESKTOP_UNIFICATION_PROGRESS.md
docs/misc/phase1-device-identity.md
docs/misc/phase2-local-discovery.md
docs/misc/phase3-p2p-remote.md
docs/misc/phase4-multi-user.md
docs/misc/README.md
docs/misc/RELAY_MIGRATION_8_TO_47.md
docs/misc/RO_GATEWAY_CALL_RELATIONSHIP.md
docs/misc/survey-2026/README.md
docs/misc/TEST_RUN_REPORT.md
docs/misc/VMCONTROL-TAURI-INTEGRATION-PLAN.md
docs/misc/VPN_DEPLOYMENT_GUIDE.md
docs/misc/设计文档.md
docs/review/README.md
docs/runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md
docs/runbooks/E2E_READINESS.md
docs/runbooks/HOT_UPDATE_DEPLOY_STEPS.md
docs/_archive/README.md
docs/submodules/novaic-agent-runtime/README.md
docs/submodules/novaic-app/README.md
docs/submodules/novaic-contracts/README.md
docs/submodules/novaic-control-plane/README.md
docs/submodules/novaic-gateway/README.md
docs/submodules/novaic-runtime-orchestrator/README.md
docs/submodules/novaic-shared-kernel/README.md
docs/submodules/novaic-storage-b/README.md
docs/submodules/novaic-tools-server/README.md
docs/submodules/README.md
docs/gateway-upgrade/00-design.md
docs/gateway-upgrade/01-chat-router.md
docs/gateway-upgrade/02-monitoring-router.md
docs/gateway-upgrade/03-files-proxy-router.md
docs/gateway-upgrade/04-tasks-and-system-router.md
docs/gateway-upgrade/05-main-gateway-slim.md
docs/gateway-upgrade/06-schema-slim.md
docs/gateway-upgrade/07-repository-cleanup.md
docs/gateway-upgrade/08-docstrings-deadcode.md
docs/gateway-upgrade/README.md
docs/ota/OTA_CHANGES_4_AGENT_REVIEW.md
docs/ota/OTA_FLOW_CAPABILITY_SWITCH.md
docs/ota/OTA_INVOKE_4_AGENT_REPORT.md
docs/ota/OTA_INVOKE_ROOT_CAUSE_ANALYSIS.md
docs/ota/OTA_PLAN_REVIEW_SUMMARY.md
docs/ota/OTA_RE_ENABLE_FRONTEND_REVIEW.md
docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md
docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_REVIEW.md
docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md
docs/ota/OTA_V2_FRONTEND_3_AGENT_SUMMARY.md
docs/ota/OTA_V2_FRONTEND_REVIEW.md
docs/p2p/P2P-FIXES-2026-03-11.md
docs/p2p/P2P-PHASE4-CODE-REVIEW-REPORT.md
docs/p2p/P2P-REVIEW-CONTEXT.md
docs/p2p/P2P-SUBAGENT-FIX-LIST.md
docs/p2p/P2P_ARCHITECTURE_SURVEY_ROUND1.md
docs/p2p/P2P_CRITICAL_REVIEW_ROUND2.md
docs/p2p/P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md
docs/p2p/P2P_REFACTOR_PROPOSAL_A.md
docs/p2p/P2P_REFACTOR_SUMMARY_ABC.md
docs/p2p/P2P_RELAY_RACE_ANALYSIS.md
docs/p2p/P2P_SERVER_ISSUE_REPORT.md
docs/device/DEVICE_AGENT_DECOUPLE_DATAFLOW_RESEARCH_ROUND2.md
docs/device/DEVICE_DATAFLOW_RESEARCH_ROUND1.md
docs/device/DEVICE_FLOATING_PANEL_DEVICEMODE_RESEARCH_ROUND3.md
docs/device/DEVICE_ITERATION_REVIEW_CONTEXT.md
docs/device/DEVICE_MANAGEMENT_DATA_STRUCTURE_REPORT.md
docs/device/DEVICE_MANAGER_FLOATING_PANEL_DATA_SOURCE_RESEARCH.md
docs/device/DEVICE_PC_CLIENT_ONLINE_PLAN.md
docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R2.md
docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3.md
docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_AGENT_DRAWER.md
docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_SECURITY.md
docs/device/DEVICE_SETUP_START_PC_CLIENT_ID_REVIEW.md
docs/device/DEVICE_STATUS_RACE_MULTI_PC_RESEARCH_ROUND3.md
docs/device/DEVICE_STATUS_STORE_POLLING_RESEARCH_ROUND2.md
docs/device/DEVICE_SWITCH_FLOW_ANALYSIS.md
docs/device/PC_CLIENT_HANDLE_DEVICE_MESSAGE_REVIEW.md
docs/device/README.md
docs/research/AGENTS_TAB_CONFIG_8_AGENT_ANALYSIS_SUMMARY.md
docs/research/AGENTS_TAB_CONFIG_AGENT_SELECTION_ANALYSIS.md
docs/research/AGENTS_TAB_CONFIG_ANALYSIS.md
docs/research/AGENTS_TAB_CONFIG_API_ANALYSIS.md
docs/research/BACKEND_STARTUP_SLOWNESS_ANALYSIS.md
docs/research/COMMANDS_ANALYSIS.md
docs/research/DB-LOG-ANALYSIS-subagent.md
docs/research/GATEWAY_VS_TAURI_RESPONSIBILITY_BOUNDARY_RESEARCH_ROUND3.md
docs/research/QUEUE_SERVER_DISCONNECTED_ROOT_CAUSE_ANALYSIS.md
docs/research/README.md
docs/research/RELAY_IPV6_FIX_ANALYSIS.md
docs/research/RESEARCH_APP_INSTANCE.md
docs/research/RESEARCH_APP_INSTANCE_MYDEVICES_LINKAGE.md
docs/research/RESEARCH_APP_INSTANCE_OVERVIEW.md
docs/research/RESEARCH_APP_INSTANCE_SYNC_AND_FAILURE_SCENARIOS.md
docs/research/RESEARCH_CONNECT_RELAY_FLOW.md
docs/research/RESEARCH_DEVICE_BACKEND.md
docs/research/RESEARCH_DEVICE_FRONTEND.md
docs/research/RESEARCH_P2P_RELAY_TUNNEL_DETAILS.md
docs/research/TOOL_ERRORS_ANALYSIS.md
docs/research/TOOL_ERRORS_TROUBLESHOOTING.md
docs/research/UNIFIED_CURRENT_STATE_AND_RESEARCH.md
docs/design/CHATS_AGENTS_TABS_DESIGN.md
docs/design/COMMANDS_SPLIT_DESIGN.md
docs/design/DESIGN-ELIMINATE-RUNTIME-ROOT-PLAN.md
docs/design/DESIGN-GATEWAY-FILTERED-TOOLS-TASKS.md
docs/design/DESIGN-gateway-no-forward.md
docs/design/DESIGN-GATEWAY-RETURNS-FILTERED-TOOLS.md
docs/design/DESIGN-LOCAL-RELAY.md
docs/design/DESIGN-novaic-quic-service-IMPLEMENTATION.md
docs/design/DESIGN-novaic-quic-service.md
docs/design/DESIGN-P2P-ORCHESTRATOR-PROPOSAL-C.md
docs/design/DESIGN-P2P-REGISTRATION-DISCOVERY.md
docs/design/DESIGN-P2P-UNIFIED.md
docs/design/DESIGN-subagent-agent-routes.md
docs/design/DESIGN-subagent-centric-gateway-migration.md
docs/design/DESIGN-subagent-wake-message-gateway-db.md
docs/design/DESIGN-vm-tools-subagent-centric.md
docs/design/DEVICE_SUBJECT_DESIGN.md
docs/design/EXECUTION_LOG_SUBAGENT_CAPSULES_DESIGN.md
docs/design/HOT_UPDATE_EXECUTION_PLAN.md
docs/design/IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md
docs/design/IMPLEMENTATION-PLAN-tools-server-remove-runtime-ro.md
docs/design/LAYOUT_CONTAINER_REFACTORING_DESIGN.md
docs/design/MOBILE_FILE_LIST_REMOVAL_PLAN.md
docs/design/MULTI_USER_DESIGN.md
docs/design/OPTIMIZATION_PLAN.md
docs/design/PARALLEL_SERVICE_STARTUP_PROPOSAL.md
docs/design/RESPONSIVE_LAYOUT_DESIGN_V2.md
docs/design/SECURE_STORAGE_DESIGN.md
docs/design/SSE_USER_LEVEL_MIGRATION.md
docs/design/SUBUSER_MAINDESK_MOVE_TO_COLUMN3_DESIGN.md
docs/design/SYSTEM_DESIGN.md
docs/design/TAURI2_MOBILE_MODULARIZATION_PLAN.md
docs/design/UNIFIED_DESIGN_TASK_ASSIGNMENT.md
docs/design/UNIFIED_LAYOUT_AND_EXECUTION_LOG_DESIGN.md
docs/design/VM_STATUS_REPORT_STOPPED_DEVICES_PLAN.md
```

