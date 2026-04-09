# Schema 与 Cascade 推送下发机制

> 路径参考：`novaic-gateway/gateway/entity/entangled_bridge.py` 与 `Entangled/packages/server-python/entangled/server/notifier.py`

## 1. Cascade 自动级联清理与装配
你不再需要建立传统关系型数据库那种重型且不可逆向迁移的 Foreign Key Constraint（外键强依）。
利用在各业务代码里在初始化实体列表赋予时的 `EntityRelation`；在网关桥接文件内，通过 `_build_relations` 方法：
- 它会通过检查每个实体的定义的 `parent` 参数属性；
- 当找到一个属于别人的父节点，桥接会主动倒过去反推，给对应的 `parent_def.relations` 挂上：如果有一天我被删除了，请也清理依赖我的某某子项。

## 2. 智慧的主动推送树建立 (First-Schema Push)
如果前端需要分别为了获得当前的 agent 再发送一个包订阅它所有的 tool/log，通信会极度阻塞。Entangled 在连接创建开始的一瞬间解决此事。
- **下发 Schema**:
    服务端解析出 `capabilities` 且带着它所有拥有属性的信息，随附第一个报文发送给打通 WebSocket 的网关信道。这宣告了后端的同步约定和处理阈值极限。
- **Cascade Subscription (服务端代理订阅)**:
    不再依赖前端发出 `subscribe A, and then subscribe B, C`；当网关 WebSocket 解析了一个发来的 `subscribe A`：如果发现 `A` 的业务表名有 `subscription_cascade=(B, C)`；服务端会代打请求。
    网关此时会直接向底仓查询这 3 张表的全量及偏移拉取，随后打包一股脑把所有必须组件的数据一同塞入 Push WebSocket 信道下发给客户端。客户端只用挂着听。
