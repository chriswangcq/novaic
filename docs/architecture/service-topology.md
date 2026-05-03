# NovAIC 服务拆分原理与调用拓扑

> 更新：2026-05-03。本文描述当前主路径；历史 Gateway-centric / RO / Gateway entity proxy 叙述不作为实现依据。

---

## 一、当前原则

| 原则 | 当前落点 |
|---|---|
| Gateway 薄边缘 | Auth、App WS push/signaling、Entangled endpoint discovery、TURN、File Proxy |
| Entangled 是实体同步层 | App 直连 Entangled WS；Business 是服务端 action/HTTP 写入方 |
| Business 是产品业务层 | action hooks、Environment、SubAgent、Device 编排、配置读取 |
| Runtime 是执行层 | Queue/Saga/Task Worker，调用 Cortex、Factory、Business/tool executor |
| Cortex 是工作轨迹层 | scope tree、reasoning/action/observation、payload ref、summary.md |
| Device 是硬件层 | CloudBridge、VmControl、WebRTC/VM/HD 控制 |

---

## 二、服务清单

| 进程 | 端口 | 职责 |
|---|---:|---|
| **Entangled** | `19900` | 实体 HTTP + sync WS，schema/action 注册，服务端 SQLite |
| **Gateway** | `19999` | Auth、App WS、file proxy、TURN、Entangled sync endpoint discovery |
| **Business** | `19998` | 产品 action hooks、Environment、Subscriber 输入、Device 编排、内部产品 API |
| **Device** | `19993` | Device registry、CloudBridge typed WS、hardware/VM/WebRTC API |
| **Queue Service** | `19997` | Task/Saga/session 调度，拥有 `queue.db` |
| **Cortex** | `19996` | Agent scope/context/work trace/payload/sandbox |
| **Storage-A** | `19995` | 文件与大对象 |
| **LLM Factory** | deployment-specific | provider/API key/model routing，标准 chat completions |
| **Runtime Workers** | worker | Saga Worker、Task Worker、Health、Scheduler |
| **Tauri App** | local | React UI、Entangled Rust cache、VmControl 本地端 |

---

## 三、当前调用拓扑

```text
                  ┌─────────────────────┐
                  │      Tauri App       │
                  │ React + Rust cache   │
                  └───────┬───────┬─────┘
                          │       │
     Auth/File/App WS HTTP│       │Entangled sync WS
                          ▼       ▼
                    ┌────────┐  ┌────────────┐
                    │Gateway │  │ Entangled  │
                    │:19999  │  │ :19900     │
                    └───┬────┘  └─────▲──────┘
                        │             │
       signaling/push   │             │HTTP/action writes
                        ▼             │
                    ┌────────┐        │
                    │Business│────────┘
                    │:19998  │
                    └──┬──┬──┘
       notifications  │  │device orchestration
                      ▼  ▼
              ┌──────────┐    ┌────────┐
              │Queue Svc │    │Device  │
              │:19997    │    │:19993  │
              └────▲─────┘    └───┬────┘
                   │              │CloudBridge
                   │claim         ▼
             ┌─────┴────────┐  ┌──────────┐
             │Runtime       │  │VmControl │
             │Workers       │  │local     │
             └─┬────┬────┬──┘  └──────────┘
               │    │    │
               │    │    └────► Business / Device tools
               │    └─────────► LLM Factory
               └──────────────► Cortex
```

---

## 四、用户消息生命周期

```text
1. App dispatch messages.send
   → Entangled action hook
   → Business message action

2. Business
   → writes chat UI projection to Entangled
   → creates Environment IM event + notification

3. DispatchSubscriber
   → claims dispatchable Environment notification
   → Queue Service /api/queue/dispatch

4. Queue Service
   → serializes by agent/thread/session
   → Saga Worker claims wake saga

5. Runtime
   → Cortex prepare_for_llm
   → LLM Factory chat completions
   → tool calls through Business/Cortex/Device/Runtime native executors
   → Cortex append observation/reasoning/action

6. Reply/finalize
   → im_reply writes user-visible message through Business/Environment projection
   → skill_end(report=...) closes wake scope summary.md in Cortex
   → Agent Monitor reads Entangled activity projection
```

---

## 五、边界速查

| 不要再这么理解 | 当前真实边界 |
|---|---|
| App 通过 Gateway REST 发聊天消息 | App 通过 Entangled action `messages.send` 进入 Business |
| Gateway 负责 entity sync/schema | Entangled 负责 sync/schema；Gateway 只做 endpoint discovery |
| Queue DB 在 Gateway | Queue Service 拥有 `queue.db` |
| Runtime 通过 Gateway 取业务状态 | Runtime 通过 Business/Cortex/Factory/Queue 按职责取数据 |
| Device action hook 在 Gateway | Business 处理 devices action hook，Device 只执行硬件 |
| Agent Monitor 查 execution log | Agent Monitor 读 Entangled `agent-activity-*` 投影 |

