# 服务 URL 硬编码问题修复总结

## 修复日期
2026-02-05

## 问题描述
Gateway URL、Queue Service URL、Tools Server URL 在多处硬编码，导致多环境部署困难。

## 修复内容

### 1. 创建统一配置模块 ✅

**文件**: `novaic-backend/common/config.py`

创建了 `ServiceConfig` 类，包含：
- **Gateway 配置**: HOST, PORT, URL
- **Queue Service 配置**: HOST, PORT, URL  
- **Tools Server 配置**: HOST, PORT, URL
- **超时配置**: TASK_TIMEOUT, SAGA_TIMEOUT, SAGA_STEP_TIMEOUT, HTTP_TIMEOUT
- **间隔配置**: HEARTBEAT_INTERVAL, POLL_INTERVAL
- **并发配置**: NUM_WORKERS, MAX_CONCURRENT_SAGAS
- **配置验证**: `validate()` 方法验证所有配置的有效性

所有配置支持环境变量覆盖，默认值保持向后兼容。

### 2. 修改的文件列表 ✅

#### A. 主入口文件
1. **main_novaic.py**
   - 添加配置导入
   - 在 `main()` 函数开始处添加配置验证和日志输出
   - 替换所有硬编码的端口和 URL 默认值 (7 处)

2. **main_task.py**
   - 添加配置导入
   - 替换硬编码的 URL 和并发配置 (3 处)

3. **main_saga.py**
   - 添加配置导入
   - 替换硬编码的 URL 和并发配置 (4 处)

#### B. Worker 组件
4. **task_queue/workers/task_worker_sync.py**
   - 添加配置导入
   - 修改 `__init__` 方法使用配置 (4 处)
   - 修改 `start_worker` 和 `start_multiple_workers` 函数 (2 处)
   - 修改 `__main__` 部分 (3 处)

5. **task_queue/workers/saga_worker_sync.py**
   - 添加配置导入
   - 修改 `__init__` 方法使用配置 (6 处)
   - 修改 `start_worker` 函数 (4 处)
   - 修改 `__main__` 部分 (3 处)

6. **task_queue/workers/watchdog_sync.py**
   - 添加配置导入
   - 修改 `__init__` 方法使用配置 (4 处)
   - 修改 `start_worker` 函数和命令行参数 (6 处)

7. **task_queue/workers/watchdog.py**
   - 添加配置导入
   - 修改 `__init__` 方法使用配置 (4 处)

8. **task_queue/workers/health_worker_sync.py**
   - 添加配置导入
   - 修改 `__init__` 方法使用配置 (1 处)
   - 修改 `__main__` 部分 (1 处)

9. **task_queue/workers/__init__.py**
   - 更新文档示例，使用默认配置

#### C. Handler 组件
10. **task_queue/handlers/llm_handlers.py**
    - 添加配置导入
    - 替换所有 gateway_url 和 tools_server_url 的硬编码 (4 处)

11. **task_queue/handlers/summary_handlers.py**
    - 添加配置导入
    - 替换所有 gateway_url 的硬编码 (3 处)

#### D. 客户端和业务逻辑
12. **task_queue/client.py**
    - 添加配置导入
    - 替换所有 tools_server_url 的硬编码 (4 处)

13. **task_queue/business/mcp.py**
    - 添加配置导入
    - 替换所有 tools_server_url 的硬编码 (2 处)

14. **gateway/api/agents.py**
    - 添加配置导入
    - 替换所有 tools_server_url 的硬编码 (2 处)

### 3. 修改统计

- **文件总数**: 15 个文件
- **硬编码位置**: 约 60+ 处
- **导入添加**: 14 处
- **配置替换**: 60+ 处

### 4. 验证结果 ✅

#### 语法检查
所有修改的文件通过了 Python 语法检查：
```bash
✅ common/config.py
✅ main_novaic.py, main_task.py, main_saga.py
✅ task_queue/workers/*.py (5 个文件)
✅ task_queue/handlers/*.py (2 个文件)
✅ task_queue/client.py
✅ task_queue/business/mcp.py
✅ gateway/api/agents.py
```

#### 配置验证
配置模块验证通过：
```
Config validation passed
Gateway URL: http://127.0.0.1:19999
Queue Service URL: http://127.0.0.1:19997
Tools Server URL: http://127.0.0.1:19998
```

### 5. 环境变量支持

现在支持以下环境变量覆盖默认配置：

```bash
# Gateway
GATEWAY_HOST=127.0.0.1
GATEWAY_PORT=19999
GATEWAY_URL=http://127.0.0.1:19999

# Queue Service
QUEUE_SERVICE_HOST=127.0.0.1
QUEUE_SERVICE_PORT=19997
QUEUE_SERVICE_URL=http://127.0.0.1:19997

# Tools Server
TOOLS_SERVER_HOST=127.0.0.1
TOOLS_SERVER_PORT=19998
TOOLS_SERVER_URL=http://127.0.0.1:19998

# Timeouts
TASK_TIMEOUT=60
SAGA_TIMEOUT=120
SAGA_STEP_TIMEOUT=300
HTTP_TIMEOUT=30.0

# Intervals
HEARTBEAT_INTERVAL=10.0
POLL_INTERVAL=0.1

# Concurrency
NUM_WORKERS=5
MAX_CONCURRENT_SAGAS=10
```

### 6. 向后兼容性

- ✅ 所有默认值保持不变
- ✅ 现有代码无需修改即可运行
- ✅ 环境变量覆盖机制完全兼容现有部署
- ✅ 启动日志输出配置信息，便于验证

### 7. 配置验证机制

启动时自动验证配置：
- ✅ 端口范围检查 (1024-65535)
- ✅ 超时值检查 (> 0)
- ✅ 间隔值检查 (> 0)
- ✅ 并发值检查 (> 0)
- ✅ 配置错误时打印详细错误信息并退出

### 8. 下一步建议

1. **文档更新**: 更新部署文档，说明新的环境变量配置方式
2. **配置文件**: 可选地添加 `.env` 文件支持
3. **配置中心**: 未来可扩展为从配置中心读取配置
4. **监控指标**: 将配置信息添加到监控指标中

## 修复完成 ✅

所有硬编码问题已修复，配置统一管理，支持多环境部署。
