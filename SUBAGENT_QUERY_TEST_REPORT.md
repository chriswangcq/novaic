# subagent_query 功能测试报告

**测试日期**: 2026-02-13  
**测试范围**: Main SubAgent 查询 Sub SubAgent 状态 (subagent_query)

---

## 1. 环境准备

### 1.1 服务运行状态

| 服务 | 状态 | 端口/路径 |
|------|------|-----------|
| Gateway (main_gateway.py) | 运行中 | localhost:19999 |
| Queue Service | 运行中 | localhost:19997 |
| Tools Server (main_tools.py) | 运行中 | localhost:19998 |

### 1.2 数据库路径

- **主数据库**: `/Users/wangchaoqun/Library/Application Support/com.novaic.app/novaic.db`

### 1.3 现有 SubAgent 数据

```bash
sqlite3 ".../novaic.db" "SELECT subagent_id, agent_id, type, status, task, result FROM subagents LIMIT 10;"
```

---

## 2. API 定义

- **端点**: `GET /internal/rt/{runtime_id}/subagent/{target_subagent_id}/status`
- **文件**: novaic-backend/gateway/api/internal/runtime.py

### 响应字段

- subagent_id, status, completed, progress, result, error, runtime_id, runtime_status

---

## 3. 测试结果

| 场景 | 结果 |
|------|------|
| 查询 Main SubAgent (main-56d7ec79) | 通过 |
| 查询 Sub SubAgent (sub-test123456) | 通过 |
| 查询不存在的 SubAgent | 404 正确返回 |

### 测试命令

```bash
# 查询 Main SubAgent
curl -s "http://localhost:19999/internal/rt/rt-a17b262b4031/subagent/main-56d7ec79/status"

# 查询 Sub SubAgent（需先插入测试数据）
curl -s "http://localhost:19999/internal/rt/rt-a17b262b4031/subagent/sub-test123456/status"
```

---

## 4. 注意事项

- subagent_spawn 当前返回 500，需单独调试
- 工具 schema 使用 target_subagent_id，executor 读取 subagent_id，建议统一
