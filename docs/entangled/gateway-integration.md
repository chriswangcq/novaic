# 网关端的深度融合集成 (Gateway Integration)

> 路径参考：`novaic-gateway/gateway/entity/store.py`

## 1. 从隔离双层架构到直接继承
在早期的重构阶段，`novaic-gateway` 自己手写了一整套由大量 SQL CRUD 以及 `EntityStore` 原语构成的近两千行类库，然后再通过一个中层胶水闭包抛回给 `Entangled` 判定更新情况。这样的双层结构不仅庞大且难于演进表结构。

通过完全融入 `entangled.sql` 这个基础设层后，`Gateway` 代码体量锐减：
```python
# 现在，Gateway 自身就是 Entangled 的一个衍生数据库存储层实现
from entangled.sql import SqlEntityStore

class GatewayEntityStore(SqlEntityStore):
    def __init__(self, db, defs, runtime, vmuse_mgr):
        super().__init__(db, defs)
        self.runtime = runtime 
```

## 2. Before / After 自定义拦阻 Hook 的实现
既然表单的操作都进入了父类的包里边，Gateway 需要在这时候安插大量的 NovAIC 专供业务：例如当我们下发了一台虚拟机的开机或销毁；或我们新来了一条聊天消息。

我们覆写了生命周期的钩子（Hook）：
- **`before_insert` / `before_update`**:
    执行像 `_generate_nanoid_for_agent` 这样的动态自增，或是遇到 `EntityId="device"` 的新建，进行向远程发送开启 `VMPrep` 打通云端准备指令的任务分配。
- **`after_insert`**:
    针对 `messages`（系统和聊天的主要事件通信）。Gateway 使用此钩子将 `sending` 的请求直接打包推送到 `watchdog`，或是将新创建的请求用它独有的 Queue Service 以 saga 的形式推去跑后续流水。

所有的这些逻辑不再充斥于各种零散的 REST Controller 端点，业务控制的强绑定和实体模型的持久化完成了统一。
