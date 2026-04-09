# 文档持疑核验登记（全量）

> **方法**：每篇 **一个** subagent（或人工一轮），只对照 **该文件** 与代码；模板见 [`_scripts/SKEPTICAL_VERIFY_TEMPLATE.md`](_scripts/SKEPTICAL_VERIFY_TEMPLATE.md)。
> **进度**：`docs/_scripts/verification_state.json`（仅记录非 pending）；重生成本表：`python3 docs/_scripts/regen_verification_registry.py`。

## 统计

- **仓库内 `.md` 计数（含 `docs/` + 根 `HANDOVER.md`）**：189
- **pending（待核验）**：5
- **verified**：23 · **partial**：156 · **stale**：0 · **skipped/generated**：5

---

## 全表（路径 → 层级 → 状态）

| 路径 | 层级 | 状态 | 备注 |
|------|------|------|------|
| `HANDOVER.md` | 仓库根 · SSOT | partial | §2.1/§11.1 已对齐现行存储（2026-04）；全篇未逐段重读 |
| `docs/DOCUMENT_AGGRESSIVE_STRATEGY.md` | docs 根 | partial | 策略与保留集；非代码事实断言 |
| `docs/DOCUMENT_INVENTORY.md` | generated | generated | auto list; no factual claims |
| `docs/DOCUMENT_INVENTORY_ANNOTATED.md` | generated | generated | auto list |
| `docs/DOC_VERIFICATION_REGISTRY.md` | generated | generated | this registry |
| `docs/NEW_DOCUMENTATION_BLUEPRINT.md` | docs 根 | pending | — |
| `docs/NOVAIC_CANONICAL_GUIDE.md` | L0 入口 | verified | §3 ports vs services.json |
| `docs/PENDING_DOC_VERIFICATION.md` | generated | generated | regen_verification_registry.py 待办总表 |
| `docs/README.md` | L0 入口 | verified | 必读表与链接自检；持疑流程与 PENDING 优先级一致 |
| `docs/SYNC_CONTRACT.md` | docs 根 | verified | 路径与 novaic-app 子模块一致；v0.1 与 Path C 一致 |
| `docs/TREE.md` | generated | generated | generate_docs_tree.py |
| `docs/_archive/README.md` | 其他 | pending | — |
| `docs/_legacy/README.md` | L3 index | verified | L3 档案角色说明（无正文搬迁） |
| `docs/_scripts/SKEPTICAL_VERIFY_TEMPLATE.md` | _scripts | pending | — |
| `docs/agent-approve-points/01-novaic-architecture.md` | L2 审核 | verified | §4.3 design-level (four-tier names); §4.4 vs sync_broadcast_log + kind/status + optional BroadcastType; §5 table + idempotency ledger; sagas/handlers/queue vs repo |
| `docs/agent-approve-points/02-openclaw-architecture.md` | L2 审核 | verified | thirdparty/openclaw: pi-embedded-runner/run.ts + run/attempt.ts + pi-embedded-subscribe.ts line counts; PLUGIN_HOOK_NAMES 28 in plugins/types.ts; tool-catalog ToolProfileId minimal/coding/messaging/full; runEmbeddedPiAgent export chain; §3.1 outer loop vs while(true)+MAX_RUN_LOOP_ITERATIONS; subscribe stripBlockTags + EmbeddedBlockChunker; §6 JSONL entry 类型未在 vendor 内逐条核对 |
| `docs/agent-approve-points/03-optimization-points.md` | L2 审核 | verified | NovAIC 现状 vs novaic-agent-runtime + gateway; OpenClaw 对比未核 |
| `docs/agent-approve-points/README.md` | L2 审核 | verified | 索引表链接 ./01–03；与同目录文件一致 |
| `docs/agent-handoff-context.md` | docs 根 | verified | Gateway v63/schema/migration; main_gateway routers; internal_proxy + pc /ws; entangled_access/ServiceConfig; Cortex engine.prepare_messages_for_llm + step types; Runtime GatewayBusinessClient; §7/§13 markdown |
| `docs/architecture-verification-2026-04.md` | docs 根 | verified | §1–3 vs gateway/schema/deploy |
| `docs/backend-architecture.md` | docs 根 | verified | ports + ServiceConfig/tool_result 19994; v63 _SHADOW_AND_DEAD_TABLES; deploy Entangled/ vs entangled-service/ + factory llm-factory path; start.sh Entangled caveat; V2 Gateway row; watchdog path workers/ |
| `docs/claude-code-skills-architecture-analysis.md` | docs 根 | verified | NovAIC 两行可核对：system_prompt._build_skills_section、SkillRepository.match_skills_for_task；Claude Code 树为外部快照非本仓 |
| `docs/context-assembly-dfs-step-tree.md` | docs 根 | verified | §4.3 + §6 vs novaic-cortex api.py + context_stack/engine.py; legacy §4.1–4.2 retained |
| `docs/cortex-architecture.md` | docs 根 | verified | CORTEX_PORT/HOST; api.py routes vs §6; S3 users/{user_id}/ + agents/{agent_id}/ vs NOVAIC_OSS_PREFIX on s3_store_aliyun_oss only |
| `docs/design-no-tool-system-message.md` | docs 根 | verified | NO_TOOL_WARNING + cortex_handlers.prepare_llm_context；react_think scope_id/MAX_NO_TOOL_RETRIES/two triggers；tool_handlers _EXECUTORS；react_actions content steps + skill_end root |
| `docs/design/CHATS_AGENTS_TABS_DESIGN.md` | L3 design | partial | v63/Entangled header + novaic-app paths in §四；正文与实现需对照 Layout/* |
| `docs/design/COMMANDS_SPLIT_DESIGN.md` | L3 design | partial | 持疑对照 novaic-app/src-tauri/src/lib.rs + commands/；路径 lib.rs、get_cached_file/fetch_cached_bytes、无 vnc_urls.rs/gateway_sse；ACL 与 invoke 可能不同步 |
| `docs/design/DESIGN-ELIMINATE-RUNTIME-FROM-GATEWAY-TOOLS-SERVER.md` | L3 design | verified | Gateway helpers + schema v63 + tool_handlers scope_id/runtime_id payload; Tools Server = split repo; historical phases archived |
| `docs/design/DESIGN-ELIMINATE-RUNTIME-ROOT-PLAN.md` | L3 design | partial | §1.2 RO 边界 vs gateway ServiceConfig/main_gateway；§7 e2e；余下 Phase 表为历史计划 |
| `docs/design/DESIGN-GATEWAY-FILTERED-TOOLS-TASKS.md` | L3 design | partial | TOOL_NAME_TO_MOUNTED in gateway/agent_binding.py (incl. qemu/hd); no builtin-tools route in-tree agent.py; Tools Server split repo; Runtime tool list via Cortex (see cortex_handlers) |
| `docs/design/DESIGN-GATEWAY-RETURNS-FILTERED-TOOLS.md` | L3 design | partial | gateway/agent_binding.py: TOOL_NAME_TO_MOUNTED + proxy vm/mobile/hd + normalize_mounted; agent.py: no GET /internal/agents/{id}/builtin-tools nor _filter_builtin_tools_for_agent; tools_server split repo — doc §3 flow not fully implemented here |
| `docs/design/DESIGN-LOCAL-RELAY.md` | L3 design | partial | Aligned paths: novaic-quic-service (main/config/relay/protocol/auth). novaic-app: no local_relay/p2p/self_relay_url; setup_shared in setup.rs. LAN IP helper not in repo. |
| `docs/design/DESIGN-P2P-ORCHESTRATOR-PROPOSAL-C.md` | L3 design | partial | 术语：Orchestrator=P2P/relay 编排，非已移除的 RO；设计稿对照 backend-architecture + architecture-verification |
| `docs/design/DESIGN-P2P-REGISTRATION-DISCOVERY.md` | L3 design | partial | 无 Registry/Discovery/ServerDescriptor 实现；无 p2p crate；quic-service=STUN+relay；vmcontrol WebRTC 主线；文内已加 2026-04-09 对齐段 |
| `docs/design/DESIGN-P2P-UNIFIED.md` | L3 design | partial | novaic-quic-service src layout matches; P2pServer/P2pClient p2p crate not in repo—design aspirational; fixed doc paths + PHASE5 ref |
| `docs/design/DESIGN-gateway-no-forward.md` | L3 design | partial | no RO forward helpers in gateway; internal_proxy has no vm.py; §1 historical; agent.py VmControl WS not RO HTTP |
| `docs/design/DESIGN-novaic-quic-service-IMPLEMENTATION.md` | L3 design | partial | batch2 agent aborted; spot: align with novaic-quic-service crate; full pass later |
| `docs/design/DESIGN-novaic-quic-service.md` | L3 design | partial | §6.3+§7+§9 vs novaic-quic-service auth.rs/config.rs; novaic-quic-service layout matches §7; Gateway /api/p2p/* not present under novaic-gateway/gateway/api in this tree (expect deploy/other branch) |
| `docs/design/DESIGN-subagent-agent-routes.md` | L3 design | pending | — |
| `docs/design/DESIGN-subagent-centric-gateway-migration.md` | L3 design | partial | v63 header + key lines |
| `docs/design/DESIGN-subagent-wake-message-gateway-db.md` | L3 design | partial | v63 header |
| `docs/design/DESIGN-vm-tools-subagent-centric.md` | L3 design | pending | — |
| `docs/design/DEVICE_SUBJECT_DESIGN.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/EXECUTION_LOG_SUBAGENT_CAPSULES_DESIGN.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/HOT_UPDATE_EXECUTION_PLAN.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/IMPLEMENTATION-PLAN-runtime-cleanup-subagent-centric.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/IMPLEMENTATION-PLAN-tools-server-remove-runtime-ro.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/LAYOUT_CONTAINER_REFACTORING_DESIGN.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/MOBILE_FILE_LIST_REMOVAL_PLAN.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/MULTI_USER_DESIGN.md` | L3 design | partial | 2026-04-09 batch3: header + spot-check vs v63/Entangled |
| `docs/design/OPTIMIZATION_PLAN.md` | L3 design | partial | batch4 8-way: spot-check |
| `docs/design/PARALLEL_SERVICE_STARTUP_PROPOSAL.md` | L3 design | partial | batch4 8-way |
| `docs/design/RESPONSIVE_LAYOUT_DESIGN_V2.md` | L3 design | partial | batch4 8-way |
| `docs/design/SECURE_STORAGE_DESIGN.md` | L3 design | partial | batch4 8-way |
| `docs/design/SSE_USER_LEVEL_MIGRATION.md` | L3 design | partial | batch4 8-way |
| `docs/design/SUBUSER_MAINDESK_MOVE_TO_COLUMN3_DESIGN.md` | L3 design | partial | batch4 8-way |
| `docs/design/SYSTEM_DESIGN.md` | L3 design | partial | batch4 8-way |
| `docs/design/TAURI2_MOBILE_MODULARIZATION_PLAN.md` | L3 design | partial | batch4 8-way |
| `docs/design/UNIFIED_DESIGN_TASK_ASSIGNMENT.md` | L3 design | partial | batch5 8-way |
| `docs/design/UNIFIED_LAYOUT_AND_EXECUTION_LOG_DESIGN.md` | L3 design | partial | batch5 8-way |
| `docs/design/VM_STATUS_REPORT_STOPPED_DEVICES_PLAN.md` | L3 design | partial | batch5 8-way |
| `docs/device/DEVICE_AGENT_DECOUPLE_DATAFLOW_RESEARCH_ROUND2.md` | L3 device | partial | batch5 8-way |
| `docs/device/DEVICE_DATAFLOW_RESEARCH_ROUND1.md` | L3 device | partial | batch5 8-way |
| `docs/device/DEVICE_FLOATING_PANEL_DEVICEMODE_RESEARCH_ROUND3.md` | L3 device | partial | batch5 8-way |
| `docs/device/DEVICE_ITERATION_REVIEW_CONTEXT.md` | L3 device | partial | batch5 8-way |
| `docs/device/DEVICE_MANAGEMENT_DATA_STRUCTURE_REPORT.md` | L3 device | partial | batch5 8-way; v63 Entangled vs gateway.db (entity vs shadow; pc_clients local) |
| `docs/device/DEVICE_MANAGER_FLOATING_PANEL_DATA_SOURCE_RESEARCH.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_PC_CLIENT_ONLINE_PLAN.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R2.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_AGENT_DRAWER.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_PC_CLIENT_ONLINE_REVIEW_R3_SECURITY.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_SETUP_START_PC_CLIENT_ID_REVIEW.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_STATUS_RACE_MULTI_PC_RESEARCH_ROUND3.md` | L3 device | partial | batch6 8-way |
| `docs/device/DEVICE_STATUS_STORE_POLLING_RESEARCH_ROUND2.md` | L3 device | partial | batch7 8-way |
| `docs/device/DEVICE_SWITCH_FLOW_ANALYSIS.md` | L3 device | partial | batch7 8-way |
| `docs/device/PC_CLIENT_HANDLE_DEVICE_MESSAGE_REVIEW.md` | L3 device | partial | batch7 8-way; subagent retry: v63 header + line caveat |
| `docs/device/README.md` | L3 device | partial | batch7 8-way |
| `docs/entangled-architecture-upgrade-design-complete.md` | docs 根 | partial | 目标架构 ADR；与 SSOT 导言一致；细节未逐条对代码 |
| `docs/entangled-architecture-upgrade-plan.md` | docs 根 | partial | 路线图过程稿；分层路径与仓库结构一致 |
| `docs/entangled-cleanup-design.md` | docs 根 | partial | 技术债清零方案过程稿；未逐条验证实现进度 |
| `docs/entangled-load-test.md` | docs 根 | partial | batch8 8-way |
| `docs/entangled-multi-worker-threat-model.md` | docs 根 | partial | batch8 8-way |
| `docs/entangled-params-canonical.md` | docs 根 | partial | batch8 8-way |
| `docs/entangled-pk-conventions.md` | docs 根 | partial | batch8 8-way; v63 header aligned post-review |
| `docs/entangled-push-to-all-audit.md` | docs 根 | partial | batch8 8-way |
| `docs/entangled-rust-single-writer-notes.md` | docs 根 | partial | batch8 8-way |
| `docs/entangled-serviceization-design.md` | docs 根 | partial | batch8 8-way |
| `docs/entangled-sync-protocol-v1.md` | docs 根 | partial | batch8 8-way |
| `docs/entangled-tauri-capabilities-audit.md` | docs 根 | partial | batch9 8-way |
| `docs/entity-design-audit.md` | docs 根 | partial | batch9 8-way |
| `docs/gateway-upgrade/00-design.md` | L3 gateway-upgrade | partial | batch9 8-way: 过程稿；现行 main_gateway include_router 真值表 vs 历史 chat.py/tasks_api 计划；pointer architecture-verification §2 |
| `docs/gateway-upgrade/01-chat-router.md` | L3 gateway-upgrade | partial | batch9 8-way |
| `docs/gateway-upgrade/02-monitoring-router.md` | L3 gateway-upgrade | partial | batch9 8-way |
| `docs/gateway-upgrade/03-files-proxy-router.md` | L3 gateway-upgrade | partial | batch9 8-way; batch9 follow-up: header 行号快照说明 |
| `docs/gateway-upgrade/04-tasks-and-system-router.md` | L3 gateway-upgrade | partial | batch9 8-way; batch9 follow-up: header 行号快照说明 |
| `docs/gateway-upgrade/05-main-gateway-slim.md` | L3 gateway-upgrade | partial | batch9 8-way; batch9 follow-up: header 行号快照说明 |
| `docs/gateway-upgrade/06-schema-slim.md` | L3 gateway-upgrade | partial | batch11 8-way |
| `docs/gateway-upgrade/07-repository-cleanup.md` | L3 gateway-upgrade | partial | batch11 8-way; checklist 指向 entity/repos/chat |
| `docs/gateway-upgrade/08-docstrings-deadcode.md` | L3 gateway-upgrade | partial | batch11 8-way |
| `docs/gateway-upgrade/README.md` | L3 gateway-upgrade | partial | batch11 8-way |
| `docs/icons/README.md` | 其他 | partial | batch11 8-way |
| `docs/im-tool-design.md` | docs 根 | partial | batch11 8-way |
| `docs/misc/AGENTS_TAB_API_CONTRACT_VALIDATION.md` | L2/L3 misc | partial | batch11 8-way |
| `docs/misc/AGENTS_TAB_CONFIG_GATEWAY_API_REPORT.md` | L2/L3 misc | partial | batch11 8-way |
| `docs/misc/CLIENT_DB_ARCHITECTURE.md` | L2/L3 misc | verified | 重写为现行端侧数据；对齐 sync_design 与 novaic-app |
| `docs/misc/CROSS_PLATFORM_ARCHITECTURE.md` | L2/L3 misc | verified | 去掉 batch 批注；存储表述对齐 sync_design |
| `docs/misc/CURRENT_STATE_SURVEY_SUMMARY.md` | L2/L3 misc | partial | batch12 8-way; subagent code↔doc pass |
| `docs/misc/FRONTEND_HOT_UPDATE_SUMMARY.md` | L2/L3 misc | partial | batch12 8-way; subagent code↔doc pass |
| `docs/misc/IOS_BLACK_SCREEN_ISSUE_REPORT.md` | L2/L3 misc | partial | batch12 8-way; subagent code↔doc pass |
| `docs/misc/MOBILE_DESKTOP_UNIFICATION_PROGRESS.md` | L2/L3 misc | partial | batch13 8-way; subagent code↔doc pass |
| `docs/misc/README.md` | L2/L3 misc | partial | batch14 follow-up: survey git 指针 |
| `docs/misc/RELAY_MIGRATION_8_TO_47.md` | L2/L3 misc | partial | batch13 8-way; subagent code↔doc pass |
| `docs/misc/RO_GATEWAY_CALL_RELATIONSHIP.md` | L2/L3 misc | partial | batch13 8-way; subagent code↔doc pass |
| `docs/misc/TEST_RUN_REPORT.md` | L2/L3 misc | partial | batch13 8-way; subagent code↔doc pass |
| `docs/misc/VMCONTROL-TAURI-INTEGRATION-PLAN.md` | L2/L3 misc | partial | batch13 8-way; subagent code↔doc pass |
| `docs/misc/phase1-device-identity.md` | L2/L3 misc | partial | batch13 8-way; subagent code↔doc pass |
| `docs/misc/phase2-local-discovery.md` | L2/L3 misc | partial | batch14 8-way; subagent code↔doc pass |
| `docs/misc/phase3-p2p-remote.md` | L2/L3 misc | partial | batch14 8-way; subagent code↔doc pass |
| `docs/misc/phase4-multi-user.md` | L2/L3 misc | partial | batch14 8-way; subagent code↔doc pass |
| `docs/misc/survey-2026/README.md` | L2/L3 misc | partial | batch14 follow-up: code↔doc (OTA_FLOW whitelist; CHANGES; survey header) |
| `docs/misc/设计文档.md` | L2/L3 misc | partial | batch14 8-way; subagent code↔doc pass |
| `docs/model-entity-refactor.md` | docs 根 | partial | batch14 8-way; subagent code↔doc pass |
| `docs/ota/OTA_CHANGES_4_AGENT_REVIEW.md` | L3 ota | partial | batch14 follow-up: code↔doc (OTA_FLOW whitelist; CHANGES; survey header) |
| `docs/ota/OTA_FLOW_CAPABILITY_SWITCH.md` | L3 ota | partial | batch14 follow-up: code↔doc (OTA_FLOW whitelist; CHANGES; survey header) |
| `docs/ota/OTA_INVOKE_4_AGENT_REPORT.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_INVOKE_ROOT_CAUSE_ANALYSIS.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_PLAN_REVIEW_SUMMARY.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_RE_ENABLE_FRONTEND_REVIEW.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_REVIEW.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_RE_ENABLE_IMPLEMENTATION_PLAN_V2.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_V2_FRONTEND_3_AGENT_SUMMARY.md` | L3 ota | partial | batch15 second pass: routes.py; OTA_FLOW cross-refs; V2 window poll |
| `docs/ota/OTA_V2_FRONTEND_REVIEW.md` | L3 ota | partial | batch16 8-way: OTA favicon/routes; P2P paths archival note |
| `docs/p2p/P2P-FIXES-2026-03-11.md` | L3 p2p | partial | batch16 8-way: OTA favicon/routes; P2P paths archival note |
| `docs/p2p/P2P-PHASE4-CODE-REVIEW-REPORT.md` | L3 p2p | partial | batch16 8-way: OTA favicon/routes; P2P paths archival note |
| `docs/p2p/P2P-REVIEW-CONTEXT.md` | L3 p2p | partial | batch16 8-way: OTA favicon/routes; P2P paths archival note |
| `docs/p2p/P2P-SUBAGENT-FIX-LIST.md` | L3 p2p | partial | batch16 8-way: OTA favicon/routes; P2P paths archival note |
| `docs/p2p/P2P_ARCHITECTURE_SURVEY_ROUND1.md` | L3 p2p | partial | batch16 8-way: §2.3 p2p.py strikethrough |
| `docs/p2p/P2P_CRITICAL_REVIEW_ROUND2.md` | L3 p2p | partial | batch16 8-way: OTA favicon/routes; P2P paths archival note |
| `docs/p2p/P2P_RACE_AND_ERROR_HANDLING_RESEARCH_ROUND3.md` | L3 p2p | partial | batch16 8-way: OTA favicon/routes; P2P paths archival note |
| `docs/p2p/P2P_REFACTOR_PROPOSAL_A.md` | L3 p2p | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/p2p/P2P_REFACTOR_SUMMARY_ABC.md` | L3 p2p | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/p2p/P2P_RELAY_RACE_ANALYSIS.md` | L3 p2p | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/p2p/P2P_SERVER_ISSUE_REPORT.md` | L3 p2p | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/research/AGENTS_TAB_CONFIG_8_AGENT_ANALYSIS_SUMMARY.md` | L3 research | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/research/AGENTS_TAB_CONFIG_AGENT_SELECTION_ANALYSIS.md` | L3 research | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/research/AGENTS_TAB_CONFIG_ANALYSIS.md` | L3 research | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/research/AGENTS_TAB_CONFIG_API_ANALYSIS.md` | L3 research | partial | batch17 8-way: P2P archival; Agents Tab Entangled/skillsService |
| `docs/research/BACKEND_STARTUP_SLOWNESS_ANALYSIS.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/COMMANDS_ANALYSIS.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/DB-LOG-ANALYSIS-subagent.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/GATEWAY_VS_TAURI_RESPONSIBILITY_BOUNDARY_RESEARCH_ROUND3.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/QUEUE_SERVER_DISCONNECTED_ROOT_CAUSE_ANALYSIS.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/README.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/RELAY_IPV6_FIX_ANALYSIS.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/RESEARCH_APP_INSTANCE.md` | L3 research | partial | batch18 8-way: research↔repo (lib.rs cmds; p2p paths; RO lines) |
| `docs/research/RESEARCH_APP_INSTANCE_MYDEVICES_LINKAGE.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/RESEARCH_APP_INSTANCE_OVERVIEW.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/RESEARCH_APP_INSTANCE_SYNC_AND_FAILURE_SCENARIOS.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/RESEARCH_CONNECT_RELAY_FLOW.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/RESEARCH_DEVICE_BACKEND.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/RESEARCH_DEVICE_FRONTEND.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/RESEARCH_P2P_RELAY_TUNNEL_DETAILS.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/TOOL_ERRORS_ANALYSIS.md` | L3 research | partial | batch19 8-way: p2p/my-devices archival; subagent_cancel entangled |
| `docs/research/TOOL_ERRORS_TROUBLESHOOTING.md` | L3 research | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/research/UNIFIED_CURRENT_STATE_AND_RESEARCH.md` | L3 research | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/review/README.md` | 其他 | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/runbooks/ARCHITECTURE-SERVICES-AND-HANDLERS.md` | L1 runbooks | partial | batch12 8-way; subagent code↔doc pass; moved from docs/misc/ (rebuild phase1) |
| `docs/runbooks/E2E_READINESS.md` | L1 runbooks | partial | batch12 8-way; subagent code↔doc pass; moved from docs/misc/ (rebuild phase1) |
| `docs/runbooks/HOT_UPDATE_DEPLOY_STEPS.md` | L1 runbooks | partial | batch12 8-way; subagent code↔doc pass; moved from docs/misc/ (rebuild phase1) |
| `docs/runbooks/README.md` | L1 runbooks | verified | Phase1 索引；链至 E2E / 服务矩阵 / 热更新 |
| `docs/runbooks/VPN_DEPLOYMENT_GUIDE.md` | L1 runbooks | partial | batch13 8-way; subagent code↔doc pass; moved from docs/misc/ (rebuild phase2) |
| `docs/scope-driven-agent-lifecycle.md` | docs 根 | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/skills-domain-investigation-reports.md` | docs 根 | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/submodules/README.md` | 子模块 README | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/submodules/novaic-agent-runtime/README.md` | 子模块 README | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/submodules/novaic-app/README.md` | 子模块 README | partial | batch20 8-way: subagent_cancel; unify-vnc; submodules index |
| `docs/submodules/novaic-contracts/README.md` | 子模块 README | partial | batch21 8-way: submodule index + sync checklist caveat |
| `docs/submodules/novaic-control-plane/README.md` | 子模块 README | partial | batch21 8-way: submodule index + sync checklist caveat |
| `docs/submodules/novaic-gateway/README.md` | 子模块 README | partial | batch21 8-way: submodule index + sync checklist caveat |
| `docs/submodules/novaic-runtime-orchestrator/README.md` | 子模块 README | partial | batch21 8-way: submodule index + sync checklist caveat |
| `docs/submodules/novaic-shared-kernel/README.md` | 子模块 README | partial | batch21 8-way: submodule index + sync checklist caveat |
| `docs/submodules/novaic-storage-b/README.md` | 子模块 README | partial | batch21 8-way: submodule index + sync checklist caveat |
| `docs/submodules/novaic-tools-server/README.md` | 子模块 README | partial | batch21 8-way: submodule index + sync checklist caveat |
| `docs/sync-contract-execution-checklist.md` | docs 根 | verified | 配套 SYNC_CONTRACT；页眉已去批次标签 |
| `docs/sync_design/implementation_plan.md` | 其他 | verified | 与 novaic-app 现行实现一致（Entangled、prefs、列表 store） |
| `docs/sync_design/multi_device_sync_caching.md` | 其他 | verified | 与 novaic-app 现行实现一致（Entangled、prefs、列表 store） |
| `docs/vnc/README.md` | 其他 | verified | 索引页；实现见 novaic-app / vmcontrol；旧正文用 git 历史检索 |

---

## 批量分批（可选）

生成 **待办总表**（每批 8 个）：见 [`PENDING_DOC_VERIFICATION.md`](PENDING_DOC_VERIFICATION.md)；CSV：`python3 docs/_scripts/emit_verify_batches.py`

