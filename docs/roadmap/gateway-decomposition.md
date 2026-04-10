# Gateway 职责膨胀现状分析与拆分建议

> 基于 `novaic-gateway` 源码审计（2026-04-10）
> gateway/ 目录 **26,230 行** Python + main_gateway.py **2,123 行**

---

## 一、Gateway 现在身上背了多少个角色？

经过源码审计，Gateway 目前至少同时扮演了 **7 个完全不同的角色**：

```
         ┌─────────────────────────────────────────┐
         │           main_gateway.py               │
         │           (2,123 行巨石入口)               │
         └──────────────┬──────────────────────────┘
                        │
    ┌───────────────────┼───────────────────────────┐
    │                   │                           │
    ▼                   ▼                           ▼
 ① API 网关        ② 数据库宿主         ③ CloudBridge 中继
 (路由+鉴权)       (Entangled+gateway.db)  (设备穿透通道)
    │                   │                           │
    ▼                   ▼                           ▼
 ④ VM/QEMU 管理    ⑤ 任务编排中心         ⑥ 前端OTA配置
 (setup/deployer)  (TaskManager)         (CDN URL 下发)
                        │
                        ▼
                   ⑦ 消息广播中枢
                   (broadcast_chat_message)
```

---

## 二、逐角色拆解

### ① API 网关 + 鉴权中心 (应有之义 ✅)

| 文件 | 行数 | 说明 |
|---|---|---|
| `api/routes.py` | 401 | 核心路由注册（config/health/cleanup/VNC） |
| `api/agents.py` | 788 | Agent CRUD + 动作 |
| `api/devices.py` | 961 | 统一设备 API |
| `api/entities.py` | ~280 | Entangled 实体通用路由 |
| `api/skills.py` | ~430 | 技能管理 |
| `infra/auth.py` | 514 | JWT 签发/刷新/校验 |
| `infra/deps.py` | ~130 | 路由依赖注入(get_current_user) |

**判定**：这是 Gateway 本职工作，不需要拆。

---

### ② 数据库双重宿主 (需要审视 ⚠️)

Gateway 目前管理了**两套数据库**：

**A. Entangled EntityStore（业务主库）**
| 文件 | 行数 | 说明 |
|---|---|---|
| `entity/defs.py` | ~380 | 所有实体定义（agents, messages, api-keys...） |
| `entity/defs_models.py` | ~480 | Model 实体定义 |
| `entity/defs_agent_forms.py` | ~280 | Agent Form 定义 |
| `entity/defs_stream.py` | ~170 | 流式实体定义 |
| `entity/defs_users.py` | ~90 | 用户实体定义 |
| `entity/store.py` | ~280 | GatewayEntityStore（Hook 继承） |
| `entity/entangled_bridge.py` | ~180 | 初始化网桥 |
| `entity/migrations.py` | ~140 | 迁移逻辑 |

**B. 原生 gateway.db（遗留运维库）**
| 文件 | 行数 | 说明 |
|---|---|---|
| `db/schema.py` | **2,080** | 🔴 全库最大文件！包含 v1~v63 全部迁移脚本 |
| `db/repositories/chat.py` | 920 | 聊天仓库 |
| `db/repositories/skill.py` | 422 | 技能仓库 |
| `db/repositories/message.py` | ~470 | 消息仓库 |
| `db/repositories/config.py` | ~300 | 配置仓库 |
| `db/repositories/device.py` | ~200 | 设备仓库 |

**问题**：`schema.py` 2080 行几乎全是历史迁移代码（v1到v63每次ALTER TABLE都保留着）。v63 之后大量表已经 DROP 进入 Entangled，但迁移历史还压在天灵盖上，读起来极其恐怖。

---

### ③ CloudBridge 云端中继 (边界模糊 ⚠️)

| 文件 | 行数 | 说明 |
|---|---|---|
| `api/app_client.py` | 657 | AppBridge WS（用户 UI 连线） |
| `api/vmcontrol.py` | ~360 | VmControl 代理路由 |
| `api/internal/pc_client.py` | 890 | 🔴 CloudBridge 核心管理器！远端设备管理/信令/消息转发 |

**问题**：`pc_client.py` 890 行是一个完整的"远程设备连接管理服务"，包含连接池、心跳、信令转发等。这本质上是一个独立微服务的体量，却塞在了 Gateway 的 `api/internal/` 里。

---

### ④ VM/QEMU 全生命周期管理 (最大越界 🔴)

| 文件 | 行数 | 说明 |
|---|---|---|
| `api/vm.py` | **1,458** | 🔴 第二大文件！VM 的 REST API（创建/启停/快照/resize） |
| `vm/manager.py` | 987 | VmManager：QEMU 进程管理/恢复/清理 |
| `vm/setup.py` | 945 | VM 初始化安装流程（下载镜像/配置网络/安装guest agent） |
| `vm/deployer.py` | ~460 | VM 部署策略 |
| `vm/ssh.py` | ~240 | SSH 连接管理 |
| `vm/repository.py` | ~210 | VM 配置存储 |
| `api/vm_users.py` | ~260 | VM 内多用户管理 |
| `api/vm_user_actions.py` | ~60 | VM 用户动作 |

**总计 ~4,620 行纯 VM 管理代码！**

**问题**：Gateway 一个网关进程，居然在管 QEMU 的 `qemu-system-x86_64` 子进程启停、磁盘镜像下载、SSH 密钥注入、guest agent 通信。这是一个完整的 **VM Orchestrator** 的工作量。

---

### ⑤ 任务编排中心 (可以拆出 ⚠️)

| 文件 | 行数 | 说明 |
|---|---|---|
| `core/task_manager.py` | **1,187** | TaskManager：任务 spawn/cancel/status/cleanup |
| `api/internal/agent.py` | 1,373 | 🔴 内部 Agent 动作 API（最核心的思考链触发入口） |
| `api/internal/subagent.py` | 782 | SubAgent 管理 |
| `api/internal/message.py` | 658 | 内部消息处理 |
| `api/internal/task.py` | 441 | 任务内部 API |
| `api/internal/factory_client.py` | ~390 | LLM Factory 代理 |

**问题**：`internal/agent.py` 1373 行包含了 Agent 的思考链触发（消息发送→唤醒Watchdog→下发给Queue Service）。这本质上是 Runtime 域的工作，Gateway 不应该知道 Agent 怎么"思考"。

---

### ⑥ 前端 OTA + 杂项配置 (不应该在这 ⚠️)

在 `main_gateway.py` 里直接硬编码了：
```python
DEFAULT_FRONTEND_CDN_URL = "https://relay.gradievo.com/resource/frontend/v0.3.0/"
```
以及 `migrate_old_data()` 数据迁移函数（175行）也直接塞在主入口文件里。

---

### ⑦ 消息广播中枢 (职责扩散 ⚠️)

`main_gateway.py` 里直接写了 `broadcast_chat_message()` 和 `broadcast_log()` 等函数，包含了消息的持久化 + 广播双重逻辑。这些应该完全由 Entangled 的 EntityStore Hook 处理，而不是在主入口文件里手写。

---

## 三、体量热力图

```
文件体量 Top 10 (按行数)：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
db/schema.py              2,080 行 🔴🔴🔴  历史迁移包袱
api/vm.py                 1,458 行 🔴🔴    VM REST 全家桶
api/internal/agent.py     1,373 行 🔴🔴    思考链/动作触发
core/task_manager.py      1,187 行 🔴🔴    任务编排
vm/manager.py               987 行 🔴      QEMU 进程管理
api/devices.py              961 行 🔴      设备统一 API
vm/setup.py                 945 行 🔴      VM 安装流程
db/repositories/chat.py     920 行 🔴      聊天仓库
api/internal/pc_client.py   890 行 🔴      CloudBridge 管理
api/agents.py               788 行 🟡      Agent CRUD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
main_gateway.py           2,123 行 🔴🔴🔴  入口巨石
```

---

## 四、诊断结论

| 角色 | 行数 | 是否属于网关本职 | 建议 |
|---|---|---|---|
| ① API 路由 + 鉴权 | ~3,500 | ✅ **核心职责** | 保留 |
| ② Entangled 数据宿主 | ~2,000 | ✅ 合理 | 保留，但 `schema.py` 迁移历史应归档冻结 |
| ③ CloudBridge 中继 | ~1,900 | ⚠️ 勉强合理 | 长期可拆为独立进程 |
| ④ **VM/QEMU 管理** | **~4,620** | 🔴 **严重越界** | **最应优先拆出** |
| ⑤ 任务编排 | ~4,830 | ⚠️ 边界模糊 | `internal/agent.py` 应归 Runtime |
| ⑥ OTA 配置 + 迁移 | ~200 | ⚠️ 杂项 | 迁移逻辑应提到独立脚本 |
| ⑦ 消息广播 | ~300 | ⚠️ 重复 | 应完全交给 EntityStore Hook |

**Gateway 现在的核心矛盾**：一个本应只做"路由+鉴权+数据中转"的网关进程，却同时在管 QEMU 虚拟机、编排任务、连接远端设备、广播消息。它已经从一个"门卫"膨胀成了"集市中心"。

---

## 五、拆分优先级建议

### P0：VM 管理独立化
将 `gateway/vm/` 和 `api/vm.py` + `api/vm_users.py` 整体抽出为独立的 `novaic-vm-orchestrator` 进程。
- 理由：这4600行代码与网关核心功能(路由/鉴权)零耦合，只是恰好"塞在这里"
- Gateway 通过 HTTP 调用  VM Orchestrator 即可（就像现在调 Queue Service 一样）
- 预估工作量：3-5 天

### P1：internal/agent.py 归入 Runtime 域
- 这1373行包含了"怎么触发思考"的业务逻辑，应该归入 `novaic-agent-runtime` 管辖
- Gateway 只需保留一个 thin proxy 转发
- 预估工作量：2-3 天

### P2：schema.py 迁移历史冻结
- v63 之前的2080行迁移脚本全部移入 `db/migrations/archived/`，只保留最新 baseline schema
- Gateway 新实例直接从 baseline 创建，不再跑 60+ 步迁移
- 预估工作量：1 天

### P3：CloudBridge 独立化（长期）
- 890行的 `pc_client.py` 天然是一个独立服务的体量
- 但因为它需要与 AppBridge WS 共享用户连接信息，目前强行断开会增加复杂度
- 建议等 Entangled 的 WS 层进一步成熟后再拆
