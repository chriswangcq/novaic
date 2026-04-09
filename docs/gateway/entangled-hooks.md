# Entangled 的定制切面：业务 Hook 实现

> 路径参考：`novaic-gateway/gateway/entity/store.py` 和 `gateway/entity/defs.py`

## 1. 从数据模型到行为声明 (`defs.py`)
所有的业务对象的长相（属性名字/长度等），全部脱离 SQL DDL，集中用 Python 代码表达在 `gateway/entity/defs.py` 内（例如：`AGENT_TOOLS`, `SKILLS`, `MESSAGES`）。
这些表述不是死的数据，它们带有能力与级联指令：
```python
# 例如声明级联更新：
subscription_cascade = ["tool_logs", "agent_tools"]
```
如果新增这其中的行为被变动，提供给 UI 生成代码包的前置指令也会被同步更新，保证前后端数据类型 `TypeScript <-> Python` 的彻底对齐（参考：`scripts/generate_entity_types.py` 工具）。

## 2. 操作阻截：Before / After Hooks
网关作为唯一直接处理各种新创建对象流经的口子。通过将自己派生为 `GatewayEntityStore(SqlEntityStore)`，其最大的工作集中于针对不同 Entity 执行干预方法。

### `before_` 系钩子（动作前的篡改与检查）：
- **拦截检查型**：你可以借此拦下越权操作（虽然底层其实自动补了 user_id）。
- **生成型：Nanoid**：在过去是由客户端生成乱码 ID 发送。但网关现在会在插入动作被抛进 Sqlite 的最后一刻前：为新的 Agent、Session 或其它需要优雅短串记录生成可读又安全的随机名（例如给某虚拟机的名字上个 NanoId 避免碰撞冲突）。

### `after_` 系钩子（旁路与异步投递的扳机）：
- **启动任务 (`messages` 为例)**：当用户从对话列表里发出一句请求，它落到了网关的数据库。通过捕获这条 `after_insert`，网关触发判断如果这是来自某个处于开启状态机器的人的消息，它将可能直接通知正在睡梦的队列唤醒对应的系统，或只是留在这里并等随后的 watchdog 来扫盘将其带进运行时进程的流水线。
- **通知派发**：在这里甚至可以结合特定的状态字段直接改变前端某个浮层的开关或者全局变量下发。
