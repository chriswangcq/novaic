# Entangled 的定制切面：业务 Hook 实现

> **⚠️ 2026-04-16 更新**：Gateway 不再拥有 `GatewayEntityStore(SqlEntityStore)`。
> 当前架构中，Entangled action hooks 由 **Business Service** 处理（`main_business.py` 中注册），
> Gateway 仅保留 `AuthEntityStore` 管理本地 auth 实体。业务 Hook 逻辑见 `novaic-business/main_business.py`。

> 路径参考：`novaic-business/main_business.py`（Hook 注册）、`novaic-business/business/internal/entity.py`（entity proxy）、`novaic-gateway/gateway/entity/store.py`（仅 `AuthEntityStore`，管理 auth 实体）

## 1. 从数据模型到行为声明 (`defs.py`)
所有的业务对象的长相（属性名字/长度等），全部脱离 SQL DDL，集中用 Python 代码表达在 `gateway/entity/defs.py` 内（例如：`AGENT_TOOLS`, `SKILLS`, `MESSAGES`）。
这些表述不是死的数据，它们带有能力声明（sync_type、subscription_mode、actions 等），保证前后端数据类型 `TypeScript <-> Python` 的彻底对齐。

> **注意**: Entangled 遵循 "一次写入 = 一次通知" 原则，不存在自动级联。Business Service 作为唯一 Entangled HTTP 消费者按需写入所需实体，客户端渲染层自行决定联动更新策略。

## 2. 操作阻截：Before / After Hooks
**Business Service** 是所有业务实体 CRUD 的中枢处理节点。Entangled action hooks 在 `main_business.py` 中注册，Business 通过 `EntangledServiceClient` 直连 Entangled HTTP，针对不同 Entity 执行干预方法。

> ~~旧架构~~：Gateway 曾派生 `GatewayEntityStore(SqlEntityStore)` 直接继承 Entangled SQL 存储。当前架构中 Gateway 仅保留 `AuthEntityStore`（管理 users/tokens/api-keys 等本地 auth 实体），不再参与业务 Hook。

### `before_` 系钩子（动作前的篡改与检查）：
- **拦截检查型**：Business Service 借此拦下越权操作（底层自动补 user_id）。
- **生成型：Nanoid**：Business Service 在插入动作被提交前，为新的 Agent、Session 或其它需要优雅短串记录生成可读又安全的随机名（例如给某虚拟机的名字上个 NanoId 避免碰撞冲突）。

### `after_` 系钩子（旁路与异步投递的扳机）：
- **启动任务 (`messages` 为例)**：当用户发出请求消息，经 Gateway 鉴权后写入 Business → Entangled。通过 `after_insert` hook，Business Service 触发判断：如果这是来自某个处于开启状态机器的人的消息，它将直接通知 Queue Session Coordinator 唤醒对应系统，而定时类唤醒则由 Scheduler 统一轮询并投递。
- **通知派发**：在这里甚至可以结合特定的状态字段直接改变前端某个浮层的开关或者全局变量下发。
