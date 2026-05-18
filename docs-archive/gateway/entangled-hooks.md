# Entangled 的定制切面：业务 Hook 实现

> **⚠️ 2026-04-16 更新**：Gateway 不再拥有 `GatewayEntityStore(SqlEntityStore)`。
> 当前架构中，Entangled action hooks 由 **Business Service** 处理（`main_business.py` 中注册），
> Gateway 仅保留 `AuthEntityStore` 管理本地 auth 实体。业务 Hook 逻辑见 `novaic-business/main_business.py`。

> 路径参考：`novaic-business/main_business.py`（Hook 注册）、`novaic-business/business/internal/entity.py`（entity proxy）、`novaic-gateway/gateway/entity/store.py`（仅 `AuthEntityStore`，管理 auth 实体）

## 1. 从数据模型到行为声明

业务实体 schema 与 action 声明由服务端 schema push 进入 Entangled。Gateway 只保留本地 auth 相关 LOCAL_ONLY entity 定义；Agent、Message、Skill、Device 等产品实体不在 Gateway 定义，也不由 Gateway 推送。

当前主路径：

```text
Business schema/action definitions
  → Entangled schema registration
  → App Entangled WS sync contract
```

> **注意**: Entangled 遵循 "一次写入 = 一次通知" 原则，不存在自动级联。Business Service 作为唯一 Entangled HTTP 消费者按需写入所需实体，客户端渲染层自行决定联动更新策略。

## 2. 操作阻截：Before / After Hooks
**Business Service** 是产品 action hook 的处理节点。Entangled action hooks 在 `main_business.py` 中注册，Business 通过 `EntangledServiceClient` 直连 Entangled HTTP，针对不同 Entity 执行业务干预。

> ~~旧架构~~：Gateway 曾派生 `GatewayEntityStore(SqlEntityStore)` 直接继承 Entangled SQL 存储。当前架构中 Gateway 仅保留 `AuthEntityStore`（管理 users/tokens/api-keys 等本地 auth 实体），不再参与业务 Hook。

### `before_` 系钩子（动作前的篡改与检查）：
- **拦截检查型**：Business Service 借此拦下越权操作（底层自动补 user_id）。
- **生成型：Nanoid**：Business Service 在插入动作被提交前，为新的 Agent、Session 或其它需要优雅短串记录生成可读又安全的随机名（例如给某虚拟机的名字上个 NanoId 避免碰撞冲突）。

### `after_` 系钩子（旁路与异步投递的扳机）：
- **启动任务 (`messages` 为例)**：用户消息通过 App Entangled action `messages.send` 进入 Business。Business 写 Environment IM event 和聊天 UI projection，并生成 Environment notification；DispatchSubscriber 再把 notification 投递到 Queue Session Coordinator。
- **通知派发**：在这里甚至可以结合特定的状态字段直接改变前端某个浮层的开关或者全局变量下发。
