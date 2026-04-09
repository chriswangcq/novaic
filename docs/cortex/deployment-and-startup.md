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

## 2. `startup` 钩子做什么

1. 读 **阿里云 OSS** 凭证：**`ALIBABA_CLOUD_ACCESS_KEY_ID`**、**`ALIBABA_CLOUD_ACCESS_KEY_SECRET`**（二者缺一则 **`RuntimeError`**，服务不会正常起来）。
2. 读 endpoint / region / bucket：**`NOVAIC_OSS_ENDPOINT`**、**`NOVAIC_OSS_REGION`**、**`NOVAIC_OSS_BUCKET`**（默认值见 `main_cortex.py`）。
3. **`boto3_client_aliyun_oss(...)`** 建客户端 → **`WorkspaceRegistry(client, bucket)`** → **`set_registry(registry)`**。
4. **`GatewayProxy()`** → **`set_proxy(...)`**。

## 3. 与专题文档的衔接

- 对象键前缀：**[storage-and-keys.md](storage-and-keys.md)**  
- Gateway 代理与 internal key：**[proxy-cli-auth.md](proxy-cli-auth.md)**  
- HTTP 路由：**[http-api.md](http-api.md)**  
