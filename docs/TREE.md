# docs/ 树形索引（自动生成 + DFS 说明）

> **物理结构**：下列 `docs/` 目录树由脚本扫描生成，反映仓库内真实路径。
> **重生成**：在仓库根执行 `python3 docs/_scripts/generate_docs_tree.py`。

---

## 1. DFS 阅读顺序（从总入口到最底层）

逻辑层级与 [`NOVAIC_CANONICAL_GUIDE.md`](NOVAIC_CANONICAL_GUIDE.md) 一致：

```
L0  入口
 ├─ NOVAIC_CANONICAL_GUIDE.md
 └─ README.md
L1  现行总览（与代码/运维对齐）
 ├─ backend-architecture.md
 ├─ architecture-verification-2026-04.md
 ├─ agent-handoff-context.md
 └─ ../HANDOVER.md（仓库根）
L2  子系统专章（深入单域）
 ├─ cortex-architecture.md / context-assembly-dfs-step-tree.md / scope-driven-agent-lifecycle.md
 ├─ SYNC_CONTRACT.md / entangled-sync-protocol-v1.md / sync-contract-execution-checklist.md
 └─ …（见 Canonical §10 表）
L3  过程稿（最底层叶子：按主题目录展开）
 ├─ design/          — 方案与迁移草案
 ├─ research/       — 调研与根因
 ├─ device/         — 设备域回合
 ├─ gateway-upgrade/ — Gateway 拆分过程
 ├─ ota/ / p2p/     — 专题记录
 ├─ misc/           — 联调运维
 └─ …（见下方物理树）
```

**DFS 到最底层**：在某一 L3 目录内，按文件名或时间自行深读；**不要求**读完所有 `.md`，以页眉「过程稿/调研」为准。

---

## 2. `docs/` 物理目录树（相对 `docs/`）

```
docs/
├── _archive/
│   ├── MANIFEST-2026-04-09-pre-rebuild.txt
│   └── README.md
├── _legacy/
│   └── README.md
├── _scripts/
│   ├── emit_verify_batches.py
│   ├── generate_docs_tree.py
│   ├── merge_verification_state.py
│   ├── regen_document_inventory.py
│   ├── regen_verification_registry.py
│   ├── SKEPTICAL_VERIFY_TEMPLATE.md
│   ├── snapshot_docs_manifest.sh
│   └── verification_state.json
├── _verification/
│   ├── batch_001_README.txt
│   ├── batch_002_README.txt
│   ├── batch_003_README.txt
│   ├── batch_004_README.txt
│   ├── batch_005_README.txt
│   ├── batch_006_README.txt
│   ├── batch_007_README.txt
│   ├── batch_008_README.txt
│   ├── batch_009_README.txt
│   ├── batch_010_README.txt
│   ├── batch_011_README.txt
│   ├── batch_012_README.txt
│   ├── batch_013_README.txt
│   ├── batch_014_README.txt
│   ├── batch_015_README.txt
│   ├── batch_016_README.txt
│   ├── batch_017_README.txt
│   ├── batch_018_README.txt
│   ├── batch_019_README.txt
│   ├── batch_020_README.txt
│   ├── batch_021_README.txt
│   ├── batch_022_README.txt
│   ├── batch_023_README.txt
│   └── verify_batches.csv
├── agent-approve-points/
│   ├── 01-novaic-architecture.md
│   ├── 02-openclaw-architecture.md
│   ├── 03-optimization-points.md
│   └── README.md
├── design/
│   ├── CHATS_AGENTS_TABS_DESIGN.md
│   ├── COMMANDS_SPLIT_DESIGN.md
│   ├── DESIGN-ELIMINATE-RUNTIME-FROM-GATEWAY-TOOLS-SERVER.md
│   ├── DESIGN-ELIMINATE-RUNTIME-ROOT-PLAN.md
│   ├── DESIGN-GATEWAY-FILTERED-TOOLS-TASKS.md
│   ├── DESIGN-gateway-no-forward.md
│   ├── DESIGN-GATEWAY-RETURNS-FILTERED-TOOLS.md
│   ├── DESIGN-LOCAL-RELAY.md
│   ├── DESIGN-novaic-quic-service-IMPLEMENTATION.md
│   ├── DESIGN-novaic-quic-service.md
│   ├── DESIGN-P2P-ORCHESTRATOR-PROPOSAL-C.md
│   ├── DESIGN-P2P-REGISTRATION-DISCOVERY.md
│   ├── DESIGN-P2P-UNIFIED.md
│   ├── DESIGN-subagent-agent-routes.md
│   ├── DESIGN-subagent-centric-gateway-migration.md
│   ├── DESIGN-subagent-wake-message-gateway-db.md
│   ├── DESIGN-vm-tools-subagent-centric.md
│   ├── DEVICE_SUBJECT_DESIGN.md
│   ├── EXECUTION_LOG_SUBAGENT_CAPSULES_DESIGN.md
│   ├── HOT_UPDATE_EXECUTION_PLAN.md
│   ├── IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md
│   ├── IMPLEMENTATION-PLAN-tools-server-remove-runtime-ro.md
│   ├── LAYOUT_CONTAINER_REFACTORING_DESIGN.md
│   ├── MOBILE_FILE_LIST_REMOVAL_PLAN.md
│   ├── MULTI_USER_DESIGN.md
│   ├── OPTIMIZATION_PLAN.md
│   ├── PARALLEL_SERVICE_STARTUP_PROPOSAL.md
│   ├── RESPONSIVE_LAYOUT_DESIGN_V2.md
│   ├── SECURE_STORAGE_DESIGN.md
│   ├── SSE_USER_LEVEL_MIGRATION.md
│   ├── SUBUSER_MAINDESK_MOVE_TO_COLUMN3_DESIGN.md
│   ├── SYSTEM_DESIGN.md
│   ├── TAURI2_MOBILE_MODULARIZATION_PLAN.md
│   ├── UNIFIED_DESIGN_TASK_ASSIGNMENT.md
│   ├── UNIFIED_LAYOUT_AND_EXECUTION_LOG_DESIGN.md
│   └── VM_STATUS_REPORT_STOPPED_DEVICES_PLAN.md
├── device/
│   ├── DEVICE_AGENT_DECOUPLE_DATAFLOW_RESEARCH_ROUND2.md
│   ├── DEVICE_DATAFLOW_RESEARCH_ROUND1.md
│   ├── DEVICE_FLOATING_PANEL_DEVICEMODE_RESEARCH_ROUND3.md
│   ├── DEVICE_ITERATION_REVIEW_CONTEXT.md
│   ├── DEVICE_MANAGEMENT_DATA_STRUCTURE_REPORT.md
│   ├── DEVICE_MANAGER_FLOATING_PANEL_DATA_SOURCE_RESEARCH.md
│   ├── DEVICE_PC_CLIENT_ONLINE_PLAN.md
│   ├── DEVICE_PC_CLIENT_ONLINE_REVIEW_R2.md
│   ├── DEVICE_PC_CLIENT_ONLINE_REVIEW_R3.md
│   ├── DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_AGENT_DRAWER.md
│   ├── DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_SECURITY.md
│   ├── DEVICE_SETUP_START_PC_CLIENT_ID_REVIEW.md
│   ├── DEVICE_STATUS_RACE_MULTI_PC_RESEARCH_ROUND3.md
│   ├── DEVICE_STATUS_STORE_POLLING_RESEARCH_ROUND2.md
│   ├── DEVICE_SWITCH_FLOW_ANALYSIS.md
│   ├── PC_CLIENT_HANDLE_DEVICE_MESSAGE_REVIEW.md
│   └── README.md
├── gateway-upgrade/
│   ├── 00-design.md
│   ├── 01-chat-router.md
│   ├── 02-monitoring-router.md
│   ├── 03-files-proxy-router.md
│   ├── 04-tasks-and-system-router.md
│   ├── 05-main-gateway-slim.md
│   ├── 06-schema-slim.md
│   ├── 07-repository-cleanup.md
│   ├── 08-docstrings-deadcode.md
│   └── README.md
├── icons/
│   └── README.md
├── misc/
│   ├── survey-2026/
│   │   └── README.md
│   ├── AGENTS_TAB_API_CONTRACT_VALIDATION.md
│   ├── AGENTS_TAB_CONFIG_GATEWAY_API_REPORT.md
│   ├── CLIENT_DB_ARCHITECTURE.md
│   ├── CROSS_PLATFORM_ARCHITECTURE.md
│   ├── CURRENT_STATE_SURVEY_SUMMARY.md
│   ├── FRONTEND_HOT_UPDATE_SUMMARY.md
│   ├── HMR_DEV_REPORT.json
│   ├── IOS_BLACK_SCREEN_ISSUE_REPORT.md
│   ├── MOBILE_DESKTOP_UNIFICATION_PROGRESS.md
│   ├── MOBILE_HOT_UPDATE_LIMITS_REPORT.json
│   ├── phase1-device-identity.md
│   ├── phase2-local-discovery.md
│   ├── phase3-p2p-remote.md
│   ├── phase4-multi-user.md
│   ├── README.md
│   ├── RELAY_MIGRATION_8_TO_47.md
│   ├── REMOTE_URL_HOT_UPDATE_REPORT.json
│   ├── RO_GATEWAY_CALL_RELATIONSHIP.md
│   ├── TAURI2_OTA_UPDATER_REPORT.json
│   ├── TEST_RUN_REPORT.md
│   ├── VMCONTROL-TAURI-INTEGRATION-PLAN.md
│   └── 设计文档.md
├── ota/
│   ├── OTA_CHANGES_4_AGENT_REVIEW.md
│   ├── OTA_FLOW_CAPABILITY_SWITCH.md
│   ├── OTA_INVOKE_4_AGENT_REPORT.md
│   ├── OTA_INVOKE_ROOT_CAUSE_ANALYSIS.md
│   ├── OTA_PLAN_REVIEW_SUMMARY.md
│   ├── OTA_RE_ENABLE_FRONTEND_REVIEW.md
│   ├── OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md
│   ├── OTA_RE_ENABLE_IMPLEMENTATION_PLAN_REVIEW.md
│   ├── OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md
│   ├── OTA_V2_FRONTEND_3_AGENT_SUMMARY.md
│   └── OTA_V2_FRONTEND_REVIEW.md
├── p2p/
│   ├── P2P-FIXES-2026-03-11.md
│   ├── P2P-PHASE4-CODE-REVIEW-REPORT.md
│   ├── P2P-REVIEW-CONTEXT.md
│   ├── P2P-SUBAGENT-FIX-LIST.md
│   ├── P2P_ARCHITECTURE_SURVEY_ROUND1.md
│   ├── P2P_CRITICAL_REVIEW_ROUND2.md
│   ├── P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md
│   ├── P2P_REFACTOR_PROPOSAL_A.md
│   ├── P2P_REFACTOR_SUMMARY_ABC.md
│   ├── P2P_RELAY_RACE_ANALYSIS.md
│   └── P2P_SERVER_ISSUE_REPORT.md
├── research/
│   ├── AGENTS_TAB_CONFIG_8_AGENT_ANALYSIS_SUMMARY.md
│   ├── AGENTS_TAB_CONFIG_AGENT_SELECTION_ANALYSIS.md
│   ├── AGENTS_TAB_CONFIG_ANALYSIS.md
│   ├── AGENTS_TAB_CONFIG_API_ANALYSIS.md
│   ├── BACKEND_STARTUP_SLOWNESS_ANALYSIS.md
│   ├── COMMANDS_ANALYSIS.md
│   ├── DB-LOG-ANALYSIS-subagent.md
│   ├── GATEWAY_VS_TAURI_RESPONSIBILITY_BOUNDARY_RESEARCH_ROUND3.md
│   ├── QUEUE_SERVER_DISCONNECTED_ROOT_CAUSE_ANALYSIS.md
│   ├── README.md
│   ├── RELAY_IPV6_FIX_ANALYSIS.md
│   ├── RESEARCH_APP_INSTANCE.md
│   ├── RESEARCH_APP_INSTANCE_MYDEVICES_LINKAGE.md
│   ├── RESEARCH_APP_INSTANCE_OVERVIEW.md
│   ├── RESEARCH_APP_INSTANCE_SYNC_AND_FAILURE_SCENARIOS.md
│   ├── RESEARCH_CONNECT_RELAY_FLOW.md
│   ├── RESEARCH_DEVICE_BACKEND.md
│   ├── RESEARCH_DEVICE_FRONTEND.md
│   ├── RESEARCH_P2P_RELAY_TUNNEL_DETAILS.md
│   ├── TOOL_ERRORS_ANALYSIS.md
│   ├── TOOL_ERRORS_TROUBLESHOOTING.md
│   └── UNIFIED_CURRENT_STATE_AND_RESEARCH.md
├── review/
│   └── README.md
├── runbooks/
│   ├── ARCHITECTURE-SERVICES-AND-HANDLERS.md
│   ├── E2E_READINESS.md
│   ├── HOT_UPDATE_DEPLOY_STEPS.md
│   ├── README.md
│   └── VPN_DEPLOYMENT_GUIDE.md
├── submodules/
│   ├── novaic-agent-runtime/
│   │   └── README.md
│   ├── novaic-app/
│   │   └── README.md
│   ├── novaic-contracts/
│   │   └── README.md
│   ├── novaic-control-plane/
│   │   └── README.md
│   ├── novaic-gateway/
│   │   └── README.md
│   ├── novaic-runtime-orchestrator/
│   │   └── README.md
│   ├── novaic-shared-kernel/
│   │   └── README.md
│   ├── novaic-storage-b/
│   │   └── README.md
│   ├── novaic-tools-server/
│   │   └── README.md
│   └── README.md
├── sync_design/
│   ├── implementation_plan.md
│   └── multi_device_sync_caching.md
├── vnc/
│   └── README.md
├── agent-handoff-context.md
├── architecture-verification-2026-04.md
├── backend-architecture.md
├── claude-code-skills-architecture-analysis.md
├── context-assembly-dfs-step-tree.md
├── cortex-architecture.md
├── design-no-tool-system-message.md
├── DOC_VERIFICATION_REGISTRY.md
├── DOCUMENT_AGGRESSIVE_STRATEGY.md
├── DOCUMENT_INVENTORY.md
├── DOCUMENT_INVENTORY_ANNOTATED.md
├── entangled-architecture-upgrade-design-complete.md
├── entangled-architecture-upgrade-plan.md
├── entangled-cleanup-design.md
├── entangled-load-test.md
├── entangled-multi-worker-threat-model.md
├── entangled-params-canonical.md
├── entangled-pk-conventions.md
├── entangled-push-to-all-audit.md
├── entangled-rust-single-writer-notes.md
├── entangled-serviceization-design.md
├── entangled-sync-protocol-v1.md
├── entangled-tauri-capabilities-audit.md
├── entity-design-audit.md
├── im-tool-design.md
├── model-entity-refactor.md
├── NEW_DOCUMENTATION_BLUEPRINT.md
├── NOVAIC_CANONICAL_GUIDE.md
├── PENDING_DOC_VERIFICATION.md
├── README.md
├── scope-driven-agent-lifecycle.md
├── skills-domain-investigation-reports.md
├── sync-contract-execution-checklist.md
├── SYNC_CONTRACT.md
└── TREE.md
```

---

## 3. 与分层对应关系（速查）

| 物理路径 | 逻辑层 |
|----------|--------|
| 根下 `NOVAIC_CANONICAL_GUIDE.md`、`README.md`、`*architecture*`、`SYNC*` 等 | L0–L2 |
| `design/`、`research/`、`device/`、`gateway-upgrade/`、`ota/`、`p2p/`、`agent-approve-points/` | L3 |
| `runbooks/` | 现行运维（E2E、服务矩阵、热更新） |
| `misc/` | 联调杂项与调查（核心 Runbook 在 `runbooks/`） |
| `_legacy/` | L3 档案角色说明（索引；正文仍在各主题目录） |
| `submodules/`、`vnc/`、`review/`、`icons/` | 占位或索引为主 |
| `sync_design/` | 多端同步与缓存（现行说明，与 SYNC_CONTRACT 配套） |

