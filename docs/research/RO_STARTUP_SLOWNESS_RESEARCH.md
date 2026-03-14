# RO 启动慢问题研究

> 2025-03 基于 main_runtime_orchestrator.py 与 gateway/db 分析

---

## 一、启动流程

```
uvicorn.run(app) 
  → lifespan 开始
    → Path(DATA_DIR).mkdir()
    → init_database(data_dir, RUNTIME_ORCHESTRATOR_DB_FILE)
        → get_db() → Database.connect(init_schema_func=init_schema_sync)
            → init_schema_sync(conn)
                → 解析 SCHEMA_SQL，创建表
                → run_migration_sync(conn, current_version)  # v0→v40
                → 创建索引
    → run_migration(db)
        → migrate_config(db, data_dir)
        → migrate_agents(db, data_dir)
        → migrate_sessions(db, data_dir)
        → migrate_add_foreign_keys(db)  # 有 bug，db.conn 不存在
  → lifespan 结束，Uvicorn 开始监听
  → /api/health 可访问
```

**关键**：`/api/health` 只有在 lifespan 完成后才可访问。lifespan 内所有步骤都是阻塞的。

---

## 二、潜在瓶颈

### 2.1 init_schema_sync（init_database 内）

| 步骤 | 耗时来源 |
|------|----------|
| 解析 SCHEMA_SQL | 大字符串 split，循环执行每条语句 |
| CREATE TABLE | 约 30+ 张表，每条 `conn.execute` |
| run_migration_sync | 若 current_version=0，执行 v21→v40 共 20 个迁移 |
| v37 _migrate_android_config | 遍历所有 agents，逐行 UPDATE |
| v38 _migrate_to_devices | 遍历 agents，创建 devices 表并插入 |
| CREATE INDEX | 约 40+ 个索引 |

**估算**：新库或大版本升级时，完整跑完约 1–5 秒，视数据量而定。

### 2.2 run_migration（gateway/db/migration.py）

| 步骤 | 耗时来源 |
|------|----------|
| migrate_config | `_candidate_config_paths` 检查 8+ 个路径；读取 JSON；批量 INSERT |
| migrate_agents | 若存在 agents.json，读取并逐 agent INSERT |
| migrate_sessions | **最可能慢**：`sessions/*.jsonl` 每个文件逐行 `json.loads` + INSERT |
| migrate_add_foreign_keys | 使用 `db.conn`，Database 无此属性 → 抛错，但 migration 继续 |

**migrate_sessions 典型耗时**：
- 每个 session 文件：读文件 + 逐行解析 + 逐行 INSERT
- 100 个 session 文件 × 每文件 100 行 ≈ 10000 次 INSERT
- 无批量 INSERT，每次 `db.execute` 单独提交（在 transaction 内会好一些）

### 2.3 Python 导入链

```
main_runtime_orchestrator
  → common.config (可能读 config 文件)
  → gateway.api.internal (runtime + subagent router)
    → gateway.db.access, gateway.db.repositories
    → common.enums, common.config
  → gateway.db (init_database, run_migration)
    → gateway.db.schema (1400+ 行)
    → gateway.db.migration (390+ 行)
```

首次 import 会加载上述模块，冷启动约 0.5–2 秒。

### 2.4 与 Gateway 的竞争

RO 与 Gateway 共用 `data_dir`，但使用不同 DB 文件：
- RO: `runtime_orchestrator.db`
- Gateway: `gateway.db`

两者都会读 `config.json`、`agents.json`、`sessions/`。若同时启动，可能产生：
- 磁盘 I/O 竞争
- 若存在文件锁，可能互相等待

### 2.5 migrate_add_foreign_keys 的 Bug

```python
# migration.py:345
cursor = db.conn.execute("PRAGMA foreign_key_list(chat_messages)")
```

`Database`（shared_runtime_common）没有 `conn` 属性，连接在 `_get_thread_connection()` 的 `_local.conn` 中。

**结果**：`AttributeError: 'Database' object has no attribute 'conn'`，被 `except` 捕获，返回 False，不影响整体流程，但会打 error 日志。

---

## 三、优化建议

### P0：修复 migrate_add_foreign_keys

使用 `db.get_connection()` 或 `db.transaction()` 获取连接，而不是 `db.conn`：

```python
def migrate_add_foreign_keys(db: Database) -> bool:
    try:
        with db.get_connection("global") as ctx:
            conn = ctx._get_thread_connection()  # 或暴露 conn 的 API
            cursor = conn.execute("PRAGMA foreign_key_list(chat_messages)")
            ...
```

或为 `Database` 增加 `conn` 属性 / 方法供 migration 使用。

### P1：migrate_sessions 批量插入

当前逐行 `db.execute`，可改为 `executemany` 或每 N 行 commit 一次，减少事务与锁开销。

### P2：RO 是否必须跑完整 migration

RO 的 `runtime_orchestrator.db` 主要存 runtimes、subagents。`migrate_config`、`migrate_agents`、`migrate_sessions` 来自 legacy 文件迁移，RO 可能不需要：

- 若 RO 不依赖 config/agents/sessions 表，可跳过这些 migration
- 需确认 RO 的 schema 与 Gateway 的差异，以及 RO 实际用到的表

### P3：延迟 migration

将 `run_migration` 移到 lifespan 之后、在后台任务中执行，使 `/api/health` 尽快可用。风险是首请求若依赖 migration 结果可能失败，需评估。

### P4：并行启动下的顺序

若 RO 与 Gateway 同时启动且都做重 migration，可考虑：
- 让 RO 先启动（当前 main.rs 已是 RO 先 spawn）
- 或错开 migration：RO 只做 schema init，不做 file-based migration

---

## 四、启动耗时日志（已接入）

已添加 `time.perf_counter()` 计时，启动后查看日志即可定位瓶颈。

### RO (main_runtime_orchestrator.py)

- `[RO] Startup: mkdir=X.XXs init_db=X.XXs total=X.XXs` — lifespan 内各步骤
- `[RO] Import+parse took X.XXs before uvicorn` — 模块导入与解析

### Gateway (main_gateway.py)

- `[Gateway] migrate_old_data took X.XXs` — 模块加载时迁移
- `[Gateway] Database initialized: ... (took X.XXs)` — init_database
- `[Gateway] load_config took X.XXs` — 配置加载
- `[Gateway] initialize_systems took X.XXs` — 系统初始化
- `[Gateway] get_agent_config+list_agents took X.XXs` — 代理配置
- `[Gateway] TaskManager initialized (took X.XXs)` — TaskManager
- `[Gateway] MessageRepository and AgentStateRepository initialized (took X.XXs)` — 仓储
- `[Gateway] VM process recovery complete (took X.XXs)` — VM 恢复
- `[Gateway] Worker SSE broadcaster initialized (took X.XXs)` — SSE
- `[Gateway] Lifespan startup total: X.XXs` — lifespan 总耗时

### Tauri (main.rs)

- `[Startup] Cleanup took Xs` — 僵尸进程清理
- `[Startup] Phase 1 (spawn all services) took Xs` — 顺序启动 7 个服务
- `[Services] All services ready (health checks took Xs)` — 并发健康检查
- `[Startup] Total before workers: Xs` — 启动 Workers 前总耗时

### 日志位置（均写入文件，不输出控制台）

- Gateway: `$NOVAIC_DATA_DIR/logs/gateway-YYYYMMDD.log`
- RO: `$NOVAIC_DATA_DIR/logs/runtime-orchestrator-YYYYMMDD.log`
- Tauri 启动诊断: `$NOVAIC_DATA_DIR/logs/startup-diagnostics.jsonl`（含 cleanup-duration、phase1-duration、phase2-health-duration、total-before-workers 等）

---

## 五、结论

| 因素 | 影响 | 优先级 |
|------|------|--------|
| migrate_sessions 逐行 INSERT | 高（session 多时） | P1 |
| migrate_add_foreign_keys 使用 db.conn | 报错，无性能影响 | P0 修复 |
| init_schema_sync + run_migration_sync | 中（新库或大版本升级） | P2 |
| Python 导入 | 低–中 | - |
| 与 Gateway 竞争 I/O | 中（并行启动时） | P4 |

建议先加计时日志确认瓶颈，再按上表优先级优化。
