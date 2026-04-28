# PR-05 调研报告 (v2)

## 1. 问题 1：`internal_client` 真实 surface 长什么样？

通过 `grep_search` 查看 `novaic-common/common/http/clients.py`：

- **有几个 factory 函数？**
  共 8 个相关函数：
  - 底层工厂：`create_internal_async_client`, `create_internal_sync_client`, `create_external_async_client`, `create_external_sync_client`
  - 上层包装：`internal_async_client`, `internal_sync_client`, `external_async_client`, `external_sync_client`
  其中内部调用相关的共有 4 个核心函数 + 1 个 alias。
- **`internal_client` 是独立函数还是 alias？**
  它是一个 alias，定义为 `internal_client = internal_sync_client`（第 55 行）。
- **修改底层函数 vs 修改 alias 会有什么差别？**
  如果只修改 alias 的签名，那些直接调用 `internal_async_client` 或 `internal_sync_client` 的代码可能漏网。我们需要在 `internal_async_client` 和 `internal_sync_client`（以及它们的底层 `create_*` 函数）上加上 `service_name: str`，保证所有的内部调用入口必带 `service_name`。
- **现有签名是 `**kwargs: Any` 还是有明确参数列表？新参 `service_name` 要放哪？是否破坏现有 call site？**
  现有包装函数的签名全是 `**kwargs: Any`。新参 `service_name: str` 必须作为第一个 positional argument 放置（例如 `def internal_async_client(service_name: str, **kwargs: Any):`），这**一定会**破坏现有没有传 `service_name` 的 call site。

**函数迁移表**：

| 函数 | 是否需要加 `service_name` |
| --- | --- |
| `create_internal_async_client` | 是 |
| `create_internal_sync_client` | 是 |
| `internal_async_client` | 是 |
| `internal_sync_client` | 是 |
| `internal_client` (alias) | 是 (随 `internal_sync_client` 改变) |
| 其他 external_* | 否 |

---

## 2. 问题 2：所有 call site 在哪？分别该传什么 `service_name`？

`TaskQueueClient` 和 `SagaClient` 并不是跨服务通用 SDK，而是 runtime 的内部类，`service_name` 应由两个 worker 各自传 `runtime-task` / `runtime-scheduler`；`EntangledServiceClient` 则在 business 等处被实例化。所有相关的类都需要在 `__init__` 要求传入 `service_name`。

| # | 文件 | 行号 | SDK/调用方 | 实例化/调用代码 | 应传 `service_name` |
| --- | --- | --- | --- | --- | --- |
| 1 | `novaic-agent-runtime/task_queue/workers/task_worker_sync.py` | 85 | `TaskQueueClient` | `TaskQueueClient(self.queue_service_url, timeout=timeout)` | `"runtime-task"` |
| 2 | `novaic-agent-runtime/task_queue/workers/task_worker_sync.py` | 86 | `SagaClient` | `SagaClient(self.queue_service_url, timeout=timeout)` | `"runtime-task"` |
| 3 | `novaic-agent-runtime/task_queue/workers/scheduler_worker_sync.py` | 78 | `SagaClient` | `SagaClient(self.queue_service_url, timeout=self.timeout)` | `"runtime-scheduler"` |
| 4-14 | `novaic-business/business/internal/entity.py` | 68/106/122/149/171/192/210/228/249/268/287 | `EntangledServiceClient` | `EntangledServiceClient(...)` | `"business"` |
| 15 | `novaic-agent-runtime/task_queue/handlers/llm_handlers.py` | 55 | `internal_client` | `internal_client(timeout=...)` | `"runtime-task"` |
| 17-18 | `novaic-agent-runtime/task_queue/workers/health_worker_sync.py` | 81, 186 | `internal_client` | `internal_client(...)` | `"runtime-health"` |
| 19 | `novaic-device/device/business_entity_client.py` | 39 | `internal_sync_client` | `internal_sync_client(...)` | `"device"` |
| 20-22 | `novaic-gateway/main_gateway.py` | 424, 442, 505 | `internal_async_client` | `internal_async_client(...)` | `"gateway"` |
| 23 | `novaic-gateway/gateway/infra/business_entity_client.py` | 36 | `internal_sync_client` | `internal_sync_client(...)` | `"gateway"` |

---

## 3. 问题 3：现有"手工注入 X-Internal-Key" 的代码在哪？PR-05 要不要一起收敛？

通过排查 `X-Internal-Key`，手工注入代码主要存在于：
1. `novaic-agent-runtime/task_queue/client.py` (如 `TaskQueueClient`, `SagaClient`, `recover_all`)
2. `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
3. `novaic-cortex/novaic_cortex/proxy.py`

**收敛方案：**
不收敛。参见以下《范围收窄决议》章节。由于目前各个微服务拥有独立的 internal key（如 `QUEUE_SERVICE_INTERNAL_KEY`，`CORTEX_INTERNAL_KEY`），盲目统一为 `NOVAIC_INTERNAL_KEY` 会导致 401 失败。现阶段只动 Service 身份，不动 Key。

---

## 4. 问题 4：PR-05 合并后，PR-04 的 allowlist 能删哪几行？

对目前 `scripts/ci/lint_httpx.sh` 中列出的文件逐一分析用途：

```bash
ALLOWLIST=(
  'novaic-common/common/http/clients.py'
  'tests/'
  # TRANSITIONAL — remove line-by-line as PRs migrate:
  'novaic-device/device/gateway_signaling.py'           # DELETE in PR-05 (内部调用 gateway，迁移至 internal_client)
  'novaic-business/business/provider_client.py'         # KEEP (永久保留：外部调用 LLM Provider 不应走内部客户端)
  'novaic-business/business/agent_actions.py'           # DELETE in PR-05 (内部调用 Queue Service，迁移至 internal_client)
  'novaic-business/business/internal/factory_client.py' # DELETE in PR-05 (内部调用 Factory，迁移至 internal_client)
  'novaic-business/business/internal/message.py'        # DELETE in PR-05 (内部调用 Queue cancel-all，迁移至 internal_client)
  'novaic-business/business/internal/signaling.py'      # DELETE in PR-05 (内部调用 Gateway，迁移至 internal_client)
  'novaic-business/business/factory_admin_client.py'    # DELETE in PR-05 (内部调用 Factory Admin，迁移至 internal_client)
  'novaic-business/business/device_client.py'           # DELETE in PR-05 (内部调用 Device，迁移至 internal_client)
  'novaic-agent-runtime/task_queue/factory_client.py'   # DELETE in PR-05 (内部调用 Factory，迁移至 internal_client)
  'novaic-agent-runtime/task_queue/utils/cortex_bridge.py' # DELETE in PR-05 (内部调用 Cortex，迁移至 internal_client)
  'novaic-gateway/gateway/api/app_client.py'            # DELETE in PR-05 (内部调用 Business，迁移至 internal_client)
  'novaic-cortex/novaic_cortex/file_resolver.py'        # KEEP (永久保留：外部调用，读取网络文件)
  'novaic-llm-factory/factory/routes/config_routes.py'  # KEEP (永久保留：外部调用，请求 OpenAI/Anthropic 验证/拉取可用模型)
  'novaic-llm-factory/factory/providers.py'             # KEEP (永久保留：外部调用 LLM Provider)
)
```

---

## 5. 范围收窄决议

对于 `X-Internal-Key` 与统一环境变量带来的冲突，为了防止爆炸半径失控，本 PR 范围做如下收窄调整：

| 任务项 | 原 ticket 意图 | 新裁决 | 你要做什么 |
| --- | --- | --- | --- |
| `X-Internal-Service: <service_name>` 自动注入 | 做 | **做** | 按原计划实现 |
| `service_name` 必填 | 做 | **做** | 按原计划实现 |
| `X-Internal-Key` 自动注入 | 做 | **不做** | 不要碰这块，保持现状由 caller 自己传 headers |
| 统一 `NOVAIC_INTERNAL_KEY` | 做 | **不做** | 另开 PR，先记技术债 |
| 删 `task_queue/client.py` 里的手工 Key 注入 | 做 | **不删** | 保留现有 `QUEUE_SERVICE_INTERNAL_KEY` 注入逻辑 |
| 删 `cortex_bridge.py` 里的手工 Key 注入 | 做 | **不删** | 保留现有 `CORTEX_INTERNAL_KEY` 注入逻辑 |

---

## 6. service_name 命名定稿

以下是 `service_name` 填写的参考规范，本次 PR-05 中只用到以下 7 个：

| service_name | 进程 | 备注 |
| --- | --- | --- |
| `business` | novaic-business | — |
| `cortex` | novaic-cortex | — |
| `gateway` | novaic-gateway | — |
| `device` | novaic-device | — |
| `runtime-task` | task_worker_sync | 原计划叫 `runtime-worker`，改 `-task` 更准确（与其他 worker 区分） |
| `runtime-scheduler` | scheduler_worker_sync | — |
| `runtime-health` | health_worker_sync | — |

---

## 7. 提交顺序约定

在修改 ALLOWLIST 时，必须遵循以下步骤：
1. 改代码（`httpx.Client()` → `internal_client(service_name=..., ...)`）。
2. **在同一个 commit 里** 把 `scripts/ci/lint_httpx.sh` 的 allowlist 对应行删掉。
3. 本地跑 `bash scripts/ci/lint_httpx.sh` 确认 green。
4. 才能 push，保证 CI 不会被意外 Break。
