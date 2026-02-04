# Queue Service 部署指南

## 🚀 快速开始

### 1. 环境准备

```bash
# 设置数据目录
export NOVAIC_DATA_DIR=~/.novaic

# 确保目录存在
mkdir -p $NOVAIC_DATA_DIR
```

### 2. 启动 Queue Service

```bash
cd novaic-backend
./start_queue_service.sh
```

或直接运行：

```bash
cd novaic-backend
python3 -m queue_service.main
```

### 3. 验证服务

```bash
# 健康检查
curl http://127.0.0.1:19997/health

# 查看服务信息
curl http://127.0.0.1:19997/
```

---

## 📊 完整部署流程

### 步骤 1：更新 Worker 配置

修改所有 Worker 文件，将连接 URL 从 Gateway 改为 Queue Service：

```python
# novaic-backend/task_queue/workers/task_worker_sync.py
# novaic-backend/task_queue/workers/saga_worker_sync.py
# novaic-backend/task_queue/workers/health_worker_sync.py

# 从
client = TaskQueueClient("http://127.0.0.1:19999")
saga_client = SagaClient("http://127.0.0.1:19999")

# 改为
client = TaskQueueClient("http://127.0.0.1:19997")
saga_client = SagaClient("http://127.0.0.1:19997")
```

### 步骤 2：启动服务

```bash
# 终端 1：启动 Gateway
export NOVAIC_DATA_DIR=~/.novaic
cd novaic-backend
python3 main_gateway.py

# 终端 2：启动 Queue Service
export NOVAIC_DATA_DIR=~/.novaic
cd novaic-backend
python3 -m queue_service.main

# 终端 3：启动 Workers
export NOVAIC_DATA_DIR=~/.novaic
cd novaic-backend
python3 -m task_queue.workers.task_worker_sync 1
python3 -m task_queue.workers.saga_worker_sync 1
python3 -m task_queue.workers.health_worker_sync
```

### 步骤 3：测试验证

```bash
cd novaic
python3 test_queue_service.py
```

---

## 🔧 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NOVAIC_DATA_DIR` | 数据目录（必需） | - |
| `QUEUE_SERVICE_PORT` | 服务端口 | 19997 |

### 数据库配置

数据库位置：`$NOVAIC_DATA_DIR/queue.db`

PRAGMA 配置（已优化）：
- `journal_mode = WAL` - 并发读写
- `synchronous = NORMAL` - 性能优化
- `busy_timeout = 5000` - 锁等待 5 秒
- `foreign_keys = OFF` - Queue 表无外键

---

## 📈 监控和维护

### 查看日志

```bash
# 查看实时日志
tail -f $NOVAIC_DATA_DIR/logs/queue-service-$(date +%Y%m%d).log

# 搜索错误
grep ERROR $NOVAIC_DATA_DIR/logs/queue-service-*.log

# 搜索警告
grep WARNING $NOVAIC_DATA_DIR/logs/queue-service-*.log
```

### 查看数据库

```bash
# 连接数据库
sqlite3 $NOVAIC_DATA_DIR/queue.db

# 查看任务统计
SELECT status, COUNT(*) as count FROM tq_tasks GROUP BY status;

# 查看 Saga 统计
SELECT status, COUNT(*) as count FROM tq_sagas GROUP BY status;

# 查看待处理任务
SELECT id, topic, status, created_at FROM tq_tasks 
WHERE status = 'pending' 
ORDER BY created_at 
LIMIT 10;

# 查看运行中的 Saga
SELECT id, saga_type, status, created_at FROM tq_sagas 
WHERE status = 'running' 
ORDER BY created_at;
```

### 性能监控

```bash
# 查看数据库大小
du -h $NOVAIC_DATA_DIR/queue.db

# 查看 WAL 文件
ls -lh $NOVAIC_DATA_DIR/queue.db-*

# VACUUM（定期整理）
sqlite3 $NOVAIC_DATA_DIR/queue.db "VACUUM;"
```

---

## 🧹 数据清理

### 清理完成的任务

```bash
sqlite3 $NOVAIC_DATA_DIR/queue.db <<EOF
DELETE FROM tq_tasks 
WHERE status IN ('done', 'failed') 
  AND finished_at < datetime('now', '-2 days');
EOF
```

### 清理完成的 Saga

```bash
sqlite3 $NOVAIC_DATA_DIR/queue.db <<EOF
DELETE FROM tq_sagas 
WHERE status IN ('completed', 'failed')
  AND completed_at < datetime('now', '-7 days');
EOF
```

### 自动清理脚本

```bash
#!/bin/bash
# cleanup_queue.sh

export NOVAIC_DATA_DIR=~/.novaic

# 清理 2 天前的任务
sqlite3 $NOVAIC_DATA_DIR/queue.db <<EOF
DELETE FROM tq_tasks 
WHERE status IN ('done', 'failed') 
  AND finished_at < datetime('now', '-2 days');
EOF

# 清理 7 天前的 Saga
sqlite3 $NOVAIC_DATA_DIR/queue.db <<EOF
DELETE FROM tq_sagas 
WHERE status IN ('completed', 'failed')
  AND completed_at < datetime('now', '-7 days');
EOF

# VACUUM
sqlite3 $NOVAIC_DATA_DIR/queue.db "VACUUM;"

echo "✅ Cleanup complete"
```

添加到 crontab：

```bash
# 每天凌晨 2 点清理
0 2 * * * /path/to/cleanup_queue.sh
```

---

## 🔄 升级和迁移

### 从共享数据库迁移

1. **备份现有数据**：

```bash
sqlite3 $NOVAIC_DATA_DIR/novaic.db <<EOF
.output /tmp/tq_tasks_backup.sql
.dump tq_tasks
.output /tmp/tq_sagas_backup.sql
.dump tq_sagas
EOF
```

2. **启动 Queue Service**（自动创建 queue.db）

3. **迁移数据**（可选）：

```bash
# 仅迁移待处理的任务
sqlite3 $NOVAIC_DATA_DIR/novaic.db <<EOF
.mode insert tq_tasks
SELECT * FROM tq_tasks WHERE status IN ('pending', 'claimed');
EOF > /tmp/pending_tasks.sql

sqlite3 $NOVAIC_DATA_DIR/queue.db < /tmp/pending_tasks.sql
```

### 数据库升级

Schema 版本会自动升级。如需手动升级：

```python
from queue_service.db import Database, init_schema

db = Database("/path/to/queue.db")
db.connect()
# init_schema 会自动检测版本并升级
```

---

## 🐛 故障排查

### 服务无法启动

**问题**：`NOVAIC_DATA_DIR not set`

**解决**：
```bash
export NOVAIC_DATA_DIR=~/.novaic
```

**问题**：`Address already in use`

**解决**：
```bash
# 查找占用端口的进程
lsof -i :19997

# 杀死进程
kill -9 <PID>
```

### 数据库锁定

**问题**：`database is locked`

**解决**：
1. 检查是否有多个 Queue Service 实例
2. 检查 WAL 模式是否启用：
   ```bash
   sqlite3 $NOVAIC_DATA_DIR/queue.db "PRAGMA journal_mode;"
   # 应该返回 wal
   ```
3. 清理 WAL 文件：
   ```bash
   rm $NOVAIC_DATA_DIR/queue.db-wal
   rm $NOVAIC_DATA_DIR/queue.db-shm
   ```

### Workers 连接失败

**问题**：Workers 仍连接到 Gateway (19999)

**解决**：确认 Workers 配置已更新：
```python
# 应该是
client = TaskQueueClient("http://127.0.0.1:19997")
```

### 性能问题

**问题**：任务处理延迟高

**解决**：
1. 检查数据库大小：
   ```bash
   du -h $NOVAIC_DATA_DIR/queue.db
   ```
2. 运行 VACUUM：
   ```bash
   sqlite3 $NOVAIC_DATA_DIR/queue.db "VACUUM;"
   ```
3. 清理旧数据（见上文）

---

## 📝 系统集成

### systemd 服务（Linux）

创建 `/etc/systemd/system/queue-service.service`：

```ini
[Unit]
Description=NovAIC Queue Service
After=network.target

[Service]
Type=simple
User=novaic
WorkingDirectory=/opt/novaic/novaic-backend
Environment="NOVAIC_DATA_DIR=/var/lib/novaic"
Environment="QUEUE_SERVICE_PORT=19997"
ExecStart=/usr/bin/python3 -m queue_service.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable queue-service
sudo systemctl start queue-service
sudo systemctl status queue-service
```

### Docker 部署

创建 `Dockerfile.queue-service`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY novaic-backend/queue_service ./queue_service
COPY novaic-backend/requirements.txt ./

RUN pip install -r requirements.txt

ENV NOVAIC_DATA_DIR=/data
ENV QUEUE_SERVICE_PORT=19997

VOLUME ["/data"]

EXPOSE 19997

CMD ["python", "-m", "queue_service.main"]
```

构建和运行：

```bash
docker build -f Dockerfile.queue-service -t queue-service:latest .

docker run -d \
  --name queue-service \
  -p 19997:19997 \
  -v ~/.novaic:/data \
  -e NOVAIC_DATA_DIR=/data \
  queue-service:latest
```

---

## 📞 支持

如有问题，请查看：

- 📖 README: `novaic-backend/queue_service/README.md`
- 📋 迁移指南: `QUEUE_SERVICE_MIGRATION.md`
- 🧪 测试脚本: `test_queue_service.py`
- 📝 日志: `$NOVAIC_DATA_DIR/logs/queue-service-*.log`
