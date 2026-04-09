# 存储与表声明层：SqlEntityStore

> 路径参考：`Entangled/packages/server-python/entangled/sql/`

## 1. 自动映射实体防御与约束 (`EntityDef`)
与传统的 ORM `SQLAlchemy` 或 `Django` 的大包大揽不同，在 Entangled 只有极简的面向实体数据的数据属性声明模型。我们直接提供一个 JSON dict 到 `EntityDef` 转换的快速管线。
- 你可以直接通过在子类赋予 `FieldDef` 来强制类型并进行数据校验。
- 允许通过属性自动推断出这个 Entity 的 `sync_type`(`list` / `stream`)。
- 当有 JSON 类型要求时，会在 Python 的字典到 SQL 的序列化（Serde）提供隐式无缝转化，直接进出 SQLite 的 `TEXT` 并透明地解析还原。

## 2. Server-side SQLite 并发调度与 WAL (`Database` & `Locks`)
由于 Python 著名的全局解释锁以及 SQLite 有著名的并发大写入时可能遭到 `database is locked` 报错：
- 采用双轨的 Async Thread Pool 隔离：`database.py` 中所有的执行其实是被委托进单独写向事务中的 Worker。
- `locks.py` 使用了互斥与读写锁管理对同一对象的并发读写操作，并在后台启动了 WAL（Write-Ahead Logging）模式优化：使得读查询能在被后台执行密集写入或者 `DELETE` 吸储时不受任何阻塞。

## 3. Cursor Streaming 与 CRUD 接口
`SqlEntityStore` 暴露完整的核心方法。但针对实时 IM 通道必须的高速拉流查询（翻阅 1 万条消息里的前面 50 条历史）：
- 我们拥有内部实现的智能偏移动态 Cursor `list_stream`。
- 时间戳结合降序/升序查找 O(log N) 的速度获取 `head_n` 窗口。这恰巧填上了因为删掉了前端 `Dexie` IndexedDB 之后查询大量列表导致崩溃的技术空白，把这压力从前端安全交由后端 Sqlite。
