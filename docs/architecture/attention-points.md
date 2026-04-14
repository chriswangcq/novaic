# 架构关注点

> 截至 2026-04-14，服务拆分、命名治理和环境变量清除已完成。以下是后续演进中需要持续关注的点。

## 1. ~~Gateway 仍偏胖~~ ✅ 已大幅瘦身（10.4K → ~5K 行）

已完成：删除死代码（`common/llm/`、`config/settings.py`）、消除重复 `common/` 包、移除 `ConfigManagerDB`、精简 `ChatRepository`、迁出 `scripts/`。Gateway 现在 ~5K 行，职责清晰。

---

## 2. ~~前端 `src/gateway/` 目录命名有歧义~~ ✅ 已解决

`src/gateway/` 内两个文件（`auth.ts` re-export barrel、`sse.ts` SSEManager）在 Entangled 迁移后已无任何调用方，属于死代码，已物理删除。

---

## 3. ~~前端非实体状态管理偏轻~~ ✅ 评估后无需行动

实际调研发现前端状态管理已很完备：
- `application/store.ts` — 主 Zustand store（AppState），管理 layout、agent 选择、model、device、UI 开关等 ~40 个字段
- `stores/deviceStatusStore.ts` — 设备状态专用 Zustand store
- `application/logFilterStore.ts` — 日志筛选 Zustand store
- `application/logInputCacheStore.ts` — 日志 input 按需加载缓存
- `application/chatScrollRegistry.ts` — 滚动动作注册表
- 7 个 Service 类（Agent/Model/Layout/Device/VmUser/Skills/Sync）封装异步逻辑

组件内 `useState` 均为局部 UI 状态（表单输入、modal 开关等），属于正常用法，无需提升为全局 store。

---

## 4. Worker 运行时是最大代码块（14K 行），会持续膨胀

`novaic-agent-runtime/task_queue/` 包含 handler、saga、LLM 业务、工具调用等核心逻辑。随着 Agent 能力增长，这块膨胀最快。

**当前结构：**

```
task_queue/
├── handlers/        # 按领域拆分的 handler（llm、tool、runtime、subagent…）
├── business/        # LLM 业务逻辑
├── sagas/           # Saga 流程编排
├── utils/           # 广播、系统提示词、截断等工具
└── workers/         # Worker 进程（task、watchdog、scheduler、health、saga）
```

**风险点：**

- `llm_handlers.py`、`runtime_handlers.py` 可能膨胀到 500+ 行
- handler 之间的隐式依赖（通过 ctx dict 传递）缺乏类型约束

**行动项：**

- handler 文件超过 300 行时主动拆分
- 考虑为 ctx dict 定义 TypedDict，让 IDE 能做类型检查

---

## 5. VMControl Rust crate 编译开销大

`novaic-app/src-tauri/vmcontrol/` 包含 QEMU 控制、SPICE/VNC 协议、WebRTC、Android scrcpy 等重量级功能，编译时间长。

**行动项：**

- 如果 VMControl 更新频率低于前端/Tauri 壳层，配置 CI 的编译缓存（`sccache` 或 `cargo-cache`）
- 考虑将 VMControl 作为独立 crate 预编译，Tauri 壳层只链接

---

## 6. ~~端口与部署配置~~ ✅ 已优化

配置策略：**两层，CLI 参数优先**

```
services.json (开发默认值，git 管控)
      ↓
start.sh CLI 参数 (生产覆盖，ps aux 可见)
```

已完成的改进：
- **单一配置源**：gateway/runtime 的 `services.json` 改为 symlink → `novaic-common/config/services.json`
- **去冗余**：`services.json` 每个服务只保留 `url`，`host`/`port` 由 `config.py` 自动解析
- **CLI 参数驱动**：所有服务 URL 通过 `start.sh` 显式 CLI 参数传递，`ps aux` 一眼可见完整配置
- **零环境变量**：`JWT_SECRET` 移入 `services.json`（`secrets.jwt_secret`），`NOVAIC_ENTANGLED_URL` 改为 CLI `--entangled-url`
- **端口冲突修复**：vmcontrol 19996 → 19992，不再与 cortex 冲突

---

## 7. ~~Import 指向不存在的模块~~ ✅ 已确认为误报

经逐一磁盘校验，所有 5 处 import 实际均存在：

| Import | 实际位置 | 误判原因 |
|--------|---------|---------|
| `gateway.infra.sse` | `sse/` 包目录（`__init__.py` + `broadcaster.py`） | 按 `sse.py` 搜索未匹配包目录 |
| `gateway.api.schemas` | 磁盘存在，git 标记 `D`（重构中间态） | git status 与磁盘文件不一致 |
| `gateway.entity.sync_contract` | 同上 | 同上 |
| `common.http.clients` | `novaic-common/common/http/clients.py` | 搜索工具路径限制 |
| `entangled.app.factory` | Entangled 子模块中存在 | 子模块未被搜索工具索引 |

---

## 8. ~~`main_gateway.py` 仍是 God Module~~ ✅ 已通过微服务拆分解决

Gateway 完成微服务拆分（2026-04-14）：
- **Business Service** (`:19994`)：Agent/Skill/Form/Model 等业务逻辑独立为 `novaic-business/`
- **Device Service** (`:19993`)：设备管理/PC-Bridge WS/VM 操作独立为 `novaic-device/`
- `main_gateway.py` 从 ~1400 行瘦身至纯网关（Auth + Entity Proxy + Turn + File Proxy + App WS）
- 所有删除代码（~27K 行）来自 `novaic-gateway`，业务逻辑迁移到独立服务

---

## 9. Watchdog 与 Scheduler 功能重复（P1）

`WatchdogSync` 和 `SchedulerWorkerSync` 都执行相同逻辑：

```python
BusinessClient.get_due_for_wake()
SagaClient.dispatch(..., trigger_type="scheduled_wake")
```

差异仅在轮询间隔（watchdog 0.1s vs scheduler 可配置）和元数据丰富度。同时运行两者时，若后端无强幂等保证，会产生**重复唤醒**。

**行动项：** 合并为单一 Scheduler Worker，或在 Saga dispatch 层加幂等检查（`idempotency_key` 基于 wake 目标 + 时间窗口）。

---

## 10. Device 实体 Schema 所有权跨服务（P2）

`devices` 和 `vm-users` 的 SQL Schema 定义在 **Business** (`schema_push.py`)，但 Action Handler 实现在 **Device** 服务。修改这两个实体需要同时改两个服务的代码并协调部署顺序。

**行动项：**
- 方案 A：将 `devices` / `vm-users` 的 Schema 定义移至 Device 服务，Device 自己推送
- 方案 B：保持现状但在 CI 中加检查，确保 `ENTITY_ACTIONS` keys 与 `DEVICE_ACTIONS` keys 一致

---

## 11. `ServiceConfig` God Object（P2）

单个类持有所有服务的 URL、密钥、OSS、VM 超时、截断策略、重试、TURN、Cortex 参数等 ~60 个属性。问题：

- 每个服务只需要其中一小部分，但 import 时加载全部
- import 时绑定 JSON，测试时不便 mock/override
- 不相关配置耦合在一起，修改 Cortex OSS 配置可能触发 Gateway 的 config 验证失败

**行动项：** 按服务域拆分为 typed dataclass（`GatewayConfig`、`CortexConfig`、`DeviceConfig` 等），各服务只导入自己需要的。`ServiceConfig` 降级为向后兼容的聚合 facade。

---

## 12. 文档与代码不一致（P2）

| 位置 | 不一致描述 |
|------|-----------|
| Gateway 注释 | 仍提及 "reverse proxy `/internal/*` to Business"，实际 `/internal` 只有 auth |
| `gateway/entity/schema_push.py` | no-op 函数，但 lifespan 仍调用它 |
| Entangled README | 文档列出 `ENTANGLED_HOST` 等环境变量，但 `config.py` 已不读取任何环境变量 |
| `task_queue/client.py` | 类和 docstring 多处写 "Gateway"，实际连接的是 Queue Service |

**行动项：** 清理过时注释、删除 no-op 调用、更新 README。

---

## 13. 两套启动脚本不统一（P2）

| 脚本 | 定位 | 差异 |
|------|------|------|
| `scripts/start.sh` | 生产级 | 完整 10 个服务，动态读 `services.json`，CLI 传参 |
| `scripts/start-all.sh` | 开发级 | 硬编码 URL，只启动部分服务，不走 `services.json` |

开发者用 `start-all.sh` 启动后发现端口/配置与 `services.json` 不匹配，调试困难。

**行动项：** 统一为一个脚本 + `--dev` flag（dev 模式省略 OSS/外部依赖），或将 `start-all.sh` 改为调用 `start.sh` 的 wrapper。

---

## 14. ~~Cortex 启动依赖模块级变量~~ ✅ 已修复

所有 Python 服务（Gateway/Business/Device/Cortex）统一改为 `uvicorn.run(app, ...)` 直传 app 对象模式，不再使用字符串 import path `"module:app"`。这避免了 uvicorn worker 进程 re-import 模块导致 `_cli_args` 为 `None` 的问题。

---

## 15. Device 服务存在两条 VM 路径（P3）

- **本地 QEMU**（`VmManager`）：启动时 `recover_processes()`，关闭时 `stop_all()`
- **远程 VmControl**（`pc_client` WebSocket → 用户 PC 上的 Rust 进程）

注释标记本地 QEMU 为 "legacy/local"，但代码仍活跃。两条路径并存增加理解成本和测试负担。

**行动项：** 若云端部署不再使用本地 QEMU，标记 `VmManager` 为 `@deprecated` 并在 `main_device.py` 中用 feature flag 控制是否启动。

---

## 16. `strict_config.py` 验证不完整（P3）

`_validate_required_keys` 只检查顶层 section 和部分叶子路径（~15 个 key），但 `ServiceConfig` 实际读取 ~60 个 key。新增配置项时容易遗漏验证，上线后才发现 `KeyError`。

**行动项：** 基于 `ServiceConfig` 的所有 `_CFG.get(...)` 调用自动生成验证清单，或改用 JSON Schema / Pydantic model 做全量校验。

