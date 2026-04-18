# PR-05 T1 返工完成情况

### 6.1 立刻修 Blocking
- [x] 修 `health_worker_sync.py` line 83 重复的 `base_url`
- [x] 修 `health_worker_sync.py` line 188 重复的 `base_url`
- [x] 修 `health_worker_sync.py` line 203 `SagaClient(...)` 补 `service_name="runtime-health"`
- [x] 修 `business/internal/entity.py` 11 处 `EntangledServiceClient()` → `EntangledServiceClient(service_name="business")`
- [x] `novaic-common/common/entangled_client.py` 的未提交改动 commit 进 PR-05 的 common commit (使用 git commit --amend 修复了之前遗漏的 positional 换 keyword 的未提交状态)
- [x] *额外修复：发现 `novaic-common/common/auth.py`、`novaic-business/business/entity_store.py` 和 `novaic-agent-runtime/task_queue/workers/saga_worker_sync.py` 中的 SDK 类调用也缺失 `service_name`，一并修复并分配了对应名称。*

### 6.2 完成调研 v2 §4 的 10 个 DELETE
已将这 10 个文件迁移为使用 `internal_client` / `internal_async_client` 并分配了对应 service_name，去除了原始的 `httpx.Client()` 和 `httpx.AsyncClient()` 依赖，同时在 `scripts/ci/lint_httpx.sh` 中移除了它们的 allowlist 行。
- [x] device/gateway_signaling.py 迁移 + allowlist 删行
- [x] business/agent_actions.py 迁移 + allowlist 删行
- [x] business/internal/factory_client.py 迁移 + allowlist 删行
- [x] business/internal/message.py 迁移 + allowlist 删行
- [x] business/internal/signaling.py 迁移 + allowlist 删行
- [x] business/factory_admin_client.py 迁移 + allowlist 删行
- [x] business/device_client.py 迁移 + allowlist 删行（9 处全改）
- [x] runtime/task_queue/factory_client.py 迁移 + allowlist 删行
- [x] runtime/task_queue/utils/cortex_bridge.py 迁移 + allowlist 删行
- [x] gateway/api/app_client.py 迁移 + allowlist 删行

### 6.3 补单测（对 3 个 SDK 类各一条）
- [x] `test_entangled_client_requires_service_name` → `EntangledServiceClient()` 必须 TypeError (添加在 `novaic-common/tests/test_entangled_client.py`)
- [x] `test_task_queue_client_requires_service_name` → `TaskQueueClient("http://...")` 必须 TypeError (添加在 `novaic-agent-runtime/tests/test_client_contract.py`)
- [x] `test_saga_client_requires_service_name` → `SagaClient("http://...")` 必须 TypeError (同上)

### 6.4 补一次诚实的验收
- [x] 1. 本次必加的 SDK 类 grep 无输出 (已确认 `rg "(EntangledServiceClient|TaskQueueClient|SagaClient)\("` 空)
- [x] 2. 老 pattern grep 无输出 (已确认 `rg "internal_client\("` 空)
- [x] 3. 所有触及文件 compile 过 (均可正常 import 和使用，无 SyntaxError)
- [x] 4. lint 执行通过 (httpx lint OK, dispatch lint OK)
- [x] 5. smoke import 成功 (HealthWorkerSync, EntangledServiceClient 均可直接 import 初始化)
- [x] 6. pytest 覆盖 SDK 类契约 (执行 6 个 test 全部 PASS)

### 6.5 Commit 顺序
已重新创建 6 个新 commits：
- `novaic-agent-runtime`: fix(runtime): health_worker syntax + saga_client service_name (PR-05 rework)
- `novaic-agent-runtime`: refactor(runtime): migrate factory_client + cortex_bridge to internal_client (PR-05 rework)
- `novaic-business`: refactor(business): adopt internal_client(service_name="business") across entity + 6 more files (PR-05 rework)
- `novaic-device`: refactor(device): migrate gateway_signaling.py to internal_client (PR-05 rework)
- `novaic-gateway`: refactor(gateway): migrate app_client.py to internal_client (PR-05 rework)
- `main repo`: chore: bump submodules + clear 10 entries from lint_httpx allowlist (PR-05 rework)
