# 表消融时代：v63 数据库剥离详解

> 路径参考：`novaic-gateway/gateway/db/schema.py` 及内部 Repository 目录。

## 1. Schema v63 的历史巨变
在非常早期的版本里，哪怕是作为实时的聊天消息（Messages）或者是客户端列表中的所有子插件参数，全部都有一份属于自己的 SQLAlchemy Model（通过传统的 Alembic 控制迁移并在 `gateway.db` 中生成巨大的字段山）。

自完成从传统关系架构转向 Entangled 实体的全面革命：以 **Schema v63** 更新补丁为分水岭，系统经历了恐怖的“删库行动”：
- **大量 DROP TABLES**：
  曾经横陈满图的 `chat_messages`, `agents`, `subagents`, `agent_binding` 或者诸如此类和运行时刻及本地 UI 生命周期强相关一切数据表都从 `gateway.db` 当中被强制 **DROP**（删除）清除出境。
- **转移管辖**：
  它们全都被迁入了挂靠在 Entangled SQL 的底层 sqlite 中，因为那些表具备自动按照模型推导的功能及强大的 Json 层化包容特性，不再产生庞杂的关系键定义。

## 2. 残留的护城河（保留于原生 Database 的内容）
那么传统的 `gateway.db` 以及与其捆绑的常规 `repositories` （像是 `UserRepository` 等）还留些啥？
这些留下的被称为“非强实时相关的**基础设施运维与隔离数据**”：
- **`users`** 用户全局表（管理了密码、注册源等全局凭证）。
- **`user_quotas` / `config` 等控制平面表**（涉及到各种额度的配发或者全站级的统计，它们根本无需进入用户的对话 WebSocket 下发进行推送）。

这种剥离带来了极好的业务界限：“凡是对用户操作台强交互引起反馈重绘且具备树级流水的——均在 Entangled 维护；凡是为了保护这台服务器运行下去和控制金钱配额的——留在 `gateway.db`”。
