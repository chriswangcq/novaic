# 部署与进程启动

> 源码：`novaic_cortex/main_cortex.py`；应用对象来自 **`api.app`**（`set_registry` / `set_proxy`）。

## 1. 如何启动

```bash
python -m novaic_cortex.main_cortex
# 或
uvicorn novaic_cortex.main_cortex:app --host 0.0.0.0 --port 19996
```

监听地址与端口：

| 环境变量 | 默认 |
|----------|------|
| **`CORTEX_HOST`** | `0.0.0.0` |
| **`CORTEX_PORT`** | `19996` |

> **P3-5 / INV-7 — 单进程约束**  
> Cortex **必须**以 **single worker**（**`uvicorn --workers 1`** 或 **`python -m novaic_cortex.main_cortex`**）运行。栈操作、`_index.jsonl` / `context.jsonl` RMW 全部依赖 **in-process `asyncio.Lock`**（参见 **`_SCOPE_LOCKS`** / **`_get_scope_lock`**）。多进程会让每个进程各持一份独立的锁表，P1-1 锁掉的并发竞态会立刻回归。  
> 启动时会读取 **`UVICORN_WORKERS`** 环境变量，若 `>1` 会 **`RuntimeError`** 拒启（见 **`main_cortex._enforce_single_worker`**）。水平扩容路径见 **P3-6（分布式锁抽象）**。

## 2. `startup` 钩子做什么

1. 读 **阿里云 OSS** 凭证：**`ALIBABA_CLOUD_ACCESS_KEY_ID`**、**`ALIBABA_CLOUD_ACCESS_KEY_SECRET`**（二者缺一则 **`RuntimeError`**，服务不会正常起来）。
2. 读 endpoint / region / bucket：**`NOVAIC_OSS_ENDPOINT`**、**`NOVAIC_OSS_REGION`**、**`NOVAIC_OSS_BUCKET`**（默认值见 `main_cortex.py`）。
3. **`boto3_client_aliyun_oss(...)`** 建客户端 → **`WorkspaceRegistry(client, bucket)`** → **`set_registry(registry)`**。
4. **`BusinessProxy()`** → **`set_proxy(...)`**。

## 3. 与专题文档的衔接

- 对象键前缀：**[storage-and-keys.md](storage-and-keys.md)**  
- Business 代理与 internal key：**[proxy-cli-auth.md](proxy-cli-auth.md)**  
- HTTP 路由：**[http-api.md](http-api.md)**  
