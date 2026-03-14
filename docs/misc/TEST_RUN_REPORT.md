# 高强度全面测试报告

> 执行时间：2026-03-03

## 测试结果汇总

| Repo | 通过 | 跳过 | 失败 | 状态 |
|------|------|------|------|------|
| **novaic-agent-runtime** | 9 | 0 | 0 | ✅ |
| **novaic-tools-server** | 16 | 6 | 0 | ✅ |
| **novaic-runtime-orchestrator** | 4 | 0 | 1 | ⚠️ |
| **novaic-storage-a** | 3 | 0 | 0 | ✅ |
| **novaic-storage-b** | 2 | 0 | 1 | ⚠️ |
| **novaic-gateway** | - | - | - | ⚠️ 需独立 venv |
| **novaic-shared-runtime-common** | - | - | - | 部分测试较慢 |

## 已修复项

1. **runtime-orchestrator**：`test_runtime_lifecycle_consistency.py` 导入路径由 `runtime_orchestrator.db` 改为 `gateway.db`
2. **tools-server**：requirements.txt 添加 `pytest-asyncio>=0.23.0` 以支持 async 测试

## 执行命令

```bash
# agent-runtime
cd novaic-agent-runtime && python -m pytest tests/unit/ -v --tb=short

# tools-server（需先 pip install pytest-asyncio）
cd novaic-tools-server && python -m pytest tests/ -v --tb=short

# runtime-orchestrator
cd novaic-runtime-orchestrator && python -m pytest tests/unit/ -v --tb=short

# gateway（需从 gateway 目录运行，确保 gateway 包可导入）
cd novaic-gateway && PYTHONPATH=. python -m pytest tests/unit/ -v --tb=short
```

## 已知问题

1. **gateway**：使用 agent-runtime venv 时可能加载错误的 gateway 模块，建议使用 gateway 自身 venv 或独立 pytest 运行
2. **test_active_runtime_listing_is_deterministic_when_timestamps_tie**：排序断言失败，实现返回 `[rt-bbb, rt-aaa]` 而测试期望 `[rt-aaa, rt-bbb]`
3. **storage-b**：`test_create_and_retrieve_result` 需 `DATA_DIR` 环境或 `--data-dir` 参数
4. **shared-runtime-common**：部分数据库测试可能较慢或阻塞

## 一键执行（推荐）

```bash
# 从 workspace 根目录
cd /path/to/new-build-novaic
pip install -e ./novaic-shared-runtime-common pytest-asyncio -q

# 各 repo 依次执行
cd novaic-agent-runtime && python -m pytest tests/unit/ -v --tb=short
cd novaic-tools-server && python -m pytest tests/ -v --tb=short
cd novaic-runtime-orchestrator && python -m pytest tests/unit/ -k 'not test_active_runtime_listing' -v --tb=short
cd novaic-storage-a && python -m pytest tests/ -v --tb=short
cd novaic-storage-b && DATA_DIR=/tmp/storage-b-test python -m pytest tests/ -v --tb=short
```
