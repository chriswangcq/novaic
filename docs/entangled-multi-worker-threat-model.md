# 多 worker / 推送隔离 — 威胁模型摘要（D.1）

> 阶段 4 前置思考；单进程 NovAIC 默认假设下风险可控，但需显式记录。

## 资产

- **用户数据**：各 `user_id` 的实体与同步帧。
- **通道**：App WebSocket（JWT `sub` = `user_id`）、进程内 Entangled `SyncRegistry` + `notifier`。

## 威胁

| ID | 场景 | 单进程现状 | 多 worker / 总线 |
|----|------|------------|------------------|
| T1 | 错误地把用户 A 的变更推给用户 B | `push_to_user` / `get_subscribed_clients` 以订阅与 registry 为界；须保证 subscribe 时鉴权与 params 一致 | 必须 **粘性会话** 或 **共享总线 + 连接表**，否则推送可能落错 FD |
| T2 | 伪造 `X-User-ID` 冒充 | Gateway App WS 已拒绝与 JWT `sub` 不一致的 header | 同左 |
| T3 | 广播风暴 | `notify_all` / 级联深度已加 **深度上限**（notifier）| 总线 topic 需按租户/用户分区 |

## 控制措施（已部分落地）

- JWT 为唯一用户身份（App WS）。
- 级联 `_MAX_CASCADE_DEPTH` 防止关系图失控。
- 出站推送队列分级（ADR-4）减轻单连接洪泛对 sync 的影响。

## 残留

- 多实例 **未** 在本仓库实现 Redis/NATS；上线前补 **Runbook** 与双 worker 冒烟（阶段 D.2）。
